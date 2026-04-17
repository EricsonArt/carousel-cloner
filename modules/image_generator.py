"""
Generowanie nowych slajdów karuzeli przez Gemini 2.5 Flash Image (Nano Banana).
Image-to-image editing: zachowuje tekst i główne elementy, zmienia tło/otoczenie.
"""
import time
from pathlib import Path

from PIL import Image

from config import GEMINI_API_KEY, API_DELAY_SECONDS
from modules.ocr_reader import SlideText


NANO_BANANA_MODEL = "gemini-2.5-flash-image"


# Domyślny prompt — balans: te same produkty, inne tło
DEFAULT_PROMPT = (
    "This is a real photograph. Create a realistic variation where the MAIN SUBJECTS "
    "(products, devices, people, items on screen) stay visually identical, but the "
    "BACKGROUND and ENVIRONMENT change noticeably.\n\n"
    "MUST STAY EXACTLY THE SAME:\n"
    "- All products, items, and devices shown in focus (do NOT swap products)\n"
    "- All content displayed on screens (same website, same product grid, same apps)\n"
    "- Main subject (same person's hands/outfit central elements)\n"
    "- Same general composition and framing\n"
    "- Photographic realism — NOT AI-generated look, NOT CGI, NOT illustration\n\n"
    "CHANGE NOTICEABLY (but keep it realistic):\n"
    "- Background/surroundings: different wall, different room, or different outdoor setting\n"
    "- Lighting: different time of day, warmer or cooler tone, different shadow direction\n"
    "- Atmosphere: cozy/minimal/professional/home/studio — pick one different from original\n"
    "- Surface/table (different wood tone, different color, different material)\n"
    "- Ambient props NOT in focus (different plants, different cups, different decor)\n\n"
    "GOAL: the subject/product is CLEARLY the same, but anyone looking at both photos "
    "would instantly see they're different shots in different settings. "
    "Look like a professional product photographer took the same item in a different location. "
    "Natural, realistic, no AI artifacts, TikTok-worthy quality."
)


def _build_prompt(exact_text: str, custom_prompt: str | None = None) -> str:
    """Buduje prompt Nano Banana. custom_prompt nadpisuje domyślny."""
    base = (custom_prompt or DEFAULT_PROMPT).strip()

    text_instruction = ""
    if exact_text.strip():
        text_instruction = (
            f"\n\n— TEXT PRESERVATION —\n"
            f"This EXACT text must appear on the new image, unchanged "
            f"(copy letter-by-letter, every word, every emoji — do NOT translate or modify):\n"
            f"```\n{exact_text}\n```\n"
            f"Re-render text in the same font/position/size/color as the original."
        )

    return base + text_instruction


def _recreate_via_nano_banana(
    source_image: Path,
    output_path: Path,
    exact_text: str = "",
    custom_prompt: str | None = None,
) -> Path | None:
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

        prompt = _build_prompt(exact_text, custom_prompt=custom_prompt)

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
    """Fallback: kopiuje oryginal gdy Nano Banana nie zadziala."""
    import shutil

    output_path.parent.mkdir(parents=True, exist_ok=True)
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
    custom_prompt: str | None = None,
) -> Path:
    """Rekreuje slajd przez edycję oryginalnego obrazu."""
    if source_image and Path(source_image).exists():
        result = _recreate_via_nano_banana(
            Path(source_image),
            output_path,
            exact_text=slide_text.main_text,
            custom_prompt=custom_prompt,
        )
        if result:
            return result
        print(f"[image_gen] Nano Banana nie zadzialalo dla slajdu {index}, kopiuje oryginal")
        return _fallback_copy_original(source_image, output_path)

    raise RuntimeError(
        f"Brak oryginalnego obrazu dla slajdu {index}. Nano Banana wymaga obrazu wejsciowego."
    )


def recreate_all_slides(
    slide_texts: list[SlideText],
    output_dir: Path,
    source_images: list[Path] | None = None,
    progress_callback=None,
    custom_prompt: str | None = None,
) -> list[Path]:
    """
    Rekreuje wszystkie slajdy przez Nano Banana.

    custom_prompt: opcjonalny własny prompt uzytkownika. Jesli None, uzywa DEFAULT_PROMPT.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not source_images or len(source_images) != len(slide_texts):
        raise ValueError(
            "source_images jest wymagane i musi miec te sama dlugosc co slide_texts."
        )

    results = []
    total = len(slide_texts)

    for i, (st, src) in enumerate(zip(slide_texts, source_images), start=1):
        out_path = output_dir / f"slide_{i:02d}.png"
        try:
            path = recreate_slide(
                st, i, out_path,
                source_image=src,
                custom_prompt=custom_prompt,
            )
            results.append(path)
        except Exception as e:
            print(f"[image_gen] ERROR slajd {i}: {e}")
            results.append(None)

        if progress_callback:
            progress_callback(i, total)

        if i < total:
            time.sleep(API_DELAY_SECONDS)

    return results
