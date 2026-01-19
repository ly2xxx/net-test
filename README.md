# NetPull + Streamlit POC

This POC (Proof of Concept) application tests the compatibility of **netpull** (Playwright-based web scraping) with **Streamlit**.

## Purpose

Verify that Playwright can run successfully within a Streamlit application environment by using the `netpull` package from PyPI.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install firefox
```

Or install all browsers:

```bash
playwright install
```

### 3. Run the Streamlit App

```bash
streamlit run app.py
```

The app will open in your default browser at `http://localhost:8501`

## Automated Extraction via URL

You can trigger automated extraction by passing parameters in the URL. This is useful for automated testing or integrating with other tools.

**Supported Parameters:**
- `url`: The target URL to extract (triggers auto-extraction)
- `browser`: `firefox`, `chrome`, or `webkit` (default: `firefox`)
- `headlessMode`: `true` or `false` (default: `true`)
- `timeout`: Timeout in seconds (default: `30`)

**Sample Call:**
[http://localhost:8501/?url=https://example.com&browser=firefox&headlessMode=true&timeout=45](http://localhost:8501/?url=https://example.com&browser=firefox&headlessMode=true&timeout=45)

## Features

### Browser Configuration
- Select browser: Firefox, Chrome, or Webkit
- Toggle headless mode
- Adjust timeout settings

### Extraction Options
- **Screenshot**: Capture full-page screenshot
- **HTML**: Extract and clean HTML content
- **Structured Data**: Extract title, headings, paragraphs, and links
- **Images**: Extract image metadata (src, alt, title)
- **Tables**: Extract table data as structured JSON
- **Forms**: Extract form structures and inputs
- **Metadata**: Extract OpenGraph and Twitter Card metadata

### Results Display
- Interactive tabs showing different extraction outputs
- Screenshot preview
- HTML viewer with download option
- JSON display for structured data
- System information panel

## Testing Scenarios

### Scenario 1: Basic Extraction (Default)
1. Use default URL: `https://example.com`
2. Enable Screenshot and HTML
3. Click "Extract Content"
4. ✅ **Expected**: Success with screenshot and HTML displayed

### Scenario 2: Full Extraction
1. Enter URL: `https://news.ycombinator.com`
2. Enable all extraction options
3. Click "Extract Content"
4. ✅ **Expected**: All tabs populated with data

### Scenario 3: Different Browsers
1. Test with Firefox (default)
2. Test with Chrome
3. Test with Webkit
4. ✅ **Expected**: All browsers work successfully

### Scenario 4: Non-headless Mode
1. Uncheck "Headless Mode"
2. Extract any URL
3. ✅ **Expected**: Browser window appears briefly during extraction

## Troubleshooting

### Error: "netpull is not installed"
```bash
pip install netpull
```

### Error: "Executable doesn't exist"
```bash
playwright install firefox
```

### Error: Browser launch timeout
- Increase timeout in sidebar
- Check internet connection
- Try headless mode

### Error: Permission denied on Linux/WSL
```bash
# Install system dependencies
playwright install-deps
```

## Expected Outputs

### Success Indicators
- ✅ Green success message
- Screenshot displayed in UI
- HTML content viewable
- Structured data in JSON format
- Files saved to `./poc_output/` directory

### Output Files
All extracted content is saved to `./poc_output/`:
- `{domain}_{timestamp}.png` - Screenshot
- `{domain}_{timestamp}.html` - Cleaned HTML

## System Requirements

- Python 3.8+
- Streamlit 1.45+
- netpull 0.1.0+
- Internet connection for web scraping

## Known Issues

### Streamlit Rerun Behavior
Streamlit may rerun the script on certain interactions. This is normal and doesn't affect the extraction process.

### Browser Installation
First run requires `playwright install` to download browser binaries (~200MB per browser).

### WSL2 Considerations
If running on WSL2, you may need additional dependencies:
```bash
sudo apt-get update
sudo apt-get install -y libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2
```

## Success Criteria

This POC is successful if:
1. ✅ netpull installs from PyPI without errors
2. ✅ Playwright browsers launch within Streamlit
3. ✅ Web content extraction completes successfully
4. ✅ Screenshots are captured and displayed
5. ✅ HTML and structured data are extracted correctly
6. ✅ No compatibility errors between Streamlit and Playwright

## Next Steps

If this POC succeeds, netpull can be confidently used in Streamlit applications for:
- Web monitoring dashboards
- Content extraction tools
- Automated screenshot services
- Data scraping interfaces
- Web archiving applications

## Streamlit Cloud Deployment

This app is fully compatible with **Streamlit Community Cloud**!

### Required Files
- `app.py` - Main application (includes auto-install logic)
- `requirements.txt` - Python dependencies
- `packages.txt` - System dependencies for Playwright browsers
- `.streamlit/config.toml` - Streamlit configuration

### Deployment Notes
- ✅ Browsers are installed automatically on first run
- ✅ Installation is cached for subsequent runs
- ⏱️ First deployment takes 2-3 minutes for browser setup
- 💾 Only Firefox is installed by default to save disk space

📖 **For detailed deployment instructions and troubleshooting, see [DEPLOYMENT.md](./DEPLOYMENT.md)**

## Resources

- [netpull on PyPI](https://pypi.org/project/netpull/)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Playwright Documentation](https://playwright.dev/python/)
- [Streamlit Cloud Deployment Guide](./DEPLOYMENT.md)
