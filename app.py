"""
POC Streamlit App to test netpull (Playwright) compatibility with Streamlit
"""
import streamlit as st
import asyncio
import sys
import subprocess
import os

# Set event loop policy for Windows to avoid "NotImplementedError" with Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

print("🚀 Starting Streamlit App...")

from pathlib import Path
import json

# Install Playwright browsers on first run (needed for Streamlit Cloud)
@st.cache_resource
def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed (cached after first run)"""
    if sys.platform != 'linux':
        return True  # Only needed on Linux (Streamlit Cloud)

    try:
        # Install system dependencies is handled by packages.txt on Streamlit Cloud
        
        # Install Firefox and Chromium browsers
        print("Installing Playwright browsers (firefox, chromium)...")
        browser_result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "firefox", "chromium"],
            capture_output=True,
            text=True,
            timeout=600 # Increased timeout for multiple browsers
        )

        if browser_result.returncode == 0:
            print("✅ Playwright browsers installed successfully")
            return True
        else:
            print(f"⚠️ Browser installation failed: {browser_result.stderr}")
            # Try installing just firefox as fallback
            print("Trying fallback: installing only firefox...")
            fallback_result = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "firefox"],
                capture_output=True,
                text=True,
                timeout=300
            ) 
            if fallback_result.returncode == 0:
                 print("✅ Playwright Firefox installed successfully (fallback)")
                 return True
            
            print(f"❌ Fallback installation failed: {fallback_result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Browser installation timed out")
        return False
    except Exception as e:
        print(f"❌ Error installing browser: {e}")
        return False

# Check if netpull is installed
try:
    from netpull import extract_webpage, ExtractionConfig, BrowserConfig
    NETPULL_AVAILABLE = True
except ImportError:
    NETPULL_AVAILABLE = False

st.set_page_config(page_title="NetPull + Streamlit POC", layout="wide")

st.title("NetPull + Streamlit Compatibility Test")
st.markdown("Testing if Playwright (via netpull) works within Streamlit environment")

# Check installation status
if not NETPULL_AVAILABLE:
    st.error("❌ netpull is not installed!")
    st.code("pip install netpull", language="bash")
    st.stop()

st.success("✅ netpull is installed and imported successfully")

# Initialize browsers on first run (deferred from module import)
if sys.platform == 'linux':
    with st.spinner("🔧 Initializing Playwright browsers (first run only, ~2-3 minutes)..."):
        browser_ready = ensure_playwright_browsers()

    if browser_ready:
        st.success("✅ Playwright browsers ready")
    else:
        st.error("❌ Failed to install Playwright browsers. Check logs for details.")
        st.stop()

# Sidebar configuration
st.sidebar.header("Configuration")

# Parse query parameters for defaults
qp = st.query_params
default_browser = qp.get("browser", "firefox").lower()
if default_browser not in ["firefox", "chrome", "webkit"]:
    default_browser = "firefox"

default_headless = qp.get("headlessMode", "true").lower() == "true"

try:
    default_timeout = int(qp.get("timeout", 30))
except ValueError:
    default_timeout = 30

default_url = qp.get("url", "https://example.com")
should_auto_extract = "url" in qp and "auto_extracted" not in st.session_state

# Browser selection
browser_options = ["firefox", "chrome", "webkit"]
browser_type = st.sidebar.selectbox(
    "Browser",
    options=browser_options,
    index=browser_options.index(default_browser)
)

# Headless mode
headless = st.sidebar.checkbox("Headless Mode", value=default_headless)

# Timeout
timeout = st.sidebar.slider("Timeout (seconds)", min_value=10, max_value=60, value=default_timeout)

# URL input
st.header("Web Extraction Test")
url = st.text_input(
    "Enter URL to extract",
    value=default_url,
    placeholder="https://example.com"
)

# Extraction options
st.subheader("Extraction Options")
col1, col2, col3 = st.columns(3)

with col1:
    extract_screenshot = st.checkbox("Screenshot", value=True)
    extract_html = st.checkbox("HTML", value=True)

with col2:
    extract_images = st.checkbox("Images", value=False)
    extract_tables = st.checkbox("Tables", value=False)

with col3:
    extract_forms = st.checkbox("Forms", value=False)
    extract_metadata = st.checkbox("Metadata", value=False)

# Extract button
manual_extract = st.button("Extract Content", type="primary")

if manual_extract or should_auto_extract:
    if should_auto_extract:
        st.session_state.auto_extracted = True
    if not url:
        st.warning("Please enter a URL")
    else:
        # Create output directory
        output_dir = Path("./poc_output")
        output_dir.mkdir(exist_ok=True)

        # Configure browser
        browser_config = BrowserConfig(
            browser_type=browser_type,
            headless=headless,
            timeout=timeout * 1000  # Convert to milliseconds
        )

        # Configure extraction
        extraction_config = ExtractionConfig(
            output_dir=output_dir,
            extract_screenshot=extract_screenshot,
            extract_html=extract_html,
            extract_images=extract_images,
            extract_tables=extract_tables,
            extract_forms=extract_forms,
            extract_metadata=extract_metadata
        )

        # Progress indicator
        with st.spinner(f"Extracting content from {url}..."):
            try:
                # Extract webpage
                result = extract_webpage(
                    url=url,
                    extraction_config=extraction_config,
                    browser_config=browser_config
                )

                # Display results
                if result.success:
                    st.success("✅ Extraction successful!")

                    # Create tabs for different outputs
                    tabs = []
                    tab_names = []

                    if result.screenshot_path:
                        tab_names.append("Screenshot")
                    if result.html_path:
                        tab_names.append("HTML")
                    if result.structured_data:
                        tab_names.append("Structured Data")
                    if result.images:
                        tab_names.append("Images")
                    if result.tables:
                        tab_names.append("Tables")
                    if result.forms:
                        tab_names.append("Forms")
                    if result.metadata:
                        tab_names.append("Metadata")

                    if tab_names:
                        tabs = st.tabs(tab_names)
                        tab_index = 0

                        # Screenshot tab
                        if result.screenshot_path:
                            with tabs[tab_index]:
                                st.subheader("Screenshot")
                                if result.screenshot_path.exists():
                                    st.image(str(result.screenshot_path), use_container_width=True)
                                    st.caption(f"Saved to: {result.screenshot_path}")
                                else:
                                    st.error(f"Screenshot file not found: {result.screenshot_path}")
                            tab_index += 1

                        # HTML tab
                        if result.html_path:
                            with tabs[tab_index]:
                                st.subheader("HTML Content")
                                if result.html_path.exists():
                                    with open(result.html_path, 'r', encoding='utf-8') as f:
                                        html_content = f.read()
                                    st.code(html_content[:5000], language="html")  # Show first 5000 chars
                                    if len(html_content) > 5000:
                                        st.info(f"Showing first 5000 characters. Total: {len(html_content)} characters")
                                    st.caption(f"Saved to: {result.html_path}")

                                    # Download button
                                    st.download_button(
                                        label="Download HTML",
                                        data=html_content,
                                        file_name=result.html_path.name,
                                        mime="text/html"
                                    )
                                else:
                                    st.error(f"HTML file not found: {result.html_path}")
                            tab_index += 1

                        # Structured data tab
                        if result.structured_data:
                            with tabs[tab_index]:
                                st.subheader("Structured Data")
                                st.json(result.structured_data)
                            tab_index += 1

                        # Images tab
                        if result.images:
                            with tabs[tab_index]:
                                st.subheader(f"Images ({len(result.images)})")
                                st.json(result.images)
                            tab_index += 1

                        # Tables tab
                        if result.tables:
                            with tabs[tab_index]:
                                st.subheader(f"Tables ({len(result.tables)})")
                                st.json(result.tables)
                            tab_index += 1

                        # Forms tab
                        if result.forms:
                            with tabs[tab_index]:
                                st.subheader(f"Forms ({len(result.forms)})")
                                st.json(result.forms)
                            tab_index += 1

                        # Metadata tab
                        if result.metadata:
                            with tabs[tab_index]:
                                st.subheader("Metadata")
                                st.json(result.metadata)
                            tab_index += 1

                    # Result summary
                    with st.expander("View Full Result Object"):
                        st.json(result.to_dict())

                else:
                    st.error(f"❌ Extraction failed: {result.error}")

            except Exception as e:
                st.error(f"❌ Error during extraction: {str(e)}")
                st.exception(e)

# System info
with st.expander("System Information"):
    st.write("**Python Version:**", sys.version)
    st.write("**Streamlit Version:**", st.__version__)

    if NETPULL_AVAILABLE:
        import netpull
        st.write("**NetPull Version:**", netpull.__version__)

    try:
        import playwright
        st.write("**Playwright Available:**", "✅ Yes")
    except ImportError:
        st.write("**Playwright Available:**", "❌ No")

# Instructions
with st.expander("📝 Instructions"):
    st.markdown("""
    ### How to use this POC:

    1. **Install dependencies:**
       ```bash
       pip install -r requirements.txt
       playwright install firefox
       ```

    2. **Run the app:**
       ```bash
       streamlit run app.py
       ```

    3. **Test extraction:**
       - Enter a URL (default: https://example.com)
       - Select browser and options
       - Click "Extract Content"
       - View results in tabs

    ### What this tests:

    - ✅ Playwright browser automation within Streamlit
    - ✅ Screenshot capture
    - ✅ HTML extraction and cleaning
    - ✅ Structured data extraction (headings, paragraphs, links)
    - ✅ Optional: Images, tables, forms, metadata extraction

    ### Expected outcome:

    If Playwright works correctly with Streamlit, you should see:
    - Successful extraction message
    - Screenshot displayed in the UI
    - HTML content viewable/downloadable
    - Structured data in JSON format

    If there are compatibility issues, you'll see error messages with details.
    """)
