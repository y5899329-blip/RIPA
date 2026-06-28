import io
import os
from PIL import Image, ImageDraw, ImageFont

WIDTH = 1000
HEIGHT = 300

BG_COLOR = (180, 0, 0)
STRIPE_COLOR = (140, 0, 0)
TEXT_COLOR = (255, 255, 255)

_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(_HERE, "..", "assets", "bold.ttf")

# How much breathing room to leave around the text inside the dark bar
H_PADDING = 110   # left + right margin so text doesn't span edge to edge
V_PADDING = 55    # top + bottom margin inside the center bar


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int) -> ImageFont.FreeTypeFont:
    """Binary-search the largest font size that fits inside max_w × max_h."""
    lo, hi = 20, 800
    best = ImageFont.truetype(FONT_PATH, lo)
    while lo <= hi:
        mid = (lo + hi) // 2
        font = ImageFont.truetype(FONT_PATH, mid)
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if w <= max_w and h <= max_h:
            best = font
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def make_action_banner(text: str) -> io.BytesIO:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Diagonal stripe texture
    for x in range(-HEIGHT, WIDTH + HEIGHT, 50):
        draw.line([(x, 0), (x + HEIGHT, HEIGHT)], fill=STRIPE_COLOR, width=24)

    # Dark centre bar
    bar_pad = 18
    draw.rectangle([(0, bar_pad), (WIDTH, HEIGHT - bar_pad)], fill=(115, 0, 0))

    # Fit font inside the padded area so there's clear space all around
    usable_w = WIDTH - H_PADDING * 2
    usable_h = HEIGHT - bar_pad * 2 - V_PADDING * 2
    font = _fit_font(draw, text, usable_w, usable_h)

    # Perfectly centre the text in the full banner
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (WIDTH - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (HEIGHT - (bbox[3] - bbox[1])) // 2 - bbox[1]

    # Drop shadow
    draw.text((x + 4, y + 4), text, font=font, fill=(60, 0, 0))
    # Main text
    draw.text((x, y), text, font=font, fill=TEXT_COLOR)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
