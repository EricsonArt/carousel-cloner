"""
Konfiguracja projektu Carousel Cloner.
API keys przez python-dotenv (.env file).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# === KATALOGI ===
PROJECT_DIR = Path(__file__).parent
OUTPUTS_DIR = PROJECT_DIR / "outputs"
TEMP_DIR = PROJECT_DIR / "temp"
FONTS_DIR = PROJECT_DIR / "fonts"

# === API ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# === MODELE GEMINI ===
GEMINI_VISION_MODEL = "gemini-2.0-flash"   # 1500 req/day free (OCR, tłum., opis)
IMAGEN_MODEL = "imagen-4.0-fast-generate-001"

# === OBRAZY ===
SLIDE_WIDTH = 1080
SLIDE_HEIGHT = 1350  # Instagram carousel 4:5
OUTPUT_FORMAT = "PNG"

# === SCENE DETECTION ===
SCENE_DIFF_THRESHOLD = 30.0
MIN_SCENE_INTERVAL = 1.5  # sekundy

# === CTA ===
DEFAULT_CTA_TEXT = "Wejdz na flipzone.pl"

# === FONT ===
FONT_NAME = "Montserrat-Bold.ttf"
FONT_PATH = FONTS_DIR / FONT_NAME
FALLBACK_FONT = "arial.ttf"

# === RATE LIMITING ===
API_DELAY_SECONDS = 2

# === Twórz katalogi przy imporcie ===
for _d in [OUTPUTS_DIR, TEMP_DIR, FONTS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
