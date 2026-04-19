"""
Tlumaczenie tekstu na slajdach na wybrany jezyk przez Gemini.
Zachowuje emoji, liczby, formatowanie linii.
"""
from dataclasses import replace

from google import genai

from config import get_api_key, GEMINI_VISION_MODEL
from modules.ocr_reader import SlideText


def _client():
    key = get_api_key()
    return genai.Client(api_key=key) if key else None


LANGUAGES = {
    "original": "Taki sam jak oryginal",
    "polish": "Polski",
    "english": "Angielski",
    "german": "Niemiecki",
    "spanish": "Hiszpanski",
    "french": "Francuski",
    "italian": "Wloski",
}

LANG_NAMES = {
    "polish": "Polish",
    "english": "English",
    "german": "German",
    "spanish": "Spanish",
    "french": "French",
    "italian": "Italian",
}


TRANSLATE_PROMPT = """Translate the following carousel slide text into {target_lang}.

STRICT RULES:
- Keep the EXACT same line breaks and formatting
- Keep all emojis EXACTLY as they are (do NOT remove, change, or add emojis)
- Keep numbers, brand names, usernames, hashtags, URLs UNCHANGED
- Keep the same casual social-media tone (TikTok/Instagram style)
- If text is already in {target_lang}, return it UNCHANGED
- Return ONLY the translated text, nothing else (no quotes, no explanation, no prefix)

TEXT TO TRANSLATE:
{text}"""


def translate_text(text: str, target_lang: str) -> str:
    """Tlumaczy tekst na target_lang. target_lang to kod: 'english', 'polish' itd."""
    client = _client()
    if not client or target_lang == "original" or not text.strip():
        return text

    lang_name = LANG_NAMES.get(target_lang)
    if not lang_name:
        return text

    prompt = TRANSLATE_PROMPT.format(target_lang=lang_name, text=text)

    try:
        response = client.models.generate_content(
            model=GEMINI_VISION_MODEL,
            contents=prompt,
        )
        translated = (response.text or "").strip()
        # Usun cudzyslowy jesli Gemini dodal
        if translated.startswith('"') and translated.endswith('"'):
            translated = translated[1:-1]
        return translated if translated else text
    except Exception as e:
        print(f"[translator] FAILED: {e}")
        return text


def translate_slide_texts(
    slide_texts: list[SlideText],
    target_lang: str,
    progress_callback=None,
) -> list[SlideText]:
    """
    Tlumaczy main_text kazdego slajdu na target_lang.
    Zwraca NOWA liste SlideText (nie mutuje oryginalu).
    """
    if target_lang == "original":
        return slide_texts

    import time
    from config import API_DELAY_SECONDS

    results = []
    total = len(slide_texts)
    for i, st in enumerate(slide_texts, start=1):
        translated = translate_text(st.main_text, target_lang)
        results.append(replace(st, main_text=translated))
        if progress_callback:
            progress_callback(i, total)
        if i < total:
            time.sleep(API_DELAY_SECONDS / 2)  # szybkie tlumaczenie

    return results
