# -*- coding: utf-8 -*-
# File: coco.py

import numpy as np
import os
from termcolor import colored
from tabulate import tabulate
import tqdm

from tensorpack.utils import logger
from tensorpack.utils.rect import BoxBase
from tensorpack.utils.timer import timed_operation
from tensorpack.utils.argtools import log_once


class FloatBox(BoxBase):
    def __init__(self, x1, y1, x2, y2):
        for k in [x1, y1, x2, y2]:
            assert isinstance(k, float), "type={},value={}".format(type(k), k)
        super(FloatBox, self).__init__(x1, y1, x2, y2)

    @property
    def w(self):
        return self.x2 - self.x1

    @property
    def h(self):
        return self.y2 - self.y1

    @staticmethod
    def from_intbox(intbox):
        return FloatBox(intbox.x1, intbox.y1,
                        intbox.x2 + 1, intbox.y2 + 1)

    def clip_by_shape(self, shape):
        self.x1 = np.clip(self.x1, 0, shape[1])
        self.x2 = np.clip(self.x2, 0, shape[1])
        self.y1 = np.clip(self.y1, 0, shape[0])
        self.y2 = np.clip(self.y2, 0, shape[0])


__all__ = ['COCODetection', 'COCOMeta']


class _COCOMeta(object):
    # CLASS_NAMES = []
    INSTANCE_TO_BASEDIR = {
        'train2014': 'train2014',
        'val2014': 'val2014',
        'valminusminival2014': 'val2014',
        'minival2014': 'val2014',
        'test2014': 'test2014',
        'train2017': 'train2017',
        'val2017': 'val2017',
    }

    def valid(self):
        return hasattr(self, 'cat_names')

    def create(self, cat_ids, cat_names):
        """
        cat_ids: list of ids
        cat_names: list of names
        """
        assert not self.valid()
        assert len(cat_ids) == 80 and len(cat_names) == 80
        self.cat_names = cat_names
        self.class_names = ['BG'] + self.cat_names

        # background has class id of 0
        self.category_id_to_class_id = {
            v: i + 1 for i, v in enumerate(cat_ids)}
        self.class_id_to_category_id = {
            v: k for k, v in self.category_id_to_class_id.items()}
        CLASS_NAMES = self.class_names


COCOMeta = _COCOMeta()


