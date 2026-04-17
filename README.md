# Carousel Cloner

Rekreacja wiralowych karuzeli z TikToka i Instagrama.

## Jak używać

1. Pobierz slajdy samodzielnie ze [ssstik.io](https://ssstik.io) lub [snaptik.app](https://snaptik.app)
2. Wgraj je do aplikacji (zakładka "Wgraj pliki")
3. System przeanalizuje tekst (Gemini Vision)
4. Wygeneruje nowe slajdy z tym samym tekstem, ale innym tłem (Imagen 4)
5. Przepisze opis i hashtagi
6. Pobierz ZIP z gotową karuzelą

## Lokalne uruchomienie

```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your_key
python -m streamlit run app.py
```

## Deployment

Deploy na Streamlit Community Cloud:
1. Fork/Clone repo
2. Wejdź na https://share.streamlit.io
3. Wybierz repo, main branch, `app.py`
4. W Secrets dodaj: `GEMINI_API_KEY = "your_key"`

## Technologia

- **Streamlit** — UI
- **Gemini 2.5 Flash** — OCR i przepisywanie opisu
- **Imagen 4 Fast** — generowanie teł
- **Pillow** — nakładanie tekstu na tło
- **OpenCV** — detekcja zmian scen w wideo
- **yt-dlp** — opcjonalne pobieranie z URL
