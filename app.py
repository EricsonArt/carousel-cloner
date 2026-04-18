"""
Carousel Cloner — auto-pipeline Streamlit app.
Wklej link → wszystko dzieje się automatycznie → ZIP auto-pobiera się.
"""
import base64
import sys
import time
from pathlib import Path

import streamlit as st

PROJECT_DIR = Path(__file__).parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from config import OUTPUTS_DIR, DEFAULT_CTA_TEXT

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Carousel Cloner",
    page_icon="🎠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Premium CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Globalne */
.stApp {
    background: radial-gradient(ellipse at top, #1a0e2e 0%, #0a0514 50%, #050309 100%);
    background-attachment: fixed;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1100px; }

/* Hero */
.hero {
    text-align: center;
    padding: 3rem 1rem 2rem;
    margin-bottom: 1rem;
}
.hero-title {
    font-size: 4rem;
    font-weight: 900;
    letter-spacing: -2px;
    background: linear-gradient(135deg, #c084fc 0%, #f472b6 50%, #fb923c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1;
}
.hero-subtitle {
    font-size: 1.15rem;
    color: #a0a0b8;
    margin-top: 1rem;
    font-weight: 400;
}

/* Glass card */
.glass-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(168, 85, 247, 0.15);
    border-radius: 20px;
    padding: 2rem;
    margin: 1.5rem 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(30, 20, 45, 0.8) !important;
    border: 1.5px solid rgba(168, 85, 247, 0.3) !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.2s ease;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #c084fc !important;
    box-shadow: 0 0 0 3px rgba(192, 132, 252, 0.15) !important;
}

/* Primary button */
.stButton > button[kind="primary"],
.stDownloadButton > button {
    background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%) !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.9rem 2rem !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    color: white !important;
    box-shadow: 0 4px 20px rgba(168, 85, 247, 0.4) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.3px;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(168, 85, 247, 0.6) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    background: rgba(20, 15, 35, 0.5);
    padding: 0.4rem;
    border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 10px;
    padding: 0.7rem 1.4rem;
    color: #a0a0b8;
    font-weight: 600;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #a855f7 0%, #ec4899 100%) !important;
    color: white !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #a855f7, #ec4899) !important;
    border-radius: 10px !important;
}

/* Success banner */
.success-banner {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    color: #6ee7b7;
    font-size: 1.1rem;
    font-weight: 600;
    margin: 1rem 0;
}