class COCODetection(object):
    def __init__(self, basedir, name):
        assert name in COCOMeta.INSTANCE_TO_BASEDIR.keys(), name

        self.name = name
        self._imgdir = os.path.realpath(os.path.join(
            basedir, COCOMeta.INSTANCE_TO_BASEDIR[name]))
        assert os.path.isdir(self._imgdir), self._imgdir
        annotation_file = os.path.join(
            basedir, 'annotations/instances_{}.json'.format(name))
        assert os.path.isfile(annotation_file), annotation_file

        from pycocotools.coco import COCO
        self.coco = COCO(annotation_file)

        # initialize the meta
        cat_ids = self.coco.getCatIds()
        cat_names = [c['name'] for c in self.coco.loadCats(cat_ids)]
        if not COCOMeta.valid():
            COCOMeta.create(cat_ids, cat_names)
        else:
            assert COCOMeta.cat_names == cat_names

        logger.info("Instances loaded from {}.".format(annotation_file))

    def load(self, add_gt=True, add_mask=False):
        """
        Args:
            add_gt: whether to add ground truth bounding box annotations to the dicts
            add_mask: whether to also add ground truth mask

        Returns:
            a list of dict, each has keys including:
                'height', 'width', 'id', 'file_name',
                and (if add_gt is True) 'boxes', 'class', 'is_crowd', and optionally
                'segmentation'.
        """
        if add_mask:
            assert add_gt
        with timed_operation('Load Groundtruth Boxes for {}'.format(self.name)):
            img_ids = self.coco.getImgIds()
            img_ids.sort()
            # list of dict, each has keys: height,width,id,file_name
            imgs = self.coco.loadImgs(img_ids)

            for img in tqdm.tqdm(imgs):
                self._use_absolute_file_name(img)
                if add_gt:
                    self._add_detection_gt(img, add_mask)
            return imgs

    def _use_absolute_file_name(self, img):
        """
        Change relative filename to abosolute file name.
        """
        img['file_name'] = os.path.join(
            self._imgdir, img['file_name'])
        assert os.path.isfile(img['file_name']), img['file_name']

    def _add_detection_gt(self, img, add_mask):
        """
        Add 'boxes', 'class', 'is_crowd' of this image to the dict, used by detection.
        If add_mask is True, also add 'segmentation' in coco poly format.
        """
        # ann_ids = self.coco.getAnnIds(imgIds=img['id'])
        # objs = self.coco.loadAnns(ann_ids)
        objs = self.coco.imgToAnns[img['id']]  # equivalent but faster than the above two lines

        # clean-up boxes
        valid_objs = []
        width = img['width']
        height = img['height']
        for obj in objs:
            if obj.get('ignore', 0) == 1:
                continue
            x1, y1, w, h = obj['bbox']
            # bbox is originally in float
            # x1/y1 means upper-left corner and w/h means true w/h. This can be verified by segmentation pixels.
            # But we do assume that (0.0, 0.0) is upper-left corner of the first pixel
            box = FloatBox(float(x1), float(y1),
                           float(x1 + w), float(y1 + h))
            box.clip_by_shape([height, width])
            # Require non-zero seg area and more than 1x1 box size
            if obj['area'] > 1 and box.is_box() and box.area() >= 4:
                obj['bbox'] = [box.x1, box.y1, box.x2, box.y2]
                valid_objs.append(obj)

                if add_mask:
                    segs = obj['segmentation']
                    if not isinstance(segs, list):
                        assert obj['iscrowd'] == 1
                        obj['segmentation'] = None
                    else:
                        valid_segs = [np.asarray(p).reshape(-1, 2).astype('float32') for p in segs if len(p) >= 6]
                        if len(valid_segs) < len(segs):
                            log_once("Image {} has invalid polygons!".format(img['file_name']), 'warn')

                        obj['segmentation'] = valid_segs

        # all geometrically-valid boxes are returned
        boxes = np.asarray([obj['bbox'] for obj in valid_objs], dtype='float32')  # (n, 4)
        cls = np.asarray([
            COCOMeta.category_id_to_class_id[obj['category_id']]
            for obj in valid_objs], dtype='int32')  # (n,)
        is_crowd = np.asarray([obj['iscrowd'] for obj in valid_objs], dtype='int8')

        # add the keys
        img['boxes'] = boxes  # nx4
        img['class'] = cls  # n, always >0
        img['is_crowd'] = is_crowd  # n,
        if add_mask:
            # also required to be float32
            img['segmentation'] = [
                obj['segmentation'] for obj in valid_objs]

    def print_class_histogram(self, imgs):
        nr_class = len(COCOMeta.class_names)
        hist_bins = np.arange(nr_class + 1)

        # Histogram of ground-truth objects
        gt_hist = np.zeros((nr_class,), dtype=np.int)
        for entry in imgs:
            # filter crowd?
            gt_inds = np.where(
                (entry['class'] > 0) & (entry['is_crowd'] == 0))[0]
            gt_classes = entry['class'][gt_inds]
            gt_hist += np.histogram(gt_classes, bins=hist_bins)[0]
        data = [[COCOMeta.class_names[i], v] for i, v in enumerate(gt_hist)]
        data.append(['total', sum([x[1] for x in data])])
        table = tabulate(data, headers=['class', '#box'], tablefmt='pipe')
        logger.info("Ground-Truth Boxes:\n" + colored(table, 'cyan'))

    @staticmethod
    def load_many(basedir, names, add_gt=True, add_mask=False):
        """
        Load and merges several instance files together.

        Returns the same format as :meth:`COCODetection.load`.
        """
        if not isinstance(names, (list, tuple)):
            names = [names]
        ret = []
        for n in names:
            coco = COCODetection(basedir, n)
            ret.extend(coco.load(add_gt, add_mask=add_mask))
        return ret
