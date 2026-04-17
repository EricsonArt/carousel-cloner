@echo off
echo ========================================
echo   Carousel Cloner — Start
echo ========================================
echo.

cd /d "%~dp0"

:: Sprawdz czy streamlit jest zainstalowany
python -c "import streamlit" 2>nul
if %errorlevel% neq 0 (
    echo Instalowanie zaleznosci...
    pip install -r requirements.txt
)

echo Uruchamiam dashboard...
python -m streamlit run app.py --server.port 8502

pause
