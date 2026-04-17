"""
Carousel Cloner — Streamlit Dashboard
Rekreacja wiralowych karuzeli z TikToka/Instagrama.

Uruchom: python -m streamlit run app.py --server.port 8502
"""
import sys
import time
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config import OUTPUTS_DIR, TEMP_DIR, DEFAULT_CTA_TEXT

# ─── Konfiguracja strony ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Carousel Cloner",
    page_icon="🎠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS — ciemny motyw ──────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }

    .main-header {
        background: linear-gradient(135deg, #1a0a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem 2.5rem;
        border-radius: 14px;
        margin-bottom: 1.8rem;
        text-align: center;
        border: 1px solid #2a1a4e;
        box-shadow: 0 4px 24px rgba(100,0,255,0.12);
    }
    .main-header h1 { color: #a855f7; font-size: 2.4rem; margin: 0; }
    .main-header p  { color: #8b7fc7; margin: 0.5rem 0 0; font-size: 1rem; }

    .tip-box {
        background: #1a1a2e;
        border-left: 4px solid #a855f7;
        padding: 0.9rem 1.2rem;
        border-radius: 0 8px 8px 0;
        color: #b0a0d0;
        font-size: 0.9rem;
        margin: 0.8rem 0;
    }
    .success-box {
        background: linear-gradient(135deg, #0d3d25, #145c38);
        border: 1px solid #00e676;
        padding: 1rem 1.4rem;
        border-radius: 10px;
        color: #00e676;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0;
    }
    .warning-box {
        background: #2d1f0d;
        border: 1px solid #ff9800;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        color: #ffb74d;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>Carousel Cloner</h1>
    <p>Rekreacja wiralowych karuzeli z TikToka i Instagrama</p>
</div>
""", unsafe_allow_html=True)

# ─── Session State ────────────────────────────────────────────────────────────
if "phase" not in st.session_state:
    st.session_state["phase"] = 1
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(int(time.time()))


def _session_dir() -> Path:
    d = OUTPUTS_DIR / f"job_{st.session_state['session_id']}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _run_analysis_pipeline(download_result, session_dir):
    """Krok 2+3: ekstrakcja slajdów + OCR — wspólny dla obu trybów."""
    slides_dir = session_dir / "original_slides"

    # Ekstrakcja slajdów
    with st.status("Ekstrakcja slajdow...", expanded=True) as status:
        if download_result.media_type == "video" and download_result.files:
            st.write("Wykrywanie zmian scen w wideo...")
            from modules.slide_extractor import extract_slides
            slide_paths = extract_slides(download_result.files[0], slides_dir)
            if not slide_paths:
                status.update(label="Blad!", state="error")
                st.error("Nie znaleziono zadnych slajdow w wideo. Sprobuj trybu 'Wgraj pliki'.")
                return None
            st.write(f"Znaleziono {len(slide_paths)} slajdow")
        elif download_result.media_type == "images":
            slide_paths = download_result.files
            # Kopiuj do slides_dir
            slides_dir.mkdir(parents=True, exist_ok=True)
            new_paths = []
            for i, f in enumerate(slide_paths, start=1):
                dest = slides_dir / f"slide_{i:02d}{f.suffix}"
                import shutil
                shutil.copy2(str(f), str(dest))
                new_paths.append(dest)
            slide_paths = new_paths
            st.write(f"Zaladowano {len(slide_paths)} obrazow")
        else:
            status.update(label="Blad!", state="error")
            st.error("Nie znaleziono plikow do przetworzenia.")
            return None

        st.session_state["original_slides"] = slide_paths
        status.update(label=f"Wyekstrahowano {len(slide_paths)} slajdow!", state="complete")

    # OCR
    with st.status("Analiza tekstu na slajdach (Gemini Vision)...", expanded=True) as status:
        from modules.ocr_reader import extract_all_slides

        progress_bar = st.progress(0)

        def ocr_progress(current, total):
            progress_bar.progress(current / total, text=f"Slajd {current}/{total}")

        slide_texts = extract_all_slides(slide_paths, progress_callback=ocr_progress)
        st.session_state["slide_texts"] = slide_texts
        status.update(label="Analiza zakonczona!", state="complete")

    return slide_paths


# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 1 — Wejście
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state["phase"] == 1:
    st.markdown("### Faza 1: Zrodlo karuzeli")

    cta_text = st.text_input(
        "Tekst CTA (ostatni slajd)",
        value=DEFAULT_CTA_TEXT,
        key="input_cta",
    )

    # ── Dwa tryby ──────────────────────────────────────────────────────────────
    tab_url, tab_upload = st.tabs(["URL (automatyczny)", "Wgraj pliki (niezawodny)"])

    # ── TAB 1: URL ────────────────────────────────────────────────────────────
    with tab_url:
        st.markdown('<div class="warning-box">TikTok blokuje automatyczne pobieranie. Jesli URL nie zadziala, uzyj zakladki "Wgraj pliki" po prawo. Potrzebny plik cookies.txt z przegladarki.</div>', unsafe_allow_html=True)

        url = st.text_input(
            "Link do posta (TikTok lub Instagram)",
            placeholder="https://www.tiktok.com/@user/video/...",
            key="input_url",
        )

        with st.expander("Mam plik cookies.txt (opcjonalne — pomaga z TikTokiem)"):
            cookies_file = st.file_uploader(
                "Wgraj plik cookies.txt (wyeksportowany z przegladarki)",
                type=["txt"],
                key="cookies_upload",
            )
            st.markdown('<div class="tip-box">Jak zdobyc cookies.txt: zainstaluj w Chrome/Edge rozszerzenie "Get cookies.txt LOCALLY", wejdz na tiktok.com (zalogowany), kliknij rozszerzenie i "Export cookies". Wgraj plik tutaj.</div>', unsafe_allow_html=True)

        if st.button("Pobierz i analizuj", type="primary", use_container_width=True):
            if not url.strip():
                st.error("Podaj link do posta!")
            else:
                session_dir = _session_dir()
                temp_dir = session_dir / "downloaded"

                # Zapisz cookies.txt jeśli dostarczony
                cookies_path = None
                if cookies_file:
                    cookies_path = temp_dir / "cookies.txt"
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    cookies_path.write_bytes(cookies_file.read())

                with st.status("Pobieranie posta...", expanded=True) as status:
                    st.write("Laczenie z platforma...")
                    try:
                        from modules.downloader import download_post
                        result = download_post(url, temp_dir, cookies_path=cookies_path)
                        st.write(f"Pobrano: {result.media_type} ({len(result.files)} plikow)")
                        st.session_state["download_result"] = result
                        st.session_state["cta_text"] = cta_text
                        status.update(label="Pobrano!", state="complete")
                    except Exception as e:
                        status.update(label="Blad pobierania!", state="error")
                        err_msg = str(e)
                        if "blocked" in err_msg.lower() or "IP" in err_msg:
                            st.error(
                                "TikTok zablokował pobieranie. Rozwiązania:\n"
                                "1. Wgraj plik cookies.txt (instrukcja wyżej)\n"
                                "2. Użyj zakładki 'Wgraj pliki' — pobierz slajdy samodzielnie\n"
                                f"\nSzczegóły błędu: {err_msg[:200]}"
                            )
                        else:
                            st.error(f"Blad: {err_msg[:300]}")
                        st.stop()

                slide_paths = _run_analysis_pipeline(
                    st.session_state["download_result"], session_dir
                )
                if slide_paths:
                    st.session_state["phase"] = 2
                    st.rerun()

    # ── TAB 2: Ręczny upload ──────────────────────────────────────────────────
    with tab_upload:
        st.markdown('<div class="tip-box">Pobierz slajdy samodzielnie ze strony <b>ssstik.io</b> lub <b>snaptik.app</b> (wklej link do TikToka, pobierz zdjecia/wideo), a nastepnie wgraj je tutaj.</div>', unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Wgraj slajdy (obrazy PNG/JPG) lub wideo (MP4)",
            type=["png", "jpg", "jpeg", "webp", "mp4", "mov", "webm"],
            accept_multiple_files=True,
            key="manual_upload",
        )

        col1, col2 = st.columns(2)
        with col1:
            manual_desc = st.text_area(
                "Oryginalny opis posta (wklej z TikToka/IG)",
                placeholder="Napisz lub wklej oryginał opisu...",
                key="manual_desc",
                height=100,
            )
        with col2:
            manual_hashtags = st.text_input(
                "Hashtagi (opcjonalne)",
                placeholder="#viral #tiktok #tips",
                key="manual_hashtags",
            )

        if st.button("Zaladuj i analizuj", type="primary", use_container_width=True, key="btn_upload"):
            if not uploaded_files:
                st.error("Wgraj co najmniej jeden plik!")
            else:
                session_dir = _session_dir()
                temp_dir = session_dir / "downloaded"

                with st.status("Ladowanie plikow...", expanded=True) as status:
                    from modules.downloader import load_manual_upload
                    result = load_manual_upload(
                        uploaded_files,
                        temp_dir,
                        description=manual_desc,
                        hashtags_text=manual_hashtags,
                    )
                    st.session_state["download_result"] = result
                    st.session_state["cta_text"] = cta_text
                    status.update(label=f"Zaladowano {len(result.files)} plikow!", state="complete")

                slide_paths = _run_analysis_pipeline(result, session_dir)
                if slide_paths:
                    st.session_state["phase"] = 2
                    st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 2 — Przegląd i edycja
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["phase"] == 2:
    st.markdown("### Faza 2: Przegladanie i edycja slajdow")

    slide_paths = st.session_state.get("original_slides", [])
    slide_texts = st.session_state.get("slide_texts", [])
    download_result = st.session_state.get("download_result")

    if not slide_paths or not slide_texts:
        st.error("Brak danych. Wróc do fazy 1.")
        if st.button("Wróc"):
            st.session_state["phase"] = 1
            st.rerun()
        st.stop()

    st.markdown(f'<div class="tip-box">Znaleziono <b>{len(slide_paths)} slajdow</b>. Sprawdz czy tekst jest poprawny i edytuj jesli trzeba. Mozesz tez poprawic bledy OCR zanim wygenerujesz nowe slajdy.</div>', unsafe_allow_html=True)

    # Grid slajdów
    for i in range(0, len(slide_paths), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(slide_paths):
                break
            with col:
                st.markdown(f"**Slajd {idx + 1}**")
                if Path(slide_paths[idx]).exists():
                    st.image(str(slide_paths[idx]), use_container_width=True)
                original_text = slide_texts[idx].main_text if idx < len(slide_texts) else ""
                st.text_area(
                    f"Tekst slajdu {idx + 1}",
                    value=original_text,
                    key=f"text_{idx}",
                    height=100,
                )

    # Opis i hashtagi
    st.markdown("---")
    st.markdown("**Oryginalny opis:**")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        original_desc = download_result.description if download_result else ""
        st.text_area("Opis", value=original_desc, height=100, disabled=True)
    with col_d2:
        original_tags = download_result.hashtags if download_result else []
        st.text_input("Hashtagi", value=" ".join(original_tags), disabled=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Wróc", use_container_width=True):
            st.session_state["phase"] = 1
            st.rerun()
    with col2:
        if st.button("Generuj nowe slajdy", type="primary", use_container_width=True):
            # Aktualizuj teksty z edytowanych pól
            for idx in range(len(slide_texts)):
                if f"text_{idx}" in st.session_state:
                    slide_texts[idx].main_text = st.session_state[f"text_{idx}"]
            st.session_state["slide_texts"] = slide_texts
            st.session_state["phase"] = 3
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# FAZA 3 — Generowanie
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state["phase"] == 3:
    st.markdown("### Faza 3: Generowanie nowych slajdow")

    slide_texts = st.session_state.get("slide_texts", [])
    original_slides = st.session_state.get("original_slides", [])
    download_result = st.session_state.get("download_result")
    cta_text = st.session_state.get("cta_text", DEFAULT_CTA_TEXT)
    session_dir = _session_dir()
    new_slides_dir = session_dir / "new_slides"

    if not slide_texts:
        st.error("Brak danych. Wróc do fazy 1.")
        st.stop()

    # ── Generowanie (tylko raz) ───────────────────────────────────────────────
    generated_slides = st.session_state.get("generated_slides")

    if generated_slides is None:
        # Krok 1: Nowe slajdy (Nano Banana — image-to-image edit)
        with st.status("Generowanie nowych slajdow (Nano Banana)...", expanded=True) as status:
            from modules.image_generator import recreate_all_slides

            bar = st.progress(0)
            info = st.empty()

            def gen_progress(current, total):
                bar.progress(current / total)
                info.write(f"Slajd {current}/{total}...")

            generated_slides = recreate_all_slides(
                slide_texts,
                new_slides_dir,
                source_images=original_slides,
                progress_callback=gen_progress,
            )
            st.session_state["generated_slides"] = generated_slides
            status.update(label=f"Wygenerowano {len(generated_slides)} slajdow!", state="complete")

        # Krok 2: CTA
        with st.status("Generowanie slajdu CTA...", expanded=True) as status:
            from modules.cta_generator import generate_cta
            colors = slide_texts[0].dominant_colors if slide_texts else None
            cta_path = new_slides_dir / "slide_cta.png"
            generate_cta(cta_text, colors, cta_path)
            generated_slides.append(cta_path)
            st.session_state["generated_slides"] = generated_slides
            status.update(label="CTA gotowe!", state="complete")

        # Krok 3: Opis
        with st.status("Przepisywanie opisu i hashtagow...", expanded=True) as status:
            from modules.description_rewriter import rewrite_description
            original_desc = download_result.description if download_result else ""
            original_tags = download_result.hashtags if download_result else []
            rewritten = rewrite_description(original_desc, original_tags)
            st.session_state["rewritten"] = rewritten
            status.update(label="Opis przepisany!", state="complete")

        # Krok 4: ZIP
        with st.status("Pakowanie do ZIP...", expanded=True) as status:
            from modules.zip_builder import build_zip
            rewritten = st.session_state["rewritten"]
            zip_path = build_zip(
                generated_slides,
                rewritten.description,
                rewritten.hashtags,
                session_dir,
            )
            st.session_state["zip_path"] = zip_path
            status.update(label="ZIP gotowy!", state="complete")

        st.rerun()

    # ── Wyniki ────────────────────────────────────────────────────────────────
    st.markdown('<div class="success-box">Karuzela zostala wygenerowana!</div>', unsafe_allow_html=True)

    st.markdown("#### Porownanie: oryginal vs nowy")
    for i in range(len(original_slides)):
        if i >= len(generated_slides):
            break
        gen_slide = generated_slides[i]
        if gen_slide is None or not Path(gen_slide).exists():
            continue
        cols = st.columns(2)
        with cols[0]:
            st.markdown(f"**Oryginal — Slajd {i + 1}**")
            if Path(original_slides[i]).exists():
                st.image(str(original_slides[i]), use_container_width=True)
        with cols[1]:
            st.markdown(f"**Nowy — Slajd {i + 1}**")
            st.image(str(gen_slide), use_container_width=True)

    # CTA
    if len(generated_slides) > len(original_slides):
        cta_slide = generated_slides[-1]
        if cta_slide and Path(cta_slide).exists():
            st.markdown("**Slajd CTA:**")
            c = st.columns([1, 2, 1])
            with c[1]:
                st.image(str(cta_slide), use_container_width=True)

    # Opis
    st.markdown("---")
    rewritten = st.session_state.get("rewritten")
    if rewritten:
        st.markdown("#### Przepisany opis:")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.text_area("Opis", value=rewritten.description, height=120)
        with col_r2:
            st.text_area("Hashtagi", value=" ".join(rewritten.hashtags), height=60)

    # Download ZIP
    st.markdown("---")
    zip_path = st.session_state.get("zip_path")
    if zip_path and Path(zip_path).exists():
        with open(str(zip_path), "rb") as f:
            st.download_button(
                label="Pobierz ZIP z karuzela",
                data=f.read(),
                file_name="karuzela.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
            )

    if st.button("Nowa karuzela (reset)", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
