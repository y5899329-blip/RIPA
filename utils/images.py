import io
import os
from PIL import Image, ImageDraw, ImageFont

# Banner dimensions
WIDTH = 800
HEIGHT = 180

# Colors
BG_COLOR = (180, 0, 0)        # deep red
STRIPE_COLOR = (140, 0, 0)    # darker red stripe
TEXT_COLOR = (255, 255, 255)  # white


def _find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try common bold font paths; fall back to Pillow's built-in."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",   # macOS
        "C:/Windows/Fonts/arialbd.ttf",                        # Windows
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    # Pillow default (small but always available)
    return ImageFont.load_default()


def make_action_banner(text: str) -> io.BytesIO:
    """
    Generate a red PNG banner image with bold white text centered on it.
    Returns a seeked BytesIO ready to pass to discord.File.
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), color=BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Diagonal stripe pattern for texture
    stripe_gap = 40
    for x in range(-HEIGHT, WIDTH + HEIGHT, stripe_gap):
        draw.line([(x, 0), (x + HEIGHT, HEIGHT)], fill=STRIPE_COLOR, width=16)

    # Dark semi-transparent center bar to make text pop
    bar_padding = 20
    draw.rectangle(
        [(0, bar_padding), (WIDTH, HEIGHT - bar_padding)],
        fill=(120, 0, 0),
    )

    # Draw text centered
    font_size = 110
    font = _find_font(font_size)

    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2 - bbox[0]
    y = (HEIGHT - text_h) // 2 - bbox[1]

    # Drop shadow
    shadow_offset = 3
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(80, 0, 0))
    # Main text
    draw.text((x, y), text, font=font, fill=TEXT_COLOR)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
