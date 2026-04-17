"""
Pakowanie wyników do pliku ZIP.
Tworzy archiwum z ponumerowanymi slajdami + opis.txt.
"""
import zipfile
from pathlib import Path


def build_zip(
    slide_paths: list[Path],
    description: str,
    hashtags: list[str],
    output_dir: Path,
    zip_name: str = "karuzela.zip",
) -> Path:
    """
    Pakuje slajdy i opis do ZIP.

    slide_paths: lista ścieżek do slajdów (w kolejności)
    description: przepisany opis
    hashtags: lista hashtagów
    output_dir: katalog na plik ZIP
    zip_name: nazwa pliku ZIP

    Zwraca ścieżkę do pliku ZIP.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    zip_path = output_dir / zip_name

    with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
        # Dodaj slajdy
        for i, slide_path in enumerate(slide_paths, start=1):
            if slide_path and Path(slide_path).exists():
                arcname = f"slide_{i:02d}.png"
                zf.write(str(slide_path), arcname)

        # Dodaj opis
        opis_content = f"{description}\n\n{' '.join(hashtags)}"
        zf.writestr("opis.txt", opis_content)

    return zip_path
