import io
import os
from PIL import Image, ImageDraw, ImageFont

WIDTH = 900
HEIGHT = 280
BG_COLOR = (180, 0, 0)
STRIPE_COLOR = (140, 0, 0)
TEXT_COLOR = (255, 255, 255)

# Padding so the text doesn't touch the very edge
H_PADDING = 30
V_PADDING = 16


def _find_font(size: int):
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


def _fit_font(draw: ImageDraw.ImageDraw, text: str, max_w: int, max_h: int):
    """Binary-search the largest font size that fits within max_w × max_h."""
    lo, hi = 10, 600
    best_font = _find_font(lo)
    best_size = lo

    while lo <= hi:
        mid = (lo + hi) // 2
        font = _find_font(mid)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w <= max_w and h <= max_h:
            best_font = font
            best_size = mid
            lo = mid + 1
        else:
            hi = mid - 1

    return best_font


def make_action_banner(text: str) -> io.BytesIO:
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Diagonal stripe texture
    stripe_gap = 50
    for x in range(-HEIGHT, WIDTH + HEIGHT, stripe_gap):
        draw.line([(x, 0), (x + HEIGHT, HEIGHT)], fill=STRIPE_COLOR, width=22)

    # Center bar background
    draw.rectangle([(0, V_PADDING), (WIDTH, HEIGHT - V_PADDING)], fill=(120, 0, 0))

    # Find the biggest font that fills the usable area
    max_w = WIDTH - H_PADDING * 2
    max_h = HEIGHT - V_PADDING * 2
    font = _fit_font(draw, text, max_w, max_h)

    # Center the text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2 - bbox[0]
    y = (HEIGHT - text_h) // 2 - bbox[1]

    # Drop shadow
    draw.text((x + 5, y + 5), text, font=font, fill=(70, 0, 0))
    # Main text
    draw.text((x, y), text, font=font, fill=TEXT_COLOR)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
