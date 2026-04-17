"""
Generowanie nowych slajdów karuzeli.
Strategia hybrydowa:
  1. Gemini Imagen 4 Fast → generuje tło (BEZ tekstu)
  2. Pillow → nakłada tekst na wygenerowane tło

Fallback: Pollinations.ai (darmowe) → lokalne PIL (gradient).
"""
import hashlib
import random
import time
import urllib.parse
from pathlib import Path
from textwrap import wrap

import requests
from PIL import Image, ImageDraw, ImageFont

from config import (
    GEMINI_API_KEY,
    IMAGEN_MODEL,
    SLIDE_WIDTH,
    SLIDE_HEIGHT,
    FONT_PATH,
    FALLBACK_FONT,
    API_DELAY_SECONDS,
)
from modules.ocr_reader import SlideText


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Ładuje font Montserrat Bold, fallback na systemowy."""
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
    """Konwertuje kolor hex na RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _generate_background_imagen(style_prompt: str, output_path: Path) -> Path | None:
    """Generowanie tła przez Gemini Imagen 4 Fast."""
    if not GEMINI_API_KEY:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        full_prompt = (
            f"{style_prompt}. "
            "No text, no words, no letters, no writing on the image. "
            "Clean background illustration, visually appealing, high quality."
        )[:1500]
        response = client.models.generate_images(
            model=IMAGEN_MODEL,
            prompt=full_prompt,
            config={"number_of_images": 1, "aspect_ratio": "3:4"},
        )
        if response.generated_images:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.generated_images[0].image.image_bytes)
            if output_path.stat().st_size > 1000:
                return output_path
    except Exception as e:
        print(f"[imagen] FAILED: {e}")
    return None


def _generate_background_pollinations(style_prompt: str, output_path: Path) -> Path | None:
    """Fallback: generowanie tła przez Pollinations.ai (darmowe)."""
    full_prompt = (
        f"{style_prompt}. No text, no words, clean background, high quality illustration"
    )
    encoded = urllib.parse.quote(full_prompt[:500])
    seed = int(hashlib.md5(style_prompt.encode()).hexdigest()[:8], 16)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={SLIDE_WIDTH}&height={SLIDE_HEIGHT}&nologo=true&model=flux&seed={seed}"
    )
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=180)
            if r.status_code == 200 and len(r.content) > 5000:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(r.content)
                return output_path
        except Exception:
            if attempt < 2:
                time.sleep(3)
    return None


def _generate_background_local(dominant_colors: list[str], output_path: Path) -> Path:
    """Ostateczny fallback: gradient z kolorów dominujących."""
    img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT))
    draw = ImageDraw.Draw(img)

    colors = [_hex_to_rgb(c) for c in dominant_colors[:2]] if dominant_colors else [(26, 26, 46), (15, 52, 96)]
    if len(colors) < 2:
        colors.append((15, 52, 96))
    c1, c2 = colors[0], colors[1]

    for y in range(SLIDE_HEIGHT):
        r = int(c1[0] + (c2[0] - c1[0]) * y / SLIDE_HEIGHT)
        g = int(c1[1] + (c2[1] - c1[1]) * y / SLIDE_HEIGHT)
        b = int(c1[2] + (c2[2] - c1[2]) * y / SLIDE_HEIGHT)
        draw.line([(0, y), (SLIDE_WIDTH, y)], fill=(r, g, b))

    # Dodaj subtelne kształty dekoracyjne
    rng = random.Random(42)
    for _ in range(5):
        x = rng.randint(0, SLIDE_WIDTH)
        y = rng.randint(0, SLIDE_HEIGHT)
        r = rng.randint(50, 200)
        alpha_color = tuple(min(255, c + 30) for c in c2)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=None, outline=alpha_color, width=2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


