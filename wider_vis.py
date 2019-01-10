import cv2
from PIL import ImageDraw, Image
import numpy as np
from vis_utils import draw_person_attributes, draw_bounding_box_pil
from wider_load import load_many
from collections import namedtuple


class PersonAttrs:
    def __init__(self, attribute):
        self.facemask = attribute.facemask
        self.formal = attribute.formal
        self.hat = attribute.hat
        self.jeans = attribute.jeans
        self.logo = attribute.logo
        self.longhair = attribute.longhair
        self.longpants = attribute.longpants
        self.longsleeve = attribute.longsleeve
        self.male = attribute.male
        self.shorts = attribute.shorts
        self.skirt = attribute.skirt
        self.stripe = attribute.stripe
        self.sunglass = attribute.sunglass
        self.tshirt = attribute.tshirt


DetectionResult = namedtuple(
    'DetectionResult',
    ['bbox', 'facemask', 'formal', 'hat', 'jeans', 'logo',
     'longhair', 'longpants', 'longsleeve', 'male',
     'shorts', 'skirt', 'stripe', 'sunglass', 'tshirt'])


def vis_one_image(image_bgr, boxes, attrs):
    # Draw attribute results
    image_pil = Image.fromarray(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image_pil)
    for box, attr in zip(boxes, attrs):
        draw_bounding_box_pil(box, draw, 'blue')
        draw_person_attributes(draw, attr, box)

    image_disp = cv2.cvtColor(np.array(image_pil), cv2.COLOR_RGB2BGR)

    return image_disp


imgdbs = load_many('/root/datasets/wider attribute', 'train')
for imgdb in imgdbs:
    image_name = imgdb['img']

    results = [DetectionResult(*args) for args in
               zip(imgdb['bbox'], imgdb['facemask'], imgdb['formal'], imgdb['hat'],
                   imgdb['jeans'], imgdb['logo'], imgdb['longhair'], imgdb['longpants'],
                   imgdb['longsleeve'], imgdb['male'], imgdb['shorts'], imgdb['skirt'],
                   imgdb['stripe'], imgdb['sunglass'], imgdb['tshirt'])]

    img = cv2.imread(image_name, cv2.IMREAD_COLOR)
    boxes = imgdb['bbox']
    attrs = [PersonAttrs(r) for r in results]

    img_to_show = vis_one_image(img, boxes, attrs)
    if img_to_show is not None:
        cv2.imshow('wider datasets', img_to_show)
        cv2.waitKey(0)
    else:
        break
