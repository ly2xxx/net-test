"""
Script to install Playwright browsers on Streamlit Cloud
This runs before the main app to ensure browsers are available
"""
import subprocess
import sys
import os

def install_playwright_browsers():
    """Install Playwright browsers if not already installed"""
    print("Checking Playwright browser installation...")

    try:
        # Install both Firefox and Chromium
        print("Installing Firefox and Chromium...")
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "firefox", "chromium"],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode == 0:
            print("✅ Playwright browsers installed successfully")
            print(result.stdout)
        else:
            print(f"⚠️ Warning: Browser installation returned code {result.returncode}")
            print(result.stderr)
            
            # Fallback: try just firefox
            print("Attempting fallback: installing only Firefox...")
            fallback = subprocess.run(
                [sys.executable, "-m", "playwright", "install", "firefox"],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if fallback.returncode == 0:
                print("✅ Playwright Firefox installed successfully (fallback)")
            else:
                print(f"❌ Fallback failed: {fallback.stderr}")

    except subprocess.TimeoutExpired:
        print("❌ Browser installation timed out")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error installing browsers: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_playwright_browsers()
