"""
Przepisywanie opisu posta i hashtagów za pomocą Gemini.
Generuje podobny opis ale innymi słowami.
"""
from dataclasses import dataclass, field

from google import genai

from config import GEMINI_API_KEY, GEMINI_VISION_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

REWRITE_PROMPT = """Przepisz ponizszy opis posta z karuzeli na Instagramie/TikToku.

ZASADY:
- Zachowaj ten sam przekaz, ton i styl
- Uzyj INNYCH slow (nie kopiuj 1:1)
- Zachowaj podobna dlugosc
- Wygeneruj tez PODOBNE hashtagi (nie identyczne, ale z tej samej tematyki)
- Jezeli opis jest w danym jezyku, napisz w tym samym jezyku

ORYGINALNY OPIS:
{description}

ORYGINALNE HASHTAGI:
{hashtags}

Zwroc TYLKO czysty tekst w formacie:
OPIS:
(tutaj przepisany opis)

HASHTAGI:
(tutaj hashtagi oddzielone spacjami, kazdy zaczyna sie od #)"""


@dataclass
class RewrittenContent:
    description: str = ""
    hashtags: list[str] = field(default_factory=list)


def rewrite_description(
    original_description: str,
    original_hashtags: list[str],
) -> RewrittenContent:
    """
    Przepisuje opis i hashtagi za pomocą Gemini.
    Zwraca RewrittenContent z nowym opisem i hashtagami.
    """
    if not _client:
        return RewrittenContent(
            description=original_description,
            hashtags=original_hashtags,
        )

    hashtags_str = " ".join(original_hashtags) if original_hashtags else "(brak)"
    prompt = REWRITE_PROMPT.format(
        description=original_description or "(brak opisu)",
        hashtags=hashtags_str,
    )

    response = _client.models.generate_content(
        model=GEMINI_VISION_MODEL,
        contents=prompt,
    )

    raw = response.text.strip()

    # Parsuj odpowiedź
    description = ""
    hashtags = []

    if "OPIS:" in raw and "HASHTAGI:" in raw:
        parts = raw.split("HASHTAGI:")
        desc_part = parts[0].replace("OPIS:", "").strip()
        hash_part = parts[1].strip() if len(parts) > 1 else ""

        description = desc_part
        # Wyciągnij hashtagi
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
