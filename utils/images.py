import io
import os
from PIL import Image, ImageDraw, ImageFont

WIDTH = 900
HEIGHT = 260

BG_COLOR = (180, 0, 0)
STRIPE_COLOR = (140, 0, 0)
TEXT_COLOR = (255, 255, 255)


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def make_action_banner(text: str) -> io.BytesIO:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Diagonal stripe texture
    stripe_gap = 50
    for x in range(-HEIGHT, WIDTH + HEIGHT, stripe_gap):
        draw.line([(x, 0), (x + HEIGHT, HEIGHT)], fill=STRIPE_COLOR, width=22)

    # Center bar
    bar_padding = 24
    draw.rectangle(
        [(0, bar_padding), (WIDTH, HEIGHT - bar_padding)],
        fill=(120, 0, 0),
    )

    font_size = 185
    font = _find_font(font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2 - bbox[0]
    y = (HEIGHT - text_h) // 2 - bbox[1]

    # Drop shadow
    draw.text((x + 4, y + 4), text, font=font, fill=(80, 0, 0))
    # Main text
    draw.text((x, y), text, font=font, fill=TEXT_COLOR)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
