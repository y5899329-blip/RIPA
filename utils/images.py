import io
import os
from PIL import Image, ImageDraw, ImageFont

# Banner size — tall enough for massive text
WIDTH = 1000
HEIGHT = 300

BG_COLOR = (180, 0, 0)
STRIPE_COLOR = (140, 0, 0)
TEXT_COLOR = (255, 255, 255)

# Bundled font — always available regardless of OS
_HERE = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(_HERE, "..", "assets", "bold.ttf")


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int) -> ImageFont.FreeTypeFont:
    """Binary-search the largest font size where text fits inside max_w × max_h."""
    lo, hi = 50, 1000
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

    # Dark center bar
    pad = 18
    draw.rectangle([(0, pad), (WIDTH, HEIGHT - pad)], fill=(115, 0, 0))

    # Fit the font to fill almost the entire banner (4px margin each side)
    font = _fit_font(draw, text, WIDTH - 8, HEIGHT - pad * 2 - 4)

    # Center
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (WIDTH - (bbox[2] - bbox[0])) // 2 - bbox[0]
    y = (HEIGHT - (bbox[3] - bbox[1])) // 2 - bbox[1]

    # Drop shadow for depth
    draw.text((x + 6, y + 6), text, font=font, fill=(60, 0, 0))
    # Main white text
    draw.text((x, y), text, font=font, fill=TEXT_COLOR)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
