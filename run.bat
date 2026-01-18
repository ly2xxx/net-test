@echo off
REM Quick run script for NetPull + Streamlit POC (Windows)

echo Starting NetPull + Streamlit POC...
echo.

REM Check if requirements are installed
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

python -c "import netpull" 2>nul
if errorlevel 1 (
    echo Installing netpull...
    pip install -r requirements.txt
    echo.
)

REM Check if playwright browsers are installed
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.firefox.launch(); p.stop()" 2>nul
if errorlevel 1 (
    echo Installing Playwright browsers...
    playwright install firefox
    echo.
)

echo All dependencies ready!
echo.
echo Starting Streamlit app...
echo Press Ctrl+C to stop
echo.

streamlit run app.py
