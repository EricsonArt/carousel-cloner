"""
Generator slajdu CTA (Call-To-Action).
Tworzy ostatni slajd karuzeli z wezwaniem do działania.
"""
from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

from config import SLIDE_WIDTH, SLIDE_HEIGHT, FONT_PATH, FALLBACK_FONT
from modules.ocr_reader import SlideText


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


def generate_cta(
    cta_text: str,
    dominant_colors: list[str] | None = None,
    output_path: Path = None,
) -> Path:
    """
    Generuje slajd CTA z gradientem i dużym tekstem.

    cta_text: tekst CTA (np. "Wejdz na flipzone.pl")
    dominant_colors: kolory z karuzeli (dla spójności wizualnej)
    output_path: ścieżka do zapisu PNG
    """
    if dominant_colors and len(dominant_colors) >= 2:
        c1 = _hex_to_rgb(dominant_colors[0])
        c2 = _hex_to_rgb(dominant_colors[1])
    else:
        c1 = (26, 26, 46)
        c2 = (15, 52, 96)

    img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT))
    draw = ImageDraw.Draw(img)

    # Gradient tło
    for y in range(SLIDE_HEIGHT):
        r = int(c1[0] + (c2[0] - c1[0]) * y / SLIDE_HEIGHT)
        g = int(c1[1] + (c2[1] - c1[1]) * y / SLIDE_HEIGHT)
        b = int(c1[2] + (c2[2] - c1[2]) * y / SLIDE_HEIGHT)
        draw.line([(0, y), (SLIDE_WIDTH, y)], fill=(r, g, b))

    # Dekoracyjne elementy
    accent = tuple(min(255, c + 60) for c in c2)
    # Duże koło dekoracyjne
    cx, cy = SLIDE_WIDTH // 2, SLIDE_HEIGHT // 3
    draw.ellipse([cx - 250, cy - 250, cx + 250, cy + 250], fill=None, outline=accent, width=3)
    # Mniejsze koła
    draw.ellipse([cx - 180, cy - 180, cx + 180, cy + 180], fill=None, outline=accent, width=2)

    # Emoji strzałki
    arrow_font = _load_font(80)
    arrow_text = "\u2193"  # ↓
    bbox = draw.textbbox((0, 0), arrow_text, font=arrow_font)
    aw = bbox[2] - bbox[0]
    draw.text(
        ((SLIDE_WIDTH - aw) // 2, SLIDE_HEIGHT // 2 + 120),
        arrow_text,
        font=arrow_font,
        fill=(255, 255, 255),
    )

    # Tekst CTA
    font_large = _load_font(56)
    lines = wrap(cta_text, width=20)
    line_spacing = 70
    total_h = len(lines) * line_spacing
    start_y = (SLIDE_HEIGHT - total_h) // 2 - 40

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_large)
        tw = bbox[2] - bbox[0]
        x = (SLIDE_WIDTH - tw) // 2
        y = start_y + i * line_spacing
        draw.text(
            (x, y),
            line,
            font=font_large,
            fill=(255, 255, 255),
            stroke_width=3,
            stroke_fill=(0, 0, 0),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path
