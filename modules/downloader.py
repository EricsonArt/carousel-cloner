"""
Pobieranie postów z TikToka i Instagrama.

Strategia:
1. TikWM API (darmowe, bez klucza) — obsługuje TikTok /video/ i /photo/ (slideshow)
2. yt-dlp z cookies.txt (fallback dla Instagrama lub gdy TikWM nie zadziala)
3. Ręczne wgranie plików (w UI)
"""
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests


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
    raise ValueError("Nieobslugiwana platforma. Podaj link z TikToka lub Instagrama.")


def _extract_hashtags(text: str) -> list[str]:
    return re.findall(r"#\w+", text)


def _clean_tiktok_url(url: str) -> str:
    """Usuwa query string z TikTok URL (np. ?is_from_webapp=1)."""
    return url.split("?")[0].split("#")[0]


def _find_ffmpeg() -> str | None:
    location = shutil.which("ffmpeg")
    if location:
        return location
    known_paths = [
        r"C:\Users\cosmi\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin",
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
    ]
    for p in known_paths:
        if Path(p, "ffmpeg.exe").exists():
            return p
    return None


def _download_file(url: str, dest: Path, timeout: int = 30) -> bool:
    """Pobiera plik z URL do ścieżki docelowej."""
    try:
        r = requests.get(url, timeout=timeout, stream=True)
        if r.status_code == 200:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(str(dest), "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
            return dest.exists() and dest.stat().st_size > 100
    except Exception as e:
        print(f"[download_file] error: {e}")
    return False


def _download_via_tikwm(url: str, output_dir: Path) -> DownloadResult:
    """
    Pobiera post z TikToka przez TikWM API.
    Obsługuje /video/ i /photo/ (slideshow).
    Rzuca RuntimeError jesli nie zadziala.
    """
    clean_url = _clean_tiktok_url(url)

    resp = requests.post(
        "https://www.tikwm.com/api/",
        data={"url": clean_url, "hd": "1"},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"TikWM zwrocilo HTTP {resp.status_code}")

    payload = resp.json()
    if payload.get("code") != 0:
        raise RuntimeError(f"TikWM blad: {payload.get('msg', 'nieznany blad')}")

    data = payload.get("data") or {}
    description = (data.get("title") or "").strip()
    hashtags = _extract_hashtags(description)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    images = data.get("images") or []
    play_url = data.get("play") or data.get("wmplay") or ""

    # Przypadek 1: slideshow ze zdjęciami
    if images:
        saved_files = []
        for i, img_url in enumerate(images, start=1):
            dest = output_dir / f"media_{i:02d}.jpg"
            if _download_file(img_url, dest):
                saved_files.append(dest)
            else:
                print(f"[tikwm] Nie pobrano obrazu {i}/{len(images)}")

        if not saved_files:
            raise RuntimeError("TikWM zwrocilo linki do obrazow, ale zadnego nie udalo sie pobrac")

        return DownloadResult(
            media_type="images",
            files=saved_files,
            description=description,
            hashtags=hashtags,
        )

    # Przypadek 2: wideo
    if play_url:
        dest = output_dir / "media_01.mp4"
        if _download_file(play_url, dest, timeout=120):
            return DownloadResult(
                media_type="video",
                files=[dest],
                description=description,
                hashtags=hashtags,
            )
        raise RuntimeError("TikWM zwrocilo link do wideo, ale pobieranie nie powiodlo sie")

    raise RuntimeError("TikWM nie zwrocilo ani obrazow, ani wideo")


def _download_via_ytdlp(url: str, output_dir: Path, cookies_path: Path | None = None) -> DownloadResult:
    """Fallback: pobiera przez yt-dlp (glownie dla Instagrama)."""
    import yt_dlp

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = str(output_dir / "media_%(autonumber)s.%(ext)s")

    ydl_opts = {
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
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

    downloaded_files = []
    for f in sorted(output_dir.iterdir()):
        ext = f.suffix.lower()
        if ext in (".mp4", ".webm", ".mkv", ".mov", ".jpg", ".jpeg", ".png", ".webp"):
            downloaded_files.append(f)

    if not downloaded_files:
        raise RuntimeError("yt-dlp nie pobral zadnych plikow")

    video_files = [f for f in downloaded_files if f.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov")]
    image_files = [f for f in downloaded_files if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]

    if image_files and not video_files:
        return DownloadResult("images", image_files, description, hashtags)
    return DownloadResult("video", video_files or downloaded_files, description, hashtags)


def download_post(url: str, output_dir: Path, cookies_path: Path | None = None) -> DownloadResult:
    """
    Pobiera post z TikToka/Instagrama.
    TikTok → TikWM API (obsluguje /photo/ i /video/).
    Instagram → yt-dlp (z opcjonalnymi cookies).
    """
    platform = _detect_platform(url)

    if platform == "tiktok":
        # Strategia 1: TikWM (dziala dla /photo/ i /video/)
        try:
            return _download_via_tikwm(url, output_dir)
        except Exception as e:
            print(f"[downloader] TikWM failed: {e}. Fallback na yt-dlp.")
            # Strategia 2 (fallback): yt-dlp
            return _download_via_ytdlp(url, output_dir, cookies_path=cookies_path)

    # Instagram — tylko yt-dlp
    return _download_via_ytdlp(url, output_dir, cookies_path=cookies_path)


def load_manual_upload(
    files: list,  # lista UploadedFile ze Streamlit
    output_dir: Path,
    description: str = "",
    hashtags_text: str = "",
) -> DownloadResult:
    """Przetwarza pliki wgrane ręcznie przez UI."""
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
