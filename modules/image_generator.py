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


NANO_BANANA_PROMPT = (
    "Keep this image as it is — same text, same layout, same composition, same visual style. "
    "ONLY change the background to something different but in a similar aesthetic, "
    "OR slightly change the perspective / camera angle. "
    "The new image must look very similar to the original but NOT identical — "
    "just a fresh variation. "
    "Preserve all text EXACTLY, keep all graphic elements, keep the overall mood."
)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _recreate_via_nano_banana(source_image: Path, output_path: Path) -> Path | None:
    """Edytuje obraz przez Gemini 2.5 Flash Image (Nano Banana)."""
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

        response = client.models.generate_content(
            model=NANO_BANANA_MODEL,
            contents=[
                NANO_BANANA_PROMPT,
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
        result = _recreate_via_nano_banana(Path(source_image), output_path)
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
