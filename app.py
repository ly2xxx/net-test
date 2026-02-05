"""
POC Streamlit App to test netpull (Playwright) compatibility with Streamlit
"""
import streamlit as st
import asyncio
import sys
import subprocess
import os
from pathlib import Path
import json
import urllib.parse
import threading
import time
from datetime import datetime

# Set event loop policy for Windows to avoid "NotImplementedError" with Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

print("🚀 Starting Streamlit App...")

import base64

def trigger_download(file_path: Path, file_name: str):
    """Generates a link to download the given file and auto-clicks it."""
    try:
        if not file_path.exists():
            st.warning(f"File not found for download: {file_name}")
            return
        
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            
        md = f"""
            <a href="data:file/octet-stream;base64,{b64}" download="{file_name}" id="download_link_{file_name}">Download {file_name}</a>
            <script>
                (function() {{
                    var link = document.getElementById("download_link_{file_name}");
                    if (link) {{
                        link.click();
                        console.log("Auto-clicked download for {file_name}");
                    }}
                }})();
            </script>
        """
        st.components.v1.html(md, height=0, width=0)
    except Exception as e:
        print(f"Error triggering download for {file_name}: {e}")


# =============================================================================
# QR-Greeting Integration
# =============================================================================

def build_qr_greeting_url(
    source_url: str,
    title: str = "",
    summary: str = "",
    theme: str = "lights"
) -> str:
    """
    Build a URL to QR-Greeting app with pre-filled content from extraction.

    Args:
        source_url: The original URL that was scraped
        title: Extracted page title
        summary: Brief content summary (first ~300 chars of structured data)
        theme: QR-Greeting theme (lights, fireworks, snowflake, etc.)

    Returns:
        Full URL to qr-greeting.streamlit.app with query parameters
    """
    message_parts = []

    if title:
        message_parts.append(f"📰 {title}")
        message_parts.append("")

    if summary:
        truncated = summary[:300] + "..." if len(summary) > 300 else summary
        message_parts.append(truncated)
        message_parts.append("")

    message_parts.append(f"🔗 {source_url}")

    params = {
        "tab": "create",
        "from": "Shared via NetPull",
        "to": "Friend",
        "message": "\n".join(message_parts),
        "url": source_url,
        "theme": theme
    }

    base_url = "https://qr-greeting.streamlit.app/"
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def detect_theme_from_url(url: str) -> str:
    """
    Auto-detect appropriate QR-Greeting theme based on URL domain.

    Args:
        url: The source URL

    Returns:
        Theme name string
    """
    url_lower = url.lower()

    if any(d in url_lower for d in ['youtube', 'vimeo', 'tiktok', 'video']):
        return "fireworks"
    elif any(d in url_lower for d in ['news', 'bbc', 'cnn', 'nytimes']):
        return "lights"
    elif any(d in url_lower for d in ['amazon', 'ebay', 'shop', 'etsy']):
        return "confetti"
    elif any(d in url_lower for d in ['github', 'gitlab', 'stackoverflow']):
        return "stars"
    elif any(d in url_lower for d in ['linkedin', 'twitter', 'facebook']):
        return "champagne"
    else:
        return "lights"


# =============================================================================
# Marketing Funnel QR Functions
# =============================================================================

def build_funnel_url(
    landing_url: str,
    video_url: str = "",
    page_title: str = "",
    page_description: str = "",
    og_image: str = "",
    detected_price: str = ""
) -> str:
    """
    Build URL to QR-Greeting's funnel tab with pre-filled data.
    
    Args:
        landing_url: The page that was scraped (becomes CTA destination)
        video_url: Video URL if detected or user-provided
        page_title: Extracted page title (becomes headline suggestion)
        page_description: Meta description (becomes offer text suggestion)
        og_image: Open Graph image URL (for preview)
        detected_price: Price if product page (for offer text)
    
    Returns:
        Full URL to qr-greeting funnel tab
    """
    # Auto-generate headline from title
    headline = ""
    if page_title:
        # Truncate and add emoji
        headline = f"✨ {page_title[:50]}" if len(page_title) > 50 else f"✨ {page_title}"
    
    # Auto-generate offer text
    offer_text = ""
    if page_description:
        offer_text = page_description[:200]
    if detected_price:
        offer_text = f"{offer_text}\n\n💰 {detected_price}" if offer_text else f"💰 {detected_price}"
    
    params = {
        "tab": "funnel",
        "landing_url": landing_url,
        "source": "netpull"  # Track that this came from NetPull
    }
    
    # Only add non-empty values
    if video_url:
        params["video_url"] = video_url
    if headline:
        params["headline"] = headline
    if offer_text:
        params["offer_text"] = offer_text
    if og_image:
        params["og_image"] = og_image
    
    base_url = "https://qr-greeting.streamlit.app/"
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def extract_video_from_page(structured_data: dict, metadata: dict) -> str:
    """
    Try to find video URL from extracted page data.
    
    Checks:
    1. OpenGraph video meta tag
    2. YouTube embeds in page
    3. Vimeo embeds in page
    4. Direct video URLs in content
    """
    video_url = ""
    
    # Check metadata for og:video
    if metadata:
        video_url = metadata.get('og:video', '') or metadata.get('og:video:url', '')
        if video_url:
            return video_url
    
    # TODO: Check for YouTube/Vimeo embeds in structured_data
    # (This would require NetPull to extract iframe src attributes)
    
    return video_url


