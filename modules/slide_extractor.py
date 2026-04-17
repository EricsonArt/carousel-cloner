"""
Ekstrakcja slajdów z wideo (TikTok slideshow).
Używa OpenCV do detekcji zmian scen (hard cuts).
"""
from pathlib import Path

import cv2
import numpy as np

from config import SCENE_DIFF_THRESHOLD, MIN_SCENE_INTERVAL


def extract_slides(video_path: Path, output_dir: Path) -> list[Path]:
    """
    Wykrywa zmiany scen w wideo i zapisuje każdy slajd jako PNG.

    Algorytm:
    1. Czyta klatki sekwencyjnie
    2. Liczy różnicę między kolejnymi klatkami (mean absolute diff)
    3. Gdy diff > próg → zmiana sceny
    4. Zapisuje klatkę 0.5s po detekcji (unika transition frames)

    Zwraca listę ścieżek do wyekstrahowanych slajdów.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Nie mozna otworzyc wideo: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    min_interval_frames = int(MIN_SCENE_INTERVAL * fps)
    offset_frames = int(0.5 * fps)  # 0.5s po detekcji

    slides: list[Path] = []
    prev_gray = None
    frame_idx = 0
    last_cut_frame = -min_interval_frames  # pozwala na detekcję pierwszej sceny
    pending_capture_at: int | None = None

    # Zawsze zapisz pierwszą klatkę
    ret, first_frame = cap.read()
    if not ret:
        cap.release()
        return slides

    first_path = output_dir / "slide_01.png"
    cv2.imwrite(str(first_path), first_frame)
    slides.append(first_path)

    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    frame_idx = 1
    slide_num = 2

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Sprawdź czy mamy zaplanowany zapis
        if pending_capture_at is not None and frame_idx >= pending_capture_at:
            slide_path = output_dir / f"slide_{slide_num:02d}.png"
            cv2.imwrite(str(slide_path), frame)
            slides.append(slide_path)
            slide_num += 1
            pending_capture_at = None

        # Oblicz różnicę między klatkami
        diff = cv2.absdiff(prev_gray, curr_gray)
        mean_diff = float(np.mean(diff))

        # Detekcja zmiany sceny
        if (
            mean_diff > SCENE_DIFF_THRESHOLD
            and (frame_idx - last_cut_frame) > min_interval_frames
            and pending_capture_at is None
        ):
            last_cut_frame = frame_idx
            pending_capture_at = frame_idx + offset_frames

        prev_gray = curr_gray
        frame_idx += 1

    # Jeśli jest pending capture na końcu wideo, zapisz ostatnią klatkę
    if pending_capture_at is not None:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx - 1)
        ret, frame = cap.read()
        if ret:
            slide_path = output_dir / f"slide_{slide_num:02d}.png"
            cv2.imwrite(str(slide_path), frame)
            slides.append(slide_path)

    cap.release()
    return slides
