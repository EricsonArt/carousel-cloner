"""
Pobieranie postów z TikToka i Instagrama.

Strategia:
1. yt-dlp z plikiem cookies.txt (jeśli dostarczony)
2. yt-dlp bez cookies (działa dla niektórych publicznych postów)
3. Ręczne wgranie plików przez UI (zawsze działa)
"""
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DownloadResult:
    media_type: str  # "video" | "images"
    files: list[Path] = field(default_factory=list)
    description: str = ""
    hashtags: list[str] = field(default_factory=list)


def _detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "tiktok.com" in url_lower:
        return "tiktok"
    if "instagram.com" in url_lower:
        return "instagram"
    raise ValueError(
        "Nieobslugiwana platforma. Podaj link z TikToka lub Instagrama."
    )


def _extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#\w+", text)


def _find_ffmpeg() -> str | None:
    location = shutil.which("ffmpeg")
    if location:
        return location
    known_paths = [
        r"C:\Users\cosmi\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin",
        r"C:\Users\cosmi\AppData\Local\CapCut\Apps\8.3.0.3497",
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
    ]
    for p in known_paths:
        if Path(p, "ffmpeg.exe").exists():
            return p
    return None


def _collect_files(output_dir: Path) -> list[Path]:
    """Zbiera pobrane pliki z katalogu."""
    files = []
    for f in sorted(output_dir.iterdir()):
        if f.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov", ".jpg", ".jpeg", ".png", ".webp"):
            if not f.name.endswith(".json"):
                files.append(f)
    return files


def download_post(url: str, output_dir: Path, cookies_path: Path | None = None) -> DownloadResult:
    """
    Pobiera post z TikToka/Instagrama przez yt-dlp.

    url: link do posta
    output_dir: katalog na pobrane pliki
    cookies_path: opcjonalny plik cookies.txt wyeksportowany z przeglądarki

    Rzuca RuntimeError gdy nie udało się pobrać.
    """
    import yt_dlp

    _detect_platform(url)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = str(output_dir / "media_%(autonumber)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "writeinfojson": False,
        "format": "best",
        "noplaylist": True,
    }

    ffmpeg_loc = _find_ffmpeg()
    if ffmpeg_loc:
        ydl_opts["ffmpeg_location"] = ffmpeg_loc

    if cookies_path and Path(cookies_path).exists():
        ydl_opts["cookiefile"] = str(cookies_path)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    description = info.get("description", "") or ""
    hashtags = _extract_hashtags(description)

    downloaded_files = _collect_files(output_dir)
    if not downloaded_files:
        raise RuntimeError("Pobieranie nie zwrócilo zadnych plikow.")

    video_files = [f for f in downloaded_files if f.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov")]
    image_files = [f for f in downloaded_files if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]

    if image_files and not video_files:
        return DownloadResult("images", image_files, description, hashtags)
    return DownloadResult("video", video_files or downloaded_files, description, hashtags)


def load_manual_upload(
    files: list,  # lista obiektów UploadedFile ze Streamlit
    output_dir: Path,
    description: str = "",
    hashtags_text: str = "",
) -> DownloadResult:
    """
    Przetwarza pliki wgrane ręcznie przez użytkownika.

    files: lista plików z st.file_uploader
    output_dir: katalog do zapisu plików
    description: opis wpisany ręcznie przez użytkownika
    hashtags_text: hashtagi wpisane ręcznie (oddzielone spacjami)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []
    for i, f in enumerate(files, start=1):
        suffix = Path(f.name).suffix.lower() or ".png"
        dest = output_dir / f"media_{i:02d}{suffix}"
        dest.write_bytes(f.read())
        saved_paths.append(dest)

    video_files = [p for p in saved_paths if p.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov")]
    image_files = [p for p in saved_paths if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]

    hashtags = re.findall(r"#\w+", hashtags_text) if hashtags_text else []

    if image_files and not video_files:
        return DownloadResult("images", image_files, description, hashtags)
    return DownloadResult("video", video_files or saved_paths, description, hashtags)
