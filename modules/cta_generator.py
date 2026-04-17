"""
Premium fallback generator slajdu CTA — uzywany gdy Nano Banana zawiedzie.
Tworzy estetyczny slajd CTA przez Pillow z gradientem i dekoracjami.
"""
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import SLIDE_WIDTH, SLIDE_HEIGHT, FONT_PATH, FALLBACK_FONT


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        if FONT_PATH.exists():
            return ImageFont.truetype(str(FONT_PATH), size)
    except Exception:
        pass
    try:
        return ImageFont.truetype(FALLBACK_FONT, size)
    except Exception:
        return ImageFont.load_default()


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _darken(rgb: tuple, amount: float = 0.5) -> tuple:
    return tuple(max(0, int(c * amount)) for c in rgb)


def _lighten(rgb: tuple, amount: float = 1.3) -> tuple:
    return tuple(min(255, int(c * amount)) for c in rgb)


def generate_cta(
    cta_text: str,
    dominant_colors: list[str] | None = None,
    output_path: Path = None,
) -> Path:
    """
    Premium CTA slajd z gradientem + glowing accent + large bold text.
    """
    if dominant_colors and len(dominant_colors) >= 2:
        c1 = _hex_to_rgb(dominant_colors[0])
        c2 = _hex_to_rgb(dominant_colors[1])
    else:
        c1 = (15, 10, 40)
        c2 = (90, 20, 80)

    c1_dark = _darken(c1, 0.4)
    c2_light = _lighten(c2, 1.2)

    img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT))
    draw = ImageDraw.Draw(img)

    # Diagonal gradient
    for y in range(SLIDE_HEIGHT):
        t = y / SLIDE_HEIGHT
        r = int(c1_dark[0] + (c2_light[0] - c1_dark[0]) * t)
        g = int(c1_dark[1] + (c2_light[1] - c1_dark[1]) * t)
        b = int(c1_dark[2] + (c2_light[2] - c1_dark[2]) * t)
        draw.line([(0, y), (SLIDE_WIDTH, y)], fill=(r, g, b))

    # Glow orb behind text
    glow_layer = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT), (0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)
    cx, cy = SLIDE_WIDTH // 2, SLIDE_HEIGHT // 2 - 50
    glow_color = _lighten(c2, 1.4)
    for r in range(450, 0, -30):
        alpha = int(60 * (1 - r / 450))
        color = tuple(min(255, c + alpha) for c in glow_color)
        glow_draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=40))
    img = Image.blend(img, glow_layer, 0.35)
    draw = ImageDraw.Draw(img)

    # Decorative rings
    accent = _lighten(c2, 1.5)
    for r, w in [(320, 2), (280, 1)]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=accent, width=w)

    # CTA text — BIG and bold
    font_size = 72 if len(cta_text) < 22 else (60 if len(cta_text) < 30 else 48)
    font = _load_font(font_size)
    lines = wrap(cta_text, width=18 if font_size >= 60 else 22)
    line_spacing = int(font_size * 1.3)
    total_h = len(lines) * line_spacing
    start_y = (SLIDE_HEIGHT - total_h) // 2 - 30

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (SLIDE_WIDTH - tw) // 2
        y = start_y + i * line_spacing
        # Shadow
        draw.text((x + 3, y + 4), line, font=font, fill=(0, 0, 0))
        # Main text
        draw.text((x, y), line, font=font, fill=(255, 255, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0))

    # Arrow down (pointing to action)
    arrow_font = _load_font(110)
    arrow_y = SLIDE_HEIGHT - 220
    bbox = draw.textbbox((0, 0), "\u2193", font=arrow_font)
    aw = bbox[2] - bbox[0]
    draw.text((SLIDE_WIDTH // 2 - aw // 2, arrow_y), "\u2193",
              font=arrow_font, fill=accent,
              stroke_width=2, stroke_fill=(0, 0, 0))

    # Little decoration bottom
    small_font = _load_font(28)
    bottom_text = "SWIPE \u2192 TAP"
    bbox = draw.textbbox((0, 0), bottom_text, font=small_font)
    tw = bbox[2] - bbox[0]
    draw.text(
        ((SLIDE_WIDTH - tw) // 2, SLIDE_HEIGHT - 80),
        bottom_text,
        font=small_font,
        fill=(200, 200, 220),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path