def extract_price_from_page(structured_data: dict, metadata: dict) -> str:
    """
    Try to find product price from extracted page data.
    
    Checks:
    1. Schema.org price
    2. og:price:amount
    3. Common price patterns in content
    """
    if metadata:
        price = metadata.get('og:price:amount', '') or metadata.get('product:price:amount', '')
        currency = metadata.get('og:price:currency', '') or metadata.get('product:price:currency', 'USD')
        if price:
            return f"{currency} {price}"
    
    return ""


# =============================================================================
# QR-Greeting Keepalive Daemon
# =============================================================================

def _keepalive_daemon():
    """
    Daemon thread that pings qr-greeting.streamlit.app every 30 minutes
    to keep the service online (prevents Streamlit Cloud from sleeping).
    """
    import requests

    QR_GREETING_URL = "https://qr-greeting.streamlit.app/"
    PING_INTERVAL = 30 * 60  # 30 minutes in seconds

    while True:
        try:
            response = requests.get(QR_GREETING_URL, timeout=30)
            print(f"[{datetime.now().isoformat()}] Keepalive ping to qr-greeting: Status {response.status_code}")
        except requests.exceptions.Timeout:
            print(f"[{datetime.now().isoformat()}] Keepalive ping timeout (service may be waking up)")
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Keepalive ping failed: {e}")

        time.sleep(PING_INTERVAL)


@st.cache_resource
def start_keepalive_daemon():
    """
    Start the keepalive daemon thread (runs once due to cache_resource).
    The daemon pings qr-greeting.streamlit.app every 30 minutes.
    """
    thread = threading.Thread(target=_keepalive_daemon, daemon=True, name="qr-greeting-keepalive")
    thread.start()
    print(f"[{datetime.now().isoformat()}] Keepalive daemon started for qr-greeting.streamlit.app")
    return thread


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

