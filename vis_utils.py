from PIL import ImageFont

FONT = "wqy-zenhei.ttc"
DEFAULT_FONT_SIZE = 16
TITLE_FONT_SIZE = 48
LINE_THICKNESS = 4


def draw_text_pil(text, xy, draw, rgb, font_size=DEFAULT_FONT_SIZE, width=1, background=None):
    font = ImageFont.truetype(FONT, size=font_size)

    def draw_text_with_width(text, x, y, width, rgb, font):
        for x_off in range(0, width):
            for y_off in range(0, width):
                draw.text((x + x_off, y + y_off), text, fill=rgb, font=font)

    x = xy[0]
    y = xy[1]
    if isinstance(text, list):
        text_margin = 2

        for t in text:
            text_w, text_h = draw.textsize(t, font)
            if background is not None:
                draw.rectangle(((x, y), (x + text_w, y + text_h)), fill=background)
            draw_text_with_width(t, x, y, width, rgb, font)
            y = y + text_h + text_margin
    else:
        draw_text_with_width(text, x, y, width, rgb, font)


def draw_bounding_box_pil(box, draw, color):
    xmin = box[0]
    ymin = box[1]
    width = box[2]
    height = box[3]
    xmax = box[0] + width
    ymax = box[1] + height
    #xmin, xmax, ymin, ymax = box
    (left, right, top, bottom) = (xmin, xmax,
                                  ymin, ymax)
    draw.line([(left, top), (left, bottom), (right, bottom),
               (right, top), (left, top)], width=3, fill=color)


male_text = u"男"
female_text = u"女"
unspecified_text = u"性别不确定"
facemask_text = u"面罩"
formal_text = u"正装"
hat_text = u"帽子"
jeans_text = u"牛仔裤"
logo_text = u"标志"
longhair_text = u"长发"
longpants_text = u"长裤"
longsleeve_text = u"长袖"
shorts_text = u"短裤"
skirt_text = u"裙子"
stripe_text = u"条纹"
sunglass_text = u"太阳镜"
tshirt_text = u"T恤"


def label_to_text(label):
    if label == 1:
        return male_text
    elif label == 0:
        return unspecified_text
    else:
        return female_text


def draw_person_attributes(draw, person, body_box):
    # Draw (semi-)static attributes as text on body bounding boxes
    xmin, ymin, width, height = body_box
    xmax = xmin + width
    ymax = ymin + height

    text = [label_to_text(person.male)]
    # text = [male_text if person.male == 1 else female_text]
    if person.facemask == 1:
        text.append(facemask_text)
    if person.formal == 1:
        text.append(formal_text)
    if person.hat == 1:
        text.append(hat_text)
    if person.jeans == 1:
        text.append(jeans_text)
    if person.logo == 1:
        text.append(logo_text)
    if person.longhair == 1:
        text.append(longhair_text)
    if person.longpants == 1:
        text.append(longpants_text)
    if person.longsleeve == 1:
        text.append(longsleeve_text)
    if person.shorts == 1:
        text.append(shorts_text)
    if person.skirt == 1:
        text.append(skirt_text)
    if person.stripe == 1:
        text.append(stripe_text)
    if person.sunglass == 1:
        text.append(sunglass_text)
    if person.tshirt == 1:
        text.append(tshirt_text)

    draw_text_pil(text, (xmax + 3, ymin), draw, "black", width=1, background="white")