def _overlay_text(
    background_path: Path,
    text: str,
    text_position: str,
    text_color: str,
    font_style: str,
    output_path: Path,
) -> Path:
    """Nakłada tekst na tło za pomocą Pillow."""
    img = Image.open(str(background_path)).convert("RGB")
    img = img.resize((SLIDE_WIDTH, SLIDE_HEIGHT), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    if not text.strip():
        img.save(str(output_path), "PNG")
        return output_path

    # Dobierz rozmiar fontu na podstawie długości tekstu
    text_len = len(text)
    if text_len < 50:
        font_size = 64
    elif text_len < 100:
        font_size = 52
    elif text_len < 200:
        font_size = 42
    else:
        font_size = 34

    font = _load_font(font_size)

    # Zawijanie tekstu
    max_chars = max(15, SLIDE_WIDTH // (font_size // 2 + 2))
    lines = []
    for paragraph in text.split("\n"):
        if paragraph.strip():
            lines.extend(wrap(paragraph, width=max_chars))
        else:
            lines.append("")

    # Oblicz wymiary bloku tekstu
    line_spacing = int(font_size * 1.4)
    total_text_height = len(lines) * line_spacing

    # Pozycja Y
    padding = 80
    if text_position == "gora":
        start_y = padding
    elif text_position == "dol":
        start_y = SLIDE_HEIGHT - total_text_height - padding
    else:  # srodek
        start_y = (SLIDE_HEIGHT - total_text_height) // 2

    color_rgb = _hex_to_rgb(text_color)
    # Kontrast: ciemny stroke jeśli tekst jasny, jasny jeśli ciemny
    brightness = sum(color_rgb) / 3
    stroke_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)

    for i, line in enumerate(lines):
        y = start_y + i * line_spacing
        # Centrowanie linii
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (SLIDE_WIDTH - text_width) // 2

        # Rysuj tekst ze stroke (obrys dla czytelności)
        draw.text(
            (x, y),
            line,
            font=font,
            fill=color_rgb,
            stroke_width=3,
            stroke_fill=stroke_color,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path


def recreate_slide(slide_text: SlideText, index: int, output_path: Path) -> Path:
    """
    Rekreuje slajd: generuje nowe tło + nakłada oryginalny tekst.

    Kolejność prób:
    1. Gemini Imagen 4 Fast
    2. Pollinations.ai
    3. Lokalne PIL (gradient)
    """
    bg_path = output_path.parent / f"_bg_{index:02d}.png"

    # Buduj prompt do generowania tła
    style_prompt = (
        f"{slide_text.background_description}. "
        f"Style: {slide_text.style_description}. "
        f"Mood: {slide_text.mood}. "
        "Different perspective, slightly different composition, fresh look."
    )

    # Próbuj generować tło
    result = _generate_background_imagen(style_prompt, bg_path)
    if not result:
        result = _generate_background_pollinations(style_prompt, bg_path)
    if not result:
        result = _generate_background_local(slide_text.dominant_colors, bg_path)

    # Nakładaj tekst
    final = _overlay_text(
        background_path=result,
        text=slide_text.main_text,
        text_position=slide_text.text_position,
        text_color=slide_text.text_color,
        font_style=slide_text.font_style,
        output_path=output_path,
    )

    # Usuń tymczasowy plik tła
    if bg_path.exists() and bg_path != output_path:
        bg_path.unlink(missing_ok=True)

    return final


def recreate_all_slides(
    slide_texts: list[SlideText],
    output_dir: Path,
    progress_callback=None,
) -> list[Path]:
    """
    Rekreuje wszystkie slajdy sekwencyjnie.
    progress_callback(current, total) — opcjonalny callback.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    total = len(slide_texts)

    for i, st in enumerate(slide_texts, start=1):
        out_path = output_dir / f"slide_{i:02d}.png"
        try:
            path = recreate_slide(st, i, out_path)
            results.append(path)
        except Exception as e:
            print(f"[image_gen] ERROR slide {i}: {e}")
            results.append(None)

        if progress_callback:
            progress_callback(i, total)

        if i < total:
            time.sleep(API_DELAY_SECONDS)

    return results
