"""
Generowanie nowych slajdów karuzeli.

Strategia: Gemini 2.5 Flash Image (Nano Banana) — image-to-image editing.
Bierze oryginalny slajd i modyfikuje GO (zachowuje tekst, layout, styl),
zmieniając tylko tło/perspektywę.

Fallback: Pillow (tylko gdy Nano Banana nie zadziala).
"""
import time
from pathlib import Path

from PIL import Image

from config import (
    GEMINI_API_KEY,
    SLIDE_WIDTH,
    SLIDE_HEIGHT,
    API_DELAY_SECONDS,
)
from modules.ocr_reader import SlideText


NANO_BANANA_MODEL = "gemini-2.5-flash-image"


def _build_prompt(exact_text: str) -> str:
    """Buduje prompt Nano Banana — subtelne, naturalne wariacje fotografii."""
    text_instruction = ""
    if exact_text.strip():
        text_instruction = (
            f"\n\nTEXT THAT MUST STAY EXACTLY THE SAME on the image "
            f"(copy letter-by-letter, every word, every emoji — do NOT translate or modify):\n"
            f"```\n{exact_text}\n```\n"
            f"Re-render text in the same font/position/size/color as the original."
        )

    return (
        "This is a real photograph. Create a slight variation of it — like another take "
        "from the same photoshoot. The result must look like a REAL photo, NOT AI-generated, "
        "NOT illustration, NOT CGI. Keep the photographic realism and natural look."
        + text_instruction +
        "\n\nMAKE SMALL, NATURAL CHANGES (pick 2-3, keep the rest identical):\n"
        "- Change camera angle SLIGHTLY (10-25 degrees different perspective, or slight zoom change)\n"
        "- Change color of ONE element (e.g., clothing color, prop color, wall color)\n"
        "- Slightly different lighting (e.g., warmer/cooler tone, softer/sharper shadows)\n"
        "- Minor rearrangement of background items (not whole scene change)\n"
        "- Slightly different time of day (e.g., morning vs afternoon light)\n\n"
        "KEEP THESE THE SAME:\n"
        "- Same overall setting/location (if laptop on desk → still laptop on desk)\n"
        "- Same main subjects and props (same items in frame)\n"
        "- Same general composition and framing\n"
        "- Same photographic style and realism\n"
        "- Same mood and aesthetic\n\n"
        "The goal: the new photo should look like it came from the SAME creator's SAME session "
        "— just a different shot. Natural, realistic, subtle variation. "
        "TikTok-worthy realistic photo, no AI artifacts."
    )


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _recreate_via_nano_banana(source_image: Path, output_path: Path, exact_text: str = "") -> Path | None:
    """Edytuje obraz przez Gemini 2.5 Flash Image (Nano Banana).

    exact_text: dokladny tekst z OCR — przekazany do promptu zeby AI zachowal pisownie.
    """
    if not GEMINI_API_KEY:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)

        img_bytes = Path(source_image).read_bytes()
        suffix = Path(source_image).suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(suffix, "image/jpeg")

        prompt = _build_prompt(exact_text)

        response = client.models.generate_content(
            model=NANO_BANANA_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(data=img_bytes, mime_type=mime_type),
            ],
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.data:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(part.inline_data.data)
                if output_path.stat().st_size > 1000:
                    return output_path
    except Exception as e:
        print(f"[nano_banana] FAILED: {e}")
    return None


def _fallback_copy_original(source_image: Path, output_path: Path) -> Path:
    """Ostateczny fallback: kopiuje oryginal (gdy Nano Banana nie zadziala)."""
    import shutil

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Upewnij sie ze format to PNG
    if Path(source_image).suffix.lower() == ".png":
        shutil.copy2(str(source_image), str(output_path))
    else:
        img = Image.open(str(source_image)).convert("RGB")
        img.save(str(output_path), "PNG")
    return output_path


def recreate_slide(
    slide_text: SlideText,
    index: int,
    output_path: Path,
    source_image: Path | None = None,
) -> Path:
    """
    Rekreuje slajd przez edycję oryginalnego obrazu.

    source_image: ścieżka do ORYGINALNEGO slajdu (wymagane dla Nano Banana).
                  Jeśli brak — fallback do kopii oryginału.
    """
    if source_image and Path(source_image).exists():
        result = _recreate_via_nano_banana(
            Path(source_image),
            output_path,
            exact_text=slide_text.main_text,
        )
        if result:
            return result
        print(f"[image_gen] Nano Banana nie zadzialalo dla slajdu {index}, kopiuje oryginal")
        return _fallback_copy_original(source_image, output_path)

    # Brak oryginału — tylko kopiuj (awaryjnie)
    raise RuntimeError(
        f"Brak oryginalnego obrazu dla slajdu {index}. "
        "Nano Banana wymaga obrazu wejsciowego."
    )


def recreate_all_slides(
    slide_texts: list[SlideText],
    output_dir: Path,
    source_images: list[Path] | None = None,
    progress_callback=None,
) -> list[Path]:
    """
    Rekreuje wszystkie slajdy przez Nano Banana image-to-image.

    source_images: lista sciezek do oryginalnych slajdow (w tej samej kolejnosci
                   co slide_texts). Wymagane — Nano Banana edytuje obraz wejsciowy.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_images or len(source_images) != len(slide_texts):
        raise ValueError(
            "source_images jest wymagane i musi miec te sama dlugosc co slide_texts. "
            "Nano Banana wymaga obrazow wejsciowych do edycji."
        )

    results = []
    total = len(slide_texts)

    for i, (st, src) in enumerate(zip(slide_texts, source_images), start=1):
        out_path = output_dir / f"slide_{i:02d}.png"
        try:
            path = recreate_slide(st, i, out_path, source_image=src)
            results.append(path)
        except Exception as e:
            print(f"[image_gen] ERROR slajd {i}: {e}")
            results.append(None)

        if progress_callback:
            progress_callback(i, total)

        if i < total:
            time.sleep(API_DELAY_SECONDS)

    return results
