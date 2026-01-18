#!/bin/bash
# Quick run script for NetPull + Streamlit POC

echo "Starting NetPull + Streamlit POC..."
echo ""

# Check if requirements are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "❌ Streamlit not installed. Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

if ! python -c "import netpull" 2>/dev/null; then
    echo "❌ netpull not installed. Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

# Check if playwright browsers are installed
if ! python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); p.firefox.launch(); p.stop()" 2>/dev/null; then
    echo "⚠️  Playwright browsers not installed. Installing Firefox..."
    playwright install firefox
    echo ""
fi

echo "✅ All dependencies ready!"
echo ""
echo "Starting Streamlit app..."
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py
