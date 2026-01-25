# Marketing Funnel QR - Revised Implementation Plan

## Two-App Integration: NetPull → QR-Greeting

**The Key Insight:** NetPull extracts intelligence, QR-Greeting packages it for distribution.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     MARKETING FUNNEL QR ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────┐         ┌─────────────────────┐                  │
│   │     NET-TEST        │         │    QR-GREETING      │                  │
│   │   (NetPull App)     │         │                     │                  │
│   │                     │         │                     │                  │
│   │  • Extract landing  │ ──────▶ │  • Receive data     │                  │
│   │    page content     │  URL    │  • Add offer/CTA    │                  │
│   │  • Detect videos    │ params  │  • Generate QR      │                  │
│   │  • Get metadata     │         │  • Render funnel    │                  │
│   │                     │         │    experience       │                  │
│   └─────────────────────┘         └─────────────────────┘                  │
│                                                                             │
│   EXTRACTION POWER ────────────────▶ DISTRIBUTION POWER                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# PART 1: NetPull Changes (net-test.streamlit.app)

## 1.1 Files to Modify

| File | Change |
|------|--------|
| `app.py` | Add "Create Marketing Funnel" section after extraction |

## 1.2 New Feature: Marketing Funnel Builder

After successful extraction, show a new section:

```python
# =============================================================================
# ADDITION TO app.py - After extraction results, before "View Full Result"
# =============================================================================

import urllib.parse

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
    
    # Check for YouTube embeds in structured_data
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
```

## 1.3 UI Addition in app.py

Find the section after `st.success("✅ Extraction successful!")` and add:

```python
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
                            help="Add a video to make your funnel more engaging"
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
                    
                    st.markdown("---")
```

## 1.4 Testing the NetPull Side

```bash
cd net-test
streamlit run app.py

# Test with these URLs:
# Product page: https://www.amazon.com/dp/B0EXAMPLE
# Event page: https://www.eventbrite.com/e/example-event
# YouTube video page: https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

---

# PART 2: QR-Greeting Changes (qr-greeting.streamlit.app)

## 2.1 Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `tabs/funnel_tab.py` | CREATE | Main funnel creation UI |
| `utils/video_utils.py` | CREATE | Video URL validation |
| `tabs/view_page.py` | MODIFY | Render funnel experience when scanned |
| `tabs/__init__.py` | MODIFY | Add funnel_tab import |
| `app.py` | MODIFY | Add funnel tab to navigation |

## 2.2 New File: `utils/video_utils.py`

```python
"""
Video utility functions for Marketing Funnel feature
Handles video URL validation and metadata extraction
"""

import re
from typing import Tuple, Optional, Dict
from utils.url_utils import (
    convert_youtube_to_embed_url,
    convert_google_drive_to_embed_url
)


def validate_video_url(url: str) -> Tuple[bool, str, str]:
    """
    Validate if a URL is a supported video source.
    
    Args:
        url: Video URL to validate
        
    Returns:
        Tuple of (is_valid, video_type, error_message)
        video_type is one of: 'youtube', 'vimeo', 'direct', 'gdrive'
    """
    if not url:
        return False, "", "No URL provided"
    
    url_lower = url.lower()
    
    # YouTube
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        embed_url = convert_youtube_to_embed_url(url)
        if embed_url:
            return True, "YouTube", ""
        else:
            return False, "", "Invalid YouTube URL format"
    
    # Vimeo
    if 'vimeo.com' in url_lower:
        vimeo_match = re.search(r'vimeo\.com/(\d+)', url)
        if vimeo_match:
            return True, "Vimeo", ""
        else:
            return False, "", "Invalid Vimeo URL format"
    
    # Google Drive
    if 'drive.google.com' in url_lower:
        embed_url = convert_google_drive_to_embed_url(url)
        if embed_url:
            return True, "Google Drive", ""
        else:
            return False, "", "Invalid Google Drive URL format"
    
    # Direct video files
    video_extensions = ['.mp4', '.webm', '.mov', '.m4v', '.avi']
    if any(url_lower.endswith(ext) for ext in video_extensions):
        return True, "Direct Video", ""
    
    # Check for video in URL path (some CDNs)
    if any(ext in url_lower for ext in video_extensions):
        return True, "Direct Video", ""
    
    return False, "", "Unsupported video URL. Use YouTube, Vimeo, Google Drive, or direct video links (.mp4, .webm)"