/* Step indicator */
.step-row {
    display: flex;
    align-items: center;
    padding: 0.75rem 0;
    color: #d0d0e0;
    font-size: 0.95rem;
}
.step-icon {
    width: 26px;
    height: 26px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 12px;
    font-weight: bold;
    font-size: 0.85rem;
}
.step-done { background: linear-gradient(135deg, #10b981, #059669); color: white; }
.step-active { background: linear-gradient(135deg, #a855f7, #ec4899); color: white; animation: pulse 1.5s infinite; }
.step-pending { background: rgba(255,255,255,0.08); color: #666; border: 1px solid rgba(255,255,255,0.1); }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

/* Slide grid thumbnail */
.slide-thumb {
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    transition: transform 0.2s ease;
}
.slide-thumb:hover {
    transform: scale(1.03);
}

/* Labels */
.stTextInput label, .stTextArea label, .stFileUploader label {
    color: #d0d0e0 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* File uploader */
[data-testid="stFileUploaderDropzone"] {
    background: rgba(30, 20, 45, 0.5) !important;
    border: 2px dashed rgba(168, 85, 247, 0.4) !important;
    border-radius: 14px !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Session state ───────────────────────────────────────────────────────────
def _init_state():
    for key, default in [
        ("session_id", str(int(time.time()))),
        ("generated", False),
        ("zip_path", None),
        ("slides_preview", []),
        ("summary", {}),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default


_init_state()


def _session_dir() -> Path:
    d = OUTPUTS_DIR / f"job_{st.session_state['session_id']}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _reset():
    for key in ["generated", "zip_path", "slides_preview", "summary"]:
        st.session_state[key] = [] if key == "slides_preview" else ({} if key == "summary" else (False if key == "generated" else None))
    st.session_state["session_id"] = str(int(time.time()))


def _auto_download_html(zip_path: Path, filename: str = "karuzela.zip") -> str:
    """Zwraca HTML który auto-pobiera ZIP po stronie klienta."""
    data = zip_path.read_bytes()
    b64 = base64.b64encode(data).decode()
    return f"""
    <script>
    (function() {{
        const data = "data:application/zip;base64,{b64}";
        const link = document.createElement('a');
        link.href = data;
        link.download = "{filename}";
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        setTimeout(() => link.remove(), 1000);
    }})();
    </script>
    """


# ─── Hero ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1 class="hero-title">Carousel Cloner</h1>
    <p class="hero-subtitle">Wklej link do TikToka lub Instagrama → dostajesz gotową karuzelę do publikacji</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Main flow: wprowadzenie → automatyczny pipeline → auto-download
# ═══════════════════════════════════════════════════════════════════════════════

if not st.session_state["generated"]:
    from modules.image_generator import VARIATION_PROMPTS, get_prompt_for_intensity
    from modules.translator import LANGUAGES

    # ── Ustawienia: intensywnosc + jezyk ─────────────────────────────────────
    with st.expander("⚙️ Ustawienia", expanded=True):
        col_int, col_lang = st.columns(2)

        with col_int:
            st.markdown("**Jak mocno zmieniac slajdy?**")
            intensity_label = st.radio(
                "intensity",
                options=["Lekko", "Srednio", "Mocno"],
                index=1,
                horizontal=True,
                label_visibility="collapsed",
                key="intensity_label",
            )
            intensity_map = {"Lekko": "light", "Srednio": "medium", "Mocno": "strong"}
            intensity = intensity_map[intensity_label]
            st.markdown(
                {
                    "light": "<span style='color:#a0a0b8; font-size:0.82rem;'>Prawie identyczne — zmiana katu/koloru jednego detalu</span>",
                    "medium": "<span style='color:#a0a0b8; font-size:0.82rem;'>Ten sam produkt, inne tlo i otoczenie (rekomendowane)</span>",
                    "strong": "<span style='color:#a0a0b8; font-size:0.82rem;'>Inna scena, inny kat, inne rekwizyty — trudne do wykrycia</span>",
                }[intensity],
                unsafe_allow_html=True,
            )

        with col_lang:
            st.markdown("**Jezyk tekstu na slajdach**")
            lang_display = st.selectbox(
                "language",
                options=list(LANGUAGES.values()),
                index=0,
                label_visibility="collapsed",
                key="lang_display",
            )
            # Odwrotna mapa
            lang_code = {v: k for k, v in LANGUAGES.items()}[lang_display]
            st.markdown(
                "<span style='color:#a0a0b8; font-size:0.82rem;'>Tekst na slajdach "
                "i opis zostana przetlumaczone na wybrany jezyk.</span>",
                unsafe_allow_html=True,
            )

    # ── Zaawansowane: własny prompt ───────────────────────────────────────────
    base_prompt = get_prompt_for_intensity(intensity)

    with st.expander("⚙️ Zaawansowane — wlasny prompt AI", expanded=False):
        st.markdown(
            "<div style='color:#a0a0b8; font-size:0.85rem; margin-bottom:0.5rem;'>"
            "Prompt mowi AI jak ma modyfikowac slajdy. Mozesz napisac swoj wlasny "
            "(po polsku lub po angielsku) — wtedy ustawienie 'intensywnosci' zostaje nadpisane."
            "</div>",
            unsafe_allow_html=True,
        )
        user_prompt = st.text_area(
            "Prompt",
            value=st.session_state.get("user_prompt", base_prompt),
            height=240,
            key="user_prompt",
            label_visibility="collapsed",
        )
        if st.button("↺ Uzyj promptu z wybranej intensywnosci", use_container_width=False):
            st.session_state["user_prompt"] = base_prompt
            st.rerun()

    # ── Formularz ─────────────────────────────────────────────────────────────
    tab_url, tab_upload = st.tabs(["🔗 Wklej link", "📁 Wgraj pliki"])

    with tab_url:
        url = st.text_input(
            "Link do posta",
            placeholder="https://www.tiktok.com/@user/photo/...  lub  https://www.instagram.com/p/...",
            key="input_url",
            label_visibility="collapsed",
        )

        col_a, col_b = st.columns([3, 1])
        with col_a:
            cta_text = st.text_input(
                "Tekst CTA (ostatni slajd)",
                value=DEFAULT_CTA_TEXT,
                key="cta_url",
            )
        with col_b:
            st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
            start_url = st.button("✨ Sklonuj", type="primary", use_container_width=True, key="btn_url")

        auto_run_url = start_url and url.strip()

    with tab_upload:
        uploaded = st.file_uploader(
            "Wgraj slajdy lub wideo",
            type=["png", "jpg", "jpeg", "webp", "mp4", "mov"],
            accept_multiple_files=True,
            key="upload_files",
            label_visibility="collapsed",
        )

        col_u1, col_u2 = st.columns(2)
        with col_u1:
            manual_desc = st.text_area("Opis oryginalny (opcjonalne)", height=90, key="md")
        with col_u2:
            manual_hashtags = st.text_input("Hashtagi", placeholder="#viral #tiktok", key="mh")

        col_c, col_d = st.columns([3, 1])
        with col_c:
            cta_text_u = st.text_input("Tekst CTA (ostatni slajd)", value=DEFAULT_CTA_TEXT, key="cta_u")
        with col_d:
            st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
            start_upload = st.button("✨ Sklonuj", type="primary", use_container_width=True, key="btn_u")

        auto_run_upload = start_upload and uploaded

    # ── Info box ─────────────────────────────────────────────────────────────
    if not (auto_run_url or auto_run_upload):
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding: 1.2rem;">
            <span style="color:#a0a0b8; font-size:0.9rem;">
                💡 Wszystko dzieje się automatycznie — wklej, kliknij raz, czekaj. ZIP pobiera się sam.
            </span>
        </div>
        """, unsafe_allow_html=True)

    # ── Pipeline ──────────────────────────────────────────────────────────────
    if auto_run_url or auto_run_upload:
        session_dir = _session_dir()
        temp_dir = session_dir / "downloaded"
        slides_dir = session_dir / "original_slides"
        new_slides_dir = session_dir / "new_slides"

        progress = st.progress(0, text="Startuje...")
        status_container = st.empty()

        try:
            # ═══ KROK 1: Pobieranie / upload ═══
            progress.progress(10, text="📥 Pobieranie posta...")
            if auto_run_url:
                from modules.downloader import download_post
                download_result = download_post(url, temp_dir)
            else:
                from modules.downloader import load_manual_upload
                download_result = load_manual_upload(
                    uploaded, temp_dir,
                    description=manual_desc,
                    hashtags_text=manual_hashtags,
                )
                cta_text = cta_text_u

            # ═══ KROK 2: Ekstrakcja slajdów ═══
            progress.progress(20, text="🖼️ Wyciagam slajdy...")
            if download_result.media_type == "video" and download_result.files:
                from modules.slide_extractor import extract_slides
                slide_paths = extract_slides(download_result.files[0], slides_dir)
            else:
                import shutil
                slides_dir.mkdir(parents=True, exist_ok=True)
                slide_paths = []
                for i, f in enumerate(download_result.files, start=1):
                    dest = slides_dir / f"slide_{i:02d}{f.suffix}"
                    shutil.copy2(str(f), str(dest))
                    slide_paths.append(dest)

            if not slide_paths:
                raise RuntimeError("Nie znaleziono zadnych slajdow w poscie.")

            # ═══ KROK 3: OCR ═══
            progress.progress(30, text=f"🔍 Odczytuje tekst z {len(slide_paths)} slajdow...")
            from modules.ocr_reader import extract_all_slides

            def ocr_cb(cur, total):
                progress.progress(30 + int(15 * cur / total), text=f"🔍 OCR slajdu {cur}/{total}")

            slide_texts = extract_all_slides(slide_paths, progress_callback=ocr_cb)

            # ═══ KROK 3b: Tlumaczenie tekstow (jesli wybrany jezyk != original) ═══
            if lang_code != "original":
                progress.progress(43, text=f"🌐 Tlumacze na {lang_display}...")
                from modules.translator import translate_slide_texts

                def tr_cb(cur, total):
                    progress.progress(43 + int(2 * cur / total), text=f"🌐 Tlumaczenie {cur}/{total}")

                slide_texts = translate_slide_texts(slide_texts, lang_code, progress_callback=tr_cb)

            # ═══ KROK 4: Generowanie nowych slajdow (Nano Banana) ═══
            progress.progress(45, text="🎨 Generuje nowe slajdy (Nano Banana)...")
            from modules.image_generator import recreate_all_slides

            def gen_cb(cur, total):
                progress.progress(45 + int(40 * cur / total), text=f"🎨 Nowy slajd {cur}/{total}")

            # Wybierz prompt: custom (jesli edytowany) albo bazowy z wybranej intensywnosci
            user_p = st.session_state.get("user_prompt", "").strip()
            if user_p and user_p != base_prompt.strip():
                effective_prompt = user_p
            else:
                effective_prompt = base_prompt

            generated_slides = recreate_all_slides(
                slide_texts, new_slides_dir,
                source_images=slide_paths,
                progress_callback=gen_cb,
                custom_prompt=effective_prompt,
            )

            # ═══ KROK 5: CTA na ostatnim slajdzie ═══
            progress.progress(85, text="🎯 Dodaje CTA na ostatni slajd...")
            from modules.image_generator import add_cta_to_last_slide, generate_extra_cta_slide
            if generated_slides and generated_slides[-1]:
                last_original = generated_slides[-1]
                last_with_cta = new_slides_dir / "slide_last_with_cta.png"
                add_cta_to_last_slide(
                    last_original,
                    cta_text=cta_text,
                    existing_text=slide_texts[-1].main_text if slide_texts else "",
                    output_path=last_with_cta,
                )
                # Podmien ostatni slajd na wersje z CTA
                generated_slides[-1] = last_with_cta

            # ═══ KROK 6: Dodatkowy slajd CTA (opcjonalny) ═══
            progress.progress(90, text="🎨 Dodatkowy slajd CTA...")
            extra_cta_path = new_slides_dir / "slide_extra_cta.png"
            ref_slide = generated_slides[-1] if generated_slides else None

            extra_cta = None
            if ref_slide and Path(ref_slide).exists():
                extra_cta = generate_extra_cta_slide(cta_text, ref_slide, extra_cta_path)

            # Fallback: premium Pillow
            if not extra_cta:
                from modules.cta_generator import generate_cta
                colors = slide_texts[0].dominant_colors if slide_texts else None
                extra_cta = generate_cta(cta_text, colors, extra_cta_path)

            # ═══ KROK 7: Opis ═══
            progress.progress(94, text="✍️ Przepisuje opis i hashtagi...")
            from modules.description_rewriter import rewrite_description
            rewritten = rewrite_description(
                download_result.description,
                download_result.hashtags,
                target_lang=lang_code,
            )

            # ═══ KROK 8: Dwa ZIPy (z i bez dodatkowego slajdu) ═══
            progress.progress(98, text="📦 Pakuje ZIPy...")
            from modules.zip_builder import build_zip

            # ZIP bez extra (wlasciwa karuzela z CTA na ostatnim slajdzie)
            zip_without_extra = build_zip(
                generated_slides,
                rewritten.description,
                rewritten.hashtags,
                session_dir,
                zip_name="karuzela.zip",
            )

            # ZIP z extra slajdem CTA
            zip_with_extra = build_zip(
                generated_slides + [extra_cta],
                rewritten.description,
                rewritten.hashtags,
                session_dir,
                zip_name="karuzela_z_extra.zip",
            )

            progress.progress(100, text="✅ Gotowe!")
            time.sleep(0.3)
            progress.empty()

            # Zapisz do state
            st.session_state["generated"] = True
            st.session_state["zip_without_extra"] = str(zip_without_extra)
            st.session_state["zip_with_extra"] = str(zip_with_extra)
            st.session_state["slides_preview"] = [str(p) for p in generated_slides if p]
            st.session_state["extra_cta"] = str(extra_cta) if extra_cta else None
            st.session_state["summary"] = {
                "count": len(generated_slides),
                "description": rewritten.description,
                "hashtags": rewritten.hashtags,
                "original_slides": [str(p) for p in slide_paths],
            }
            st.rerun()

        except Exception as e:
            progress.empty()
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                st.error("❌ Limit Gemini API wyczerpany na dziś (darmowy plan).")
                st.warning(
                    "**Co zrobić?**\n"
                    "- Poczekaj do jutra (limit odnawia się o północy UTC)\n"
                    "- Lub włącz billing w Google AI Studio → [aistudio.google.com](https://aistudio.google.com) "
                    "(pierwsze $10 gratis przy rejestracji karty)"
                )
            else:
                st.error(f"❌ Błąd: {e}")
                st.info("💡 Sprobuj zakladki 'Wgraj pliki' — pobierz slajdy samodzielnie z ssstik.io/snaptik.app i wgraj.")


# ═══════════════════════════════════════════════════════════════════════════════
# WYNIK — slajdy + auto-download + opis
# ═══════════════════════════════════════════════════════════════════════════════
else:
    summary = st.session_state["summary"]
    slides_preview = st.session_state["slides_preview"]
    zip_without_extra = Path(st.session_state["zip_without_extra"])
    zip_with_extra = Path(st.session_state["zip_with_extra"])
    extra_cta_path = st.session_state.get("extra_cta")

    # Success banner
    st.markdown(f"""
    <div class="success-banner">
        ✨ Karuzela gotowa — CTA na ostatnim slajdzie + opis
    </div>
    """, unsafe_allow_html=True)

    # Auto-download (domyslnie bez extra)
    if not st.session_state.get("auto_dl_done"):
        st.components.v1.html(_auto_download_html(zip_without_extra), height=0)
        st.session_state["auto_dl_done"] = True

    # Dwa przyciski download + reset
    col_a, col_b, col_new = st.columns([2, 2, 1])
    with col_a:
        with open(zip_without_extra, "rb") as f:
            st.download_button(
                "⬇️ Pobierz karuzele",
                data=f.read(),
                file_name="karuzela.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True,
                help="Karuzela z CTA wbudowanym w ostatni slajd",
            )
    with col_b:
        with open(zip_with_extra, "rb") as f:
            st.download_button(
                "⬇️ + dodatkowy slajd CTA",
                data=f.read(),
                file_name="karuzela_z_extra.zip",
                mime="application/zip",
                use_container_width=True,
                help="Karuzela + dodatkowy slajd CTA na koncu",
            )
    with col_new:
        if st.button("🔄 Nowa", use_container_width=True):
            _reset()
            st.rerun()

    # Preview slajdow — porownanie side-by-side
    st.markdown("### 🔍 Porownanie: oryginal vs nowy")
    originals = summary.get("original_slides", [])

    for idx, new_path in enumerate(slides_preview):
        is_cta = idx >= len(originals)
        label = "CTA (dodatkowy slajd)" if is_cta else f"Slajd {idx + 1}"
        st.markdown(f"#### {label}")

        col_old, col_new = st.columns(2)
        with col_old:
            st.markdown("<div style='color:#a0a0b8; font-size:0.85rem; margin-bottom:0.4rem;'>ORYGINAL</div>", unsafe_allow_html=True)
            if not is_cta and idx < len(originals) and Path(originals[idx]).exists():
                st.image(originals[idx], use_container_width=True)
            else:
                st.markdown("<div style='color:#555; text-align:center; padding:2rem; border:1px dashed #333; border-radius:12px;'>—</div>", unsafe_allow_html=True)
        with col_new:
            st.markdown("<div style='color:#c084fc; font-size:0.85rem; margin-bottom:0.4rem;'>NOWY</div>", unsafe_allow_html=True)
            if Path(new_path).exists():
                st.image(new_path, use_container_width=True)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Extra CTA slajd — osobna sekcja
    if extra_cta_path and Path(extra_cta_path).exists():
        st.markdown("---")
        st.markdown("### 🎯 Dodatkowy slajd CTA (opcjonalny)")
        st.markdown(
            "<div style='color:#a0a0b8; font-size:0.85rem; margin-bottom:0.8rem;'>"
            "Ten slajd znajdziesz w pliku <code>karuzela_z_extra.zip</code>. "
            "Pobierz oddzielnie jesli chcesz dodac go na koniec karuzeli."
            "</div>",
            unsafe_allow_html=True,
        )
        c_left, c_center, c_right = st.columns([1, 2, 1])
        with c_center:
            st.image(extra_cta_path, use_container_width=True)

    # Opis do skopiowania
    st.markdown("### ✍️ Opis do posta")
    full_description = f"{summary['description']}\n\n{' '.join(summary['hashtags'])}"
    st.text_area(
        "Skopiuj i wklej przy publikacji",
        value=full_description,
        height=180,
        key="final_desc",
    )
