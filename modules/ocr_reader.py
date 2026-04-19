"""
OCR tekstu z slajdów karuzeli za pomocą Gemini Vision API.
Wyciąga tekst, opis stylu, pozycję tekstu i kolory.
"""
import base64
import json
from dataclasses import dataclass, field
from pathlib import Path

from google import genai

from config import get_api_key, GEMINI_VISION_MODEL


def _client():
    key = get_api_key()
    return genai.Client(api_key=key) if key else None

ANALYSIS_PROMPT = """Przeanalizuj ten obraz slajdu z karuzeli na Instagramie/TikToku.

Zwroc TYLKO czysty JSON (bez markdown, bez ```json```) z polami:
{
  "text": "dokladny tekst widoczny na obrazku, zachowaj formatowanie i podzialy linii",
  "style_description": "krotki opis stylu wizualnego (np. minimalistyczny, kolorowy, ciemne tlo, jasne kolory)",
  "text_position": "gora | srodek | dol",
  "text_color": "kolor tekstu jako hex np. #FFFFFF",
  "background_description": "opis tla (np. gradient niebieski, zdjecie natury, jednolity kolor)",
  "dominant_colors": ["#hex1", "#hex2", "#hex3"],
  "font_style": "bold | regular | handwritten | serif",
  "mood": "nastroj slajdu (np. motywacyjny, informacyjny, zabawny)"
}

Jesli na obrazku nie ma tekstu, pole "text" zostaw puste.
Zwroc TYLKO JSON, nic wiecej."""


@dataclass
class SlideText:
    main_text: str = ""
    style_description: str = ""
    text_position: str = "srodek"
    text_color: str = "#FFFFFF"
    background_description: str = ""
    dominant_colors: list[str] = field(default_factory=lambda: ["#1a1a2e", "#16213e", "#0f3460"])
    font_style: str = "bold"
    mood: str = ""


def extract_text_from_slide(image_path: Path) -> SlideText:
    """
    Analizuje slajd za pomocą Gemini Vision.
    Zwraca SlideText z tekstem, opisem stylu i kolorami.
    """
    client = _client()
    if not client:
        raise RuntimeError("Brak GEMINI_API_KEY — wklej klucz w panelu aplikacji.")

    image_bytes = Path(image_path).read_bytes()
    b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Wykryj typ MIME
    suffix = Path(image_path).suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime_type = mime_map.get(suffix, "image/png")

    response = client.models.generate_content(
        model=GEMINI_VISION_MODEL,
        contents=[
            {
                "parts": [
                    {"text": ANALYSIS_PROMPT},
                    {"inline_data": {"mime_type": mime_type, "data": b64}},
                ]
            }
        ],
    )

    raw = response.text.strip()
    # Usuń markdown code fences jeśli są
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return SlideText(main_text="[OCR ERROR] Nie udalo sie odczytac")

    return SlideText(
        main_text=data.get("text", ""),
        style_description=data.get("style_description", ""),
        text_position=data.get("text_position", "srodek"),
        text_color=data.get("text_color", "#FFFFFF"),
        background_description=data.get("background_description", ""),
        dominant_colors=data.get("dominant_colors", ["#1a1a2e", "#16213e", "#0f3460"]),
        font_style=data.get("font_style", "bold"),
        mood=data.get("mood", ""),
    )


def extract_all_slides(slide_paths: list[Path], progress_callback=None) -> list[SlideText]:
    """
    Analizuje wszystkie slajdy sekwencyjnie.
    progress_callback(current, total) — opcjonalny callback dla progress bar.
    """
    import time
    from config import API_DELAY_SECONDS

    results = []
    total = len(slide_paths)

    for i, path in enumerate(slide_paths, start=1):
        try:
            result = extract_text_from_slide(path)
        except Exception as e:
            result = SlideText(main_text=f"[BLAD OCR] {e}")
        results.append(result)

        if progress_callback:
            progress_callback(i, total)

        if i < total:
            time.sleep(API_DELAY_SECONDS)

    return results
