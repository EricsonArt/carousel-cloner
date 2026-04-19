"""
Przepisywanie opisu posta i hashtagów za pomocą Gemini.
Generuje podobny opis ale innymi słowami.
"""
from dataclasses import dataclass, field

from google import genai

from config import get_api_key, GEMINI_VISION_MODEL


def _client():
    key = get_api_key()
    return genai.Client(api_key=key) if key else None

REWRITE_PROMPT = """Rewrite the following carousel post description for Instagram/TikTok.

RULES:
- Keep the same message, tone and style
- Use DIFFERENT words (don't copy 1:1)
- Keep similar length
- Generate SIMILAR hashtags (not identical, but same topic)
- Write the rewritten description in this target language: {target_lang}
- Generate hashtags appropriate for that language (but brand names stay the same)

ORIGINAL DESCRIPTION:
{description}

ORIGINAL HASHTAGS:
{hashtags}

Return ONLY plain text in this format:
DESCRIPTION:
(rewritten description here)

HASHTAGS:
(hashtags separated by spaces, each starting with #)"""


LANG_DISPLAY = {
    "original": "same language as original",
    "polish": "Polish",
    "english": "English",
    "german": "German",
    "spanish": "Spanish",
    "french": "French",
    "italian": "Italian",
}


@dataclass
class RewrittenContent:
    description: str = ""
    hashtags: list[str] = field(default_factory=list)


def rewrite_description(
    original_description: str,
    original_hashtags: list[str],
    target_lang: str = "original",
) -> RewrittenContent:
    """
    Przepisuje opis i hashtagi przez Gemini na target_lang.
    target_lang: 'original' | 'polish' | 'english' | 'german' ...
    """
    client = _client()
    if not client:
        return RewrittenContent(
            description=original_description,
            hashtags=original_hashtags,
        )

    hashtags_str = " ".join(original_hashtags) if original_hashtags else "(none)"
    lang_display = LANG_DISPLAY.get(target_lang, "same language as original")
    prompt = REWRITE_PROMPT.format(
        description=original_description or "(no description)",
        hashtags=hashtags_str,
        target_lang=lang_display,
    )

    response = client.models.generate_content(
        model=GEMINI_VISION_MODEL,
        contents=prompt,
    )

    raw = response.text.strip()

    description = ""
    hashtags = []

    # Nowy format (po angielsku)
    if "DESCRIPTION:" in raw and "HASHTAGS:" in raw:
        parts = raw.split("HASHTAGS:")
        desc_part = parts[0].replace("DESCRIPTION:", "").strip()
        hash_part = parts[1].strip() if len(parts) > 1 else ""
        description = desc_part
        import re
        hashtags = re.findall(r"#\w+", hash_part)
    # Stary format (po polsku) — fallback
    elif "OPIS:" in raw and "HASHTAGI:" in raw:
        parts = raw.split("HASHTAGI:")
        desc_part = parts[0].replace("OPIS:", "").strip()
        hash_part = parts[1].strip() if len(parts) > 1 else ""
        description = desc_part
        import re
        hashtags = re.findall(r"#\w+", hash_part)
    else:
        description = raw
        import re
        hashtags = re.findall(r"#\w+", raw)

    return RewrittenContent(
        description=description,
        hashtags=hashtags if hashtags else original_hashtags,
    )
