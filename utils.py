import io
from urllib.request import urlopen
from PIL import Image, ImageFont, ImageDraw
import unicodedata

def process_data(data):
    images = {}
    text = {}

    for index, row in enumerate(data):
        if row["mc_type"] == "string":
            frame = create_text_frame(row)
            text[index] = frame
            continue
        elif row["mc_type"] == "emote":
            img_id = row["value"]
            if img_id not in images:
                images[img_id] = create_emote_frame(img_id)
        elif row["mc_type"] == "image":
            url = row["value"]
            if url not in images:
                images[url] = create_image(url)

    return (images, text)


def create_text_frame(data_row, fill_color=(255, 255, 0, 255)):
    display_text = data_row["value"]
    display_text = display_text.strip()
    segments = split_by_unicode_group(display_text)
    total_width = 0
    frames = []
    for segment in segments:
        if segment['unicode_category']=="other":
            font = ImageFont.truetype('fonts/fira-bold.ttf', 26)
        elif segment['unicode_category']=="special":
            font = ImageFont.truetype('fonts/fira-bold.ttf', 26)
        else:
            font = ImageFont.truetype('fonts/seguiemj.ttf', 24)

        width, height = font.getsize(segment['text'])
        total_width += width
        frame = Image.new('RGB', size=(width, 32))
        draw = ImageDraw.Draw(frame)
        if segment['unicode_category']=="emoji":
            draw.text((0, 4), segment['text'], font=font, embedded_color=True)
        else:
            draw.text((0, 0), segment['text'], font=font, fill=fill_color)

        frames.append(frame)

    return frames


def create_image(url):
    img_data = urlopen(url).read()
    image = Image.open(io.BytesIO(img_data))

    image_dat = {
        "image": image,
        "frames": [],
        "current_frame": 0,
        "current_frame_start": 0,
    }
    for frame_num in range(0, getattr(image, "n_frames", 1)):
        image.seek(frame_num)
        duration = image.info.get('duration', 0)

        image_rgba = image.convert(mode='RGBA')
        frame = Image.new('RGB', image.size)
        frame.paste(image_rgba, mask=image_rgba)
        image_dat["frames"].append({"frame": frame, "duration": duration})
    
    return image_dat

def create_emote_frame(img_id):
    url = f"https://static-cdn.jtvnw.net/emoticons/v2/{img_id}/default/light/1.0"
    return create_image(url)

def char_type(unicode_cat):
    print(unicode_cat)
    if unicode_cat == 'So':
        return 'emoji'
    elif unicode_cat == 'Cf':
        return 'Cf'
    elif unicode_cat == 'Sk':
        return 'Sk'
    elif unicode_cat == 'Mn':
        return 'Mn'
    elif unicode_cat == 'Co':
        return 'special'
    else:
        return 'other'


def segment(text, seg_range):
    seg = {
        'text': '',
        'unicode_category': seg_range['cat']
    }
    if seg_range['range'][1] != -1:
        seg['text'] = text[seg_range['range'][0]:seg_range['range'][1]]
    else:
        seg['text'] = text[seg_range['range'][0]:]
    return seg


def split_by_unicode_group(text):
    filtered_text = []
    for char in text:
        ct = char_type(unicodedata.category(char))
        if ct != 'Mn' and ct != 'Sk' and ct != 'Cf':
            filtered_text.append(char)
    filtered_text = ''.join(filtered_text)

    char_cats = [char_type(unicodedata.category(char)) for char in filtered_text]
    char_cats = list(filter(lambda x: (x != 'Mn' and x != 'Sk' and x != 'Cf'), char_cats))
    segment_ranges = []
    last_cat = ''
    for i, cat in enumerate(char_cats):
        if cat != last_cat:
            last_cat = cat
            if i > 0:
                segment_ranges[-1]['range'][1] = i
            segment_ranges.append({'range': [i,-1], 'cat': cat})
    
    segments = [segment(filtered_text, seg_range) for seg_range in segment_ranges]
    return segments