def get_youtube_thumbnail(video_id: str, quality: str = "hq") -> str:
    """Get YouTube video thumbnail URL."""
    quality_map = {
        "maxres": "maxresdefault",
        "hq": "hqdefault",
        "mq": "mqdefault",
        "sd": "sddefault",
        "default": "default"
    }
    quality_slug = quality_map.get(quality, "hqdefault")
    return f"https://img.youtube.com/vi/{video_id}/{quality_slug}.jpg"


def convert_to_embed_url(url: str) -> Optional[str]:
    """Convert any supported video URL to embeddable format."""
    if not url:
        return None
        
    is_valid, video_type, _ = validate_video_url(url)
    
    if not is_valid:
        return None
    
    if video_type == "YouTube":
        return convert_youtube_to_embed_url(url)
    
    if video_type == "Vimeo":
        vimeo_match = re.search(r'vimeo\.com/(\d+)', url)
        if vimeo_match:
            return f"https://player.vimeo.com/video/{vimeo_match.group(1)}"
    
    if video_type == "Google Drive":
        return convert_google_drive_to_embed_url(url)
    
    if video_type == "Direct Video":
        return url
    
    return None
```

## 2.3 New File: `tabs/funnel_tab.py`

```python
"""
Marketing Funnel Tab
Create QR codes that convert video viewers to customers

This tab can be used:
1. Standalone - user enters all data manually
2. Pre-filled - data comes from NetPull via URL parameters
"""

import streamlit as st
import urllib.parse
from datetime import datetime
from typing import Optional, Dict
import io

from i18n import get_text as _
from config import THEME_COLORS, THEME_ICONS
from qr.generator import generate_qr_code
from qr.display import display_qr_with_protection, display_animated_qr
from utils.video_utils import validate_video_url, convert_to_embed_url
from utils.download_tracker import log_download


def load_funnel_params_from_url():
    """
    Load pre-filled data from URL parameters (from NetPull redirect).
    
    Expected parameters:
    - landing_url: CTA destination
    - video_url: Video to play
    - headline: Suggested headline
    - offer_text: Suggested offer description
    - og_image: Preview image
    - source: Where the data came from (e.g., 'netpull')
    """
    try:
        params = st.query_params
        
        # Check if we have NetPull data
        if 'landing_url' in params and 'source' not in st.session_state.get('funnel_loaded', {}):
            st.session_state.funnel_loaded = {'source': params.get('source', 'direct')}
            
            # Load all available params
            if 'landing_url' in params:
                st.session_state.funnel_landing_url = params['landing_url']
            if 'video_url' in params:
                st.session_state.funnel_video_url = params['video_url']
            if 'headline' in params:
                st.session_state.funnel_headline = params['headline']
            if 'offer_text' in params:
                st.session_state.funnel_offer_text = params['offer_text']
            if 'og_image' in params:
                st.session_state.funnel_og_image = params['og_image']
            
            # Show success banner
            st.session_state.funnel_show_prefill_banner = True
            
    except Exception as e:
        pass  # Silently handle param errors