# Start keepalive daemon for qr-greeting service
start_keepalive_daemon()

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
should_auto_download = "autoDownload" in qp and qp.get("autoDownload", "false").lower() == "true"

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
                    
                    if should_auto_download:
                        if result.screenshot_path and result.screenshot_path.exists():
                            trigger_download(result.screenshot_path, result.screenshot_path.name)
                        if result.html_path and result.html_path.exists():
                            trigger_download(result.html_path, result.html_path.name)

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

                    # =================================================
                    # Marketing Funnel QR Builder Section
                    # =================================================
                    st.markdown("---")
                    st.subheader("📈 Create Marketing Funnel QR")
                    
                    st.info("""
                    **Turn this page into a conversion machine!**  
                    Create a QR code that shows a video + your offer when scanned.
                    """)
                    
                    # Extract available data
                    page_title = ""
                    page_description = ""
                    og_image = ""
                    detected_video = ""
                    detected_price = ""
                    
                    if result.structured_data:
                        page_title = result.structured_data.get('title', '')
                    
                    if result.metadata:
                        page_description = result.metadata.get('og:description', '') or \
                                          result.metadata.get('description', '')
                        og_image = result.metadata.get('og:image', '')
                        detected_video = extract_video_from_page(
                            result.structured_data or {}, 
                            result.metadata or {}
                        )
                        detected_price = extract_price_from_page(
                            result.structured_data or {},
                            result.metadata or {}
                        )
                    
                    # Show what we extracted
                    with st.expander("📊 Extracted Data for Funnel", expanded=False):
                        st.write(f"**Page Title:** {page_title or 'Not found'}")
                        st.write(f"**Description:** {page_description[:100] + '...' if len(page_description) > 100 else page_description or 'Not found'}")
                        st.write(f"**OG Image:** {'Found ✅' if og_image else 'Not found'}")
                        st.write(f"**Video Detected:** {detected_video or 'None (you can add manually)'}")
                        st.write(f"**Price Detected:** {detected_price or 'None'}")
                    
                    # Video URL input (user can override or add)
                    funnel_col1, funnel_col2 = st.columns([3, 1])
                    
                    with funnel_col1:
                        video_url_input = st.text_input(
                            "🎬 Video URL (optional but recommended)",
                            value=detected_video,
                            placeholder="https://youtube.com/watch?v=... or https://youtu.be/...",
                            help="Add a video to make your funnel more engaging",
                            key="video_url_input"
                        )
                    
                    with funnel_col2:
                        st.write("")  # Spacing
                        st.write("")
                        if video_url_input:
                            # Quick validation
                            if 'youtube' in video_url_input.lower() or 'youtu.be' in video_url_input.lower():
                                st.success("✅ YouTube")
                            elif 'vimeo' in video_url_input.lower():
                                st.success("✅ Vimeo")
                            elif video_url_input.endswith(('.mp4', '.webm')):
                                st.success("✅ Direct")
                            else:
                                st.warning("⚠️ Unknown")
                    
                    # Build the funnel URL
                    funnel_redirect_url = build_funnel_url(
                        landing_url=url,  # The page they just scraped
                        video_url=video_url_input,
                        page_title=page_title,
                        page_description=page_description,
                        og_image=og_image,
                        detected_price=detected_price
                    )
                    
                    # Action buttons
                    btn_col1, btn_col2 = st.columns(2)
                    
                    with btn_col1:
                        st.link_button(
                            "📈 Create Marketing Funnel QR →",
                            url=funnel_redirect_url,
                            type="primary",
                            use_container_width=True
                        )
                    
                    with btn_col2:
                        if st.button("📋 Copy Funnel Link", use_container_width=True, key="copy_funnel_link"):
                            st.code(funnel_redirect_url, language=None)
                    
                    st.caption("💡 Opens QR-Greeting with your page data pre-filled. Add your offer details there.")

                    # =================================================
                    # QR-Greeting Integration Section
                    # =================================================
                    st.markdown("---")
                    st.subheader("🎁 Share as QR Greeting")

                    # Extract content for QR
                    qr_title = ""
                    qr_summary = ""

                    if result.structured_data:
                        qr_title = result.structured_data.get('title', '')
                        paragraphs = result.structured_data.get('paragraphs', [])
                        if paragraphs and len(paragraphs) > 0:
                            qr_summary = paragraphs[0] if paragraphs[0] else ""

                    # Auto-detect theme with option to override
                    auto_theme = detect_theme_from_url(url)
                    theme_options = ["lights", "fireworks", "snowflake", "stars",
                                     "confetti", "champagne", "hearts"]

                    qr_col1, qr_col2 = st.columns([3, 1])

                    with qr_col1:
                        st.write("📤 Transform this page into a shareable QR greeting!")

                    with qr_col2:
                        selected_theme = st.selectbox(
                            "Theme",
                            options=theme_options,
                            index=theme_options.index(auto_theme) if auto_theme in theme_options else 0,
                            key="qr_theme_selector",
                            label_visibility="collapsed"
                        )

                    # Build QR-Greeting URL
                    qr_greeting_url = build_qr_greeting_url(
                        source_url=url,
                        title=qr_title,
                        summary=qr_summary,
                        theme=selected_theme
                    )

                    btn_col1, btn_col2 = st.columns(2)

                    with btn_col1:
                        st.link_button(
                            "🎁 Create QR Greeting →",
                            url=qr_greeting_url,
                            type="primary",
                            use_container_width=True
                        )

                    with btn_col2:
                        if st.button("📋 Copy Greeting Link",
                                     use_container_width=True,
                                     key="copy_qr_greeting_link"):
                            st.code(qr_greeting_url, language=None)

                    st.caption("💡 Opens QR-Greeting with pre-filled content from this page")
                    st.markdown("---")

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
