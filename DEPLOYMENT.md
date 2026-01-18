# Streamlit Cloud Deployment Guide

## Issue: Playwright App Failed to Start

### Root Cause
The Streamlit app failed to start on Streamlit Community Cloud with error:
```
Get "http://localhost:8501/healthz": dial tcp 127.0.0.1:8501: connect: connection refused
```

This occurred because **Playwright requires browser binaries** to be installed separately from the Python package. While `pip install playwright` was successful, the actual browser executables (Firefox, Chromium, WebKit) were not installed.

### Solution

The fix involves three components:

#### 1. **packages.txt** - System Dependencies
Created `poc/packages.txt` with Linux system libraries required by Playwright browsers:
- Core dependencies: libnss3, libnspr4, libatk, libcups2, etc.
- Browser-specific libraries for Firefox, Chromium rendering

#### 2. **Browser Auto-Install** - Modified app.py
Added automatic browser installation on first run:
```python
@st.cache_resource
def install_playwright_browsers():
    """Install Playwright browsers if not already installed"""
    if sys.platform == 'linux':
        subprocess.run([sys.executable, "-m", "playwright", "install", "firefox"])
```

This function:
- Runs only on Linux (Streamlit Cloud environment)
- Uses `@st.cache_resource` to run once and cache the result
- Installs only Firefox (default browser) to save time and disk space
- Runs before importing netpull/Playwright

#### 3. **Status Indicator** - User Feedback
Added UI feedback showing browser installation status in the app interface.

## Files Required for Deployment

For Streamlit Cloud deployment, ensure these files exist:

```
poc/
├── app.py                  # Main Streamlit app (with auto-install code)
├── requirements.txt        # Python dependencies (streamlit, netpull, playwright)
├── packages.txt           # System dependencies for browsers (NEW)
└── .streamlit/
    └── config.toml        # Streamlit configuration
```

## Deployment Steps

1. **Commit all changes** to your repository:
   ```bash
   git add poc/packages.txt poc/app.py
   git commit -m "Fix Playwright deployment with browser auto-install"
   git push
   ```

2. **Deploy to Streamlit Cloud:**
   - Go to share.streamlit.io
   - Select repository: `ly2xxx/playwright_poc`
   - Set main file path: `poc/app.py`
   - Deploy

3. **First Run:** The app will take longer to start initially while it installs Firefox browser (2-3 minutes)

4. **Subsequent Runs:** Browser installation is cached, so restarts are fast

## Testing Locally

To test the fix locally before deployment:

```bash
# Install dependencies
cd poc
pip install -r requirements.txt

# Run the app (browser auto-install will work on Linux)
streamlit run app.py
```

## Alternative Approaches Considered

1. **Post-install hook:** Not supported natively by Streamlit Cloud
2. **Install all browsers:** Too slow and uses excessive disk space (5GB+)
3. **playwright-python package:** Does not reliably auto-install on cloud platforms
4. **Docker deployment:** More complex, not necessary for this use case

## Why This Works

- **packages.txt:** Streamlit Cloud automatically installs system packages listed here
- **Auto-install in app:** Runs `playwright install firefox` on first app load
- **Caching:** `@st.cache_resource` ensures installation happens only once
- **Platform detection:** Only runs on Linux (Streamlit Cloud), not on local Windows/Mac development

## Expected Behavior After Fix

**First deployment:**
- Logs will show: "Installing Playwright Firefox browser..."
- Installation takes 2-3 minutes
- App starts successfully and displays UI

**Subsequent runs:**
- Cached installation is used
- App starts in ~30 seconds
- No reinstallation needed

## Monitoring

Check Streamlit Cloud logs for:
- ✅ "Playwright browsers installed successfully"
- ❌ Any browser installation errors
- ✅ App health check passes on port 8501
