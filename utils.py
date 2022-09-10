from PIL import Image
import requests
from io import BytesIO
import re
import random
import numexpr as ne

import configparser
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf8')

RETURN_CODE_SUCCES = config['RETURN_CODES'].getint('RETURN_CODE_SUCCES')
RETURN_CODE_ERROR = config['RETURN_CODES'].getint('RETURN_CODE_ERROR')
RETURN_CODE_UNEXPECTED_ERROR = config['RETURN_CODES'].getint('RETURN_CODE_UNEXPECTED_ERROR')

MAX_ROLE_REQUEST_LENGTH = config['DICE'].getint('MAX_ROLE_REQUEST_LENGTH')
MAX_DICES = config['DICE'].getint('MAX_DICES')

def get_mean_color_by_url(url: str):
    response = requests.get(url)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content))
    r, g, b = 0, 0, 0
    count = 1
    for x in range(img.width):
        for y in range(img.height):
            color = img.getpixel((x, y))
            if color[0] + color[1] + color[2] > 210:
                r += color[0]
                g += color[1]
                b += color[2]
                count += 1
    r //= count
    g //= count
    b //= count
    return (r, g, b)

def process_roll(src: str):
    while '**' in src:
        src = src.replace('**', '*')
    if len(src) > MAX_ROLE_REQUEST_LENGTH:
        return RETURN_CODE_ERROR, f'Духи требуют краткости (не более {MAX_ROLE_REQUEST_LENGTH} символов)'
    src = src.replace('d', 'к').replace('д', 'к')
    shift = 0
    count = 0
    rolls = []
    maxs = []
    for roll in re.finditer('\d*к\d+', src):
        count += 1
        rolls.append([])
        start, end = roll.span()
        start, end = start + shift, end + shift
        roll = src[start:end]
        n, max_ = roll.split('к')
        n = 1 if len(n) == 0 else int(n)
        max_ = int(max_)
        maxs.append(max_)
        s = 0
        if n > MAX_DICES:
            return RETURN_CODE_ERROR, f'Больше чем {MAX_DICES} костей гневают духов'
        for i in range(n):
            x = random.randint(1, max_)
            s += x
            rolls[-1].append(x)
        src = src[:start] + str(s) + src[end:]
        shift += start - end + len(str(s))
    try:
        value = ne.evaluate(src)    
        if count == 1 and len(rolls[-1]) == 1 or count == 0:
            res = "**Духи говорят:** {}".format(value)
        elif count == 1:
            res = "**Произведены броски:** `{}`\n**Итог:** `{}`".format(', '.join(map(str, rolls[-1])), value)
        else:
            res = "**Произведены броски:**\n"
            for i in range(len(rolls)):
                res += "{} : `{}`\n".format(maxs[i], ', '.join(map(str, rolls[i])))
            res += "**Итог:** `{}`".format(value)
        return RETURN_CODE_SUCCES, res
    except Exception as err:
        return RETURN_CODE_UNEXPECTED_ERROR, err