import cv2
from PIL import ImageDraw, Image
import numpy as np

from coco_load import COCODetection
from vis_utils import draw_bounding_box_pil
from wider_load import load_many


def vis_one_image(image_bgr, boxes):
    # Draw attribute results
    image_pil = Image.fromarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)
    for box in boxes:
        draw_bounding_box_pil(box, draw, 'blue')

    image_disp = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

    return image_disp


# Assuming dataset directory is /root/datasets/wider attribute/train
#imgdbs = load_many('/root/datasets/wider attribute', 'train')
#   --train
#   --val
#   --test

roidbs = COCODetection.load_many(
    '/root/datasets/COCO/DIR/', 'val2014', add_gt=True, add_mask=False)

for imgdb in roidbs:
    image_name = imgdb['file_name']

    img = cv2.imread(image_name, cv2.IMREAD_COLOR)
    boxes = imgdb['boxes']
    x1, y1, x2, y2 = np.split(boxes, 4, axis=1)
    boxes = np.concatenate([x1, y1, x2 - x1, y2 - y1], axis=1)
    img_to_show = vis_one_image(img, boxes)
    if img_to_show is not None:
        cv2.imshow('wider datasets', img_to_show)
        cv2.waitKey(0)
    else:
        break