def encode_funnel_to_url(funnel_data: Dict) -> str:
    """
    Encode funnel data to URL parameters for QR code.
    
    Uses compact parameter names to minimize QR code complexity.
    """
    base_url = "https://qr-greeting.streamlit.app/"
    
    params = {
        "tab": "view",
        "t": "funnel",  # type
        "f": funnel_data.get("brand", ""),  # from/brand
        "th": funnel_data.get("theme", "fireworks"),  # theme
        "bg": funnel_data.get("video_url", ""),  # background video
        "m": funnel_data.get("offer_text", ""),  # message/offer
        "fh": funnel_data.get("headline", ""),  # funnel headline
        "fc": funnel_data.get("cta_text", ""),  # funnel CTA text
        "fu": funnel_data.get("landing_url", ""),  # funnel CTA URL
        "fp": funnel_data.get("promo_code", ""),  # funnel promo
        "fg": funnel_data.get("urgency", ""),  # funnel urgency
    }
    
    # Remove empty params to save space
    params = {k: v for k, v in params.items() if v}
    
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def render() -> None:
    """Marketing Funnel tab main render function"""
    
    # Load URL parameters if present (from NetPull)
    load_funnel_params_from_url()
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 20px; color: white; 
                text-align: center; margin-bottom: 30px;">
        <h1>📈 Marketing Funnel QR</h1>
        <p style="font-size: 1.2em; opacity: 0.9;">
            Transform video content into high-converting QR experiences
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show pre-fill banner if data came from NetPull
    if st.session_state.get('funnel_show_prefill_banner', False):
        st.success("✅ **Data loaded from NetPull!** Review and customize below.")
        st.session_state.funnel_show_prefill_banner = False
    
    # Value proposition
    st.info("""
    **💡 The Attention Economy Problem:**  
    People watch your videos but never visit your website.
    
    **✨ The Solution:**  
    Create QR codes that play your video AND show your offer.
    
    **💪 Pro Tip:** Use [NetPull](https://net-test.streamlit.app) to auto-extract page data first!
    """)
    
    st.markdown("---")
    
    # ==========================================================================
    # Step 1: Video & Landing Page
    # ==========================================================================
    st.markdown("### 📹 Step 1: Your Content")
    
    col1, col2 = st.columns(2)
    
    with col1:
        video_url = st.text_input(
            "🎬 Video URL",
            value=st.session_state.get('funnel_video_url', ''),
            placeholder="https://youtube.com/watch?v=... or https://youtu.be/...",
            help="YouTube, Vimeo, or direct video URL (.mp4)",
            key="funnel_video_input"
        )
        
        # Validate and show preview
        if video_url:
            is_valid, video_type, error_msg = validate_video_url(video_url)
            if is_valid:
                st.success(f"✅ Valid {video_type} video")
            else:
                st.error(f"❌ {error_msg}")
    
    with col2:
        landing_url = st.text_input(
            "🔗 Landing Page URL",
            value=st.session_state.get('funnel_landing_url', ''),
            placeholder="https://yoursite.com/offer",
            help="Where users go after seeing your video + offer",
            key="funnel_landing_input"
        )
        
        if landing_url:
            if landing_url.startswith(("http://", "https://")):
                st.success("✅ Valid URL")
            else:
                st.warning("⚠️ URL should start with https://")
    
    st.markdown("---")
    
    # ==========================================================================
    # Step 2: Your Offer
    # ==========================================================================
    st.markdown("### 🎁 Step 2: Your Offer")
    
    col1, col2 = st.columns(2)
    
    with col1:
        headline = st.text_input(
            "📢 Headline",
            value=st.session_state.get('funnel_headline', '🎁 EXCLUSIVE OFFER'),
            placeholder="e.g., 🎁 EXCLUSIVE OFFER, 🔥 LIMITED TIME",
            help="Attention-grabbing headline (use emojis!)",
            key="funnel_headline_input"
        )
        
        offer_text = st.text_area(
            "💬 Offer Description",
            value=st.session_state.get('funnel_offer_text', 
                "Get 20% OFF your first order!\n\nWatch the video to see why customers love us."),
            height=100,
            placeholder="Describe your value proposition...",
            help="What's in it for them? Keep it concise.",
            key="funnel_offer_input"
        )
    
    with col2:
        cta_text = st.text_input(
            "🖱️ Call-to-Action Button",
            value="Shop Now →",
            placeholder="e.g., Shop Now, Learn More, Get Started",
            help="Action text for the button",
            key="funnel_cta_input"
        )
        
        promo_code = st.text_input(
            "🏷️ Promo Code (optional)",
            placeholder="e.g., SAVE20, WELCOME10",
            help="Discount code to display",
            key="funnel_promo_input"
        )
        
        urgency_text = st.text_input(
            "⏰ Urgency Text (optional)",
            placeholder="e.g., Offer expires in 48 hours",
            help="Create FOMO - scarcity drives action",
            key="funnel_urgency_input"
        )
    
    st.markdown("---")
    
    # ==========================================================================
    # Step 3: Branding & Theme
    # ==========================================================================
    st.markdown("### 🎨 Step 3: Branding")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        brand_name = st.text_input(
            "🏢 Brand Name",
            placeholder="Your Company Name",
            help="Shown as 'from' attribution",
            key="funnel_brand_input"
        )
    
    with col2:
        theme_options = {
            "fireworks": "🎆 Fireworks (Excitement)",
            "lights": "✨ Lights (Premium)",
            "confetti": "🎉 Confetti (Celebration)",
            "stars": "⭐ Stars (Aspirational)",
            "champagne": "🥂 Champagne (Luxury)",
        }
        
        selected_theme_label = st.selectbox(
            "🎨 Visual Theme",
            options=list(theme_options.values()),
            index=0,
            help="Sets the mood for your funnel",
            key="funnel_theme_select"
        )
        
        selected_theme = [k for k, v in theme_options.items() 
                         if v == selected_theme_label][0]
    
    with col3:
        visible_message = st.text_input(
            "📝 QR Label (optional)",
            placeholder="e.g., SCAN FOR 20% OFF",
            help="Text printed around the QR code",
            key="funnel_visible_msg_input"
        )
    
    st.markdown("---")
    
    # ==========================================================================
    # Step 4: Generate
    # ==========================================================================
    st.markdown("### 🚀 Step 4: Generate Your Funnel QR")
    
    # Validation
    can_generate = all([landing_url, headline, offer_text, cta_text])
    
    if not can_generate:
        missing = []
        if not landing_url: missing.append("Landing Page URL")
        if not headline: missing.append("Headline")
        if not offer_text: missing.append("Offer Description")
        if not cta_text: missing.append("CTA Button Text")
        st.warning(f"⚠️ Please fill in: {', '.join(missing)}")
    
    if not video_url:
        st.info("💡 **Tip:** Adding a video increases engagement significantly!")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_btn = st.button(
            "🚀 Generate Marketing Funnel QR",
            type="primary",
            disabled=not can_generate,
            use_container_width=True,
            key="funnel_generate_btn"
        )
    
    if generate_btn and can_generate:
        # Create funnel data
        funnel_data = {
            "video_url": video_url,
            "landing_url": landing_url,
            "headline": headline,
            "offer_text": offer_text,
            "cta_text": cta_text,
            "promo_code": promo_code,
            "urgency": urgency_text,
            "brand": brand_name,
            "theme": selected_theme
        }
        
        # Encode to URL
        funnel_url = encode_funnel_to_url(funnel_data)
        
        st.success("✅ Marketing Funnel QR Generated!")
        
        # Display results
        result_col1, result_col2 = st.columns([1, 1])
        
        with result_col1:
            st.markdown("#### 📱 Your Funnel QR Code")
            
            # Get theme colors
            theme_colors = THEME_COLORS.get(selected_theme, THEME_COLORS["fireworks"])
            
            # Generate QR
            qr_img = generate_qr_code(
                funnel_url,
                theme=selected_theme,
                visible_message=visible_message if visible_message else None,
                module_color=theme_colors["module"],
                position_ring_color=theme_colors["ring"]
            )
            
            display_qr_with_protection(qr_img, caption="Scan to preview your funnel")
            
            # Download button
            buf = io.BytesIO()
            qr_img.save(buf, format='PNG')
            filename = f"funnel_qr_{brand_name or 'marketing'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            st.download_button(
                label="⬇️ Download QR Code",
                data=buf.getvalue(),
                file_name=filename,
                mime="image/png",
                use_container_width=True,
                on_click=log_download,
                args=(filename,)
            )
        
        with result_col2:
            st.markdown("#### 👀 Preview: What Users See")
            
            # Mockup of the funnel experience
            st.markdown(f"""
            <div style="border: 3px solid #333; border-radius: 20px; padding: 15px; 
                        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
                        color: white; max-width: 350px; margin: 0 auto;">
                <div style="background: #000; border-radius: 10px; height: 150px; 
                            display: flex; align-items: center; justify-content: center;
                            margin-bottom: 15px; position: relative;">
                    <span style="font-size: 3em;">🎬</span>
                    <div style="position: absolute; bottom: 5px; right: 10px; 
                                background: rgba(255,255,255,0.2); padding: 2px 8px; 
                                border-radius: 3px; font-size: 0.8em;">
                        {"Video Playing..." if video_url else "No video"}
                    </div>
                </div>
                <div style="background: rgba(255,255,255,0.95); color: #333; 
                            padding: 20px; border-radius: 15px; text-align: center;">
                    <div style="font-size: 1.3em; font-weight: bold; margin-bottom: 10px;">
                        {headline}
                    </div>
                    <div style="font-size: 0.95em; margin-bottom: 15px; line-height: 1.4;">
                        {offer_text[:100]}{'...' if len(offer_text) > 100 else ''}
                    </div>
                    {"<div style='background: #ffd700; color: #333; padding: 5px 15px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; display: inline-block;'>🏷️ " + promo_code + "</div>" if promo_code else ""}
                    {"<div style='color: #e74c3c; font-size: 0.85em; margin-bottom: 10px;'>⏰ " + urgency_text + "</div>" if urgency_text else ""}
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                color: white; padding: 12px 25px; border-radius: 25px; 
                                font-weight: bold; cursor: pointer; display: inline-block;">
                        {cta_text}
                    </div>
                </div>
                <div style="text-align: center; margin-top: 10px; font-size: 0.8em; opacity: 0.7;">
                    {f"from {brand_name}" if brand_name else ""}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Usage tips
        with st.expander("📋 How to Use Your Funnel QR", expanded=True):
            st.markdown(f"""
            **Print it on:**
            - 📦 Product packaging
            - 📄 Flyers and brochures  
            - 🪧 Posters and banners
            - 💳 Business cards
            - 🧾 Receipts and invoices
            - 📱 Social media posts
            
            **Pro Tips:**
            1. **Test it first** - Scan with your phone to verify the experience
            2. **Track conversions** - Use UTM parameters in your landing URL
            3. **A/B test** - Try different headlines and CTAs
            4. **Update regularly** - Change offers to keep it fresh
            
            **Your Funnel URL:**
            ```
            {funnel_url}
            ```
            """)
```

## 2.4 Update: `tabs/view_page.py`

Add funnel rendering at the beginning of the `render()` function:

```python
def render() -> None:
    """Display greeting or funnel in mobile-friendly format."""
    query_params = dict(st.query_params)
    
    # Check if this is a funnel-type greeting
    greeting_type = query_params.get("t", "")
    
    if greeting_type == "funnel":
        render_funnel_view(query_params)
        return
    
    # ... existing greeting rendering code ...


def render_funnel_view(params: dict) -> None:
    """
    Render marketing funnel experience when QR is scanned.
    """
    # Extract funnel parameters (using compact names)
    headline = params.get("fh", "Special Offer")
    offer_text = params.get("m", "")
    cta_text = params.get("fc", "Learn More")
    cta_url = params.get("fu", "#")
    promo_code = params.get("fp", "")
    urgency = params.get("fg", "")
    video_url = params.get("bg", "")
    brand_name = params.get("f", "")
    theme = params.get("th", "fireworks")
    
    # Import here to avoid circular imports
    from utils.video_utils import convert_to_embed_url
    
    embed_url = convert_to_embed_url(video_url) if video_url else None
    
    # CSS for funnel experience
    st.markdown("""
    <style>
        .funnel-container {
            max-width: 100%;
            min-height: 100vh;
            background: #1a1a2e;
        }
        .funnel-video {
            width: 100%;
            height: 40vh;
        }
        .funnel-video iframe, .funnel-video video {
            width: 100%;
            height: 100%;
            border: none;
            object-fit: cover;
        }
        .funnel-overlay {
            background: white;
            margin: -30px 15px 15px 15px;
            padding: 25px;
            border-radius: 20px;
            box-shadow: 0 -10px 40px rgba(0,0,0,0.3);
            position: relative;
            z-index: 10;
        }
        .funnel-headline {
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
            text-align: center;
            margin-bottom: 15px;
        }
        .funnel-offer {
            font-size: 1.1em;
            color: #555;
            text-align: center;
            line-height: 1.6;
            margin-bottom: 20px;
            white-space: pre-wrap;
        }
        .funnel-promo {
            background: linear-gradient(135deg, #ffd700 0%, #ffb347 100%);
            color: #333;
            padding: 10px 20px;
            border-radius: 8px;
            font-weight: bold;
            font-size: 1.2em;
            text-align: center;
            margin-bottom: 15px;
        }
        .funnel-urgency {
            color: #e74c3c;
            text-align: center;
            font-size: 0.95em;
            margin-bottom: 15px;
        }
        .funnel-cta {
            display: block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white !important;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 30px;
            font-weight: bold;
            font-size: 1.2em;
            text-align: center;
            margin: 20px auto;
            max-width: 300px;
        }
        .funnel-brand {
            text-align: center;
            color: #888;
            font-size: 0.85em;
            margin-top: 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Build video HTML
    video_html = ""
    if embed_url:
        if 'youtube.com' in embed_url:
            video_id = embed_url.split('/')[-1]
            video_html = f'''
            <div class="funnel-video">
                <iframe src="{embed_url}?autoplay=1&mute=1&loop=1&playlist={video_id}&controls=0"
                        allow="autoplay; encrypted-media" allowfullscreen></iframe>
            </div>
            '''
        elif 'vimeo.com' in embed_url:
            video_html = f'''
            <div class="funnel-video">
                <iframe src="{embed_url}?autoplay=1&muted=1&loop=1&background=1"
                        allow="autoplay" allowfullscreen></iframe>
            </div>
            '''
        else:
            video_html = f'''
            <div class="funnel-video">
                <video autoplay muted loop playsinline>
                    <source src="{embed_url}" type="video/mp4">
                </video>
            </div>
            '''
    
    promo_html = f'<div class="funnel-promo">🏷️ {promo_code}</div>' if promo_code else ""
    urgency_html = f'<div class="funnel-urgency">⏰ {urgency}</div>' if urgency else ""
    brand_html = f'<div class="funnel-brand">from {brand_name}</div>' if brand_name else ""
    
    funnel_html = f'''
    <div class="funnel-container">
        {video_html}
        <div class="funnel-overlay">
            <div class="funnel-headline">{headline}</div>
            <div class="funnel-offer">{offer_text}</div>
            {promo_html}
            {urgency_html}
            <a href="{cta_url}" target="_blank" rel="noopener" class="funnel-cta">
                {cta_text}
            </a>
            {brand_html}
        </div>
    </div>
    '''
    
    import streamlit.components.v1 as components
    components.html(funnel_html, height=700, scrolling=True)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption("Powered by QR-Greeting")
        if st.button("Create Your Own Marketing Funnel", type="secondary", use_container_width=True):
            st.query_params.clear()
            st.query_params["tab"] = "funnel"
            st.rerun()
```

## 2.5 Update: `tabs/__init__.py`

```python
"""UI tab modules for the application"""
from tabs import demo_tab, funnel_tab  # Add funnel_tab
```

## 2.6 Update: `app.py`

Add the funnel tab to navigation. In the sidebar:

```python
with st.sidebar:
    # ... existing code ...
    
    # Add Marketing Funnel toggle
    show_funnel = st.checkbox(
        "📈 Marketing Funnel",
        value=False,
        help="Create QR codes for marketing campaigns"
    )
```

And in the tab rendering section, add `funnel_tab` similar to how `batch_tab` is added.

---

# PART 3: Testing

## 3.1 End-to-End Test Flow

```
1. Go to https://net-test.streamlit.app
2. Enter URL: https://www.example-product-page.com
3. Click "Extract Content"
4. See extracted title, description, etc.
5. (Optional) Add video URL in the funnel section
6. Click "📈 Create Marketing Funnel QR →"
7. Verify redirect to qr-greeting with pre-filled data
8. Add promo code, urgency text
9. Generate QR
10. Scan with phone
11. Verify video plays + CTA works
```

## 3.2 Test URLs

| Test Case | NetPull URL | Expected |
|-----------|-------------|----------|
| Product page | Amazon product URL | Title, price extracted |
| Event page | Eventbrite URL | Title, description extracted |
| YouTube page | YouTube video URL | Video detected |
| News article | BBC/CNN article | Title, description extracted |

---

# Summary: What Goes Where

| Component | Location | Purpose |
|-----------|----------|---------|
| `build_funnel_url()` | **net-test/app.py** | Build redirect URL to QR-Greeting |
| "Create Marketing Funnel" button | **net-test/app.py** | Trigger redirect |
| `funnel_tab.py` | **qr-greeting/tabs/** | Main funnel creation UI |
| `video_utils.py` | **qr-greeting/utils/** | Video validation |
| Funnel rendering | **qr-greeting/tabs/view_page.py** | Display when scanned |
| Tab navigation | **qr-greeting/app.py** | Add funnel tab |

---

*Document created: January 2026*
*Author: Claude (for Yang's implementation)*
*Target: Claude Code - implement in BOTH net-test AND qr-greeting apps*
