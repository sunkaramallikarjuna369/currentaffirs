"""
Centralized Configuration — All settings for the automated YouTube pipeline.
"""

import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ── Paths ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
MODULES_DIR = BASE_DIR / "modules"
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
OUTPUT_DIR = BASE_DIR / "output"

def get_today_output_dir():
    """Get/create today's output directory."""
    today = datetime.now().strftime("%Y-%m-%d")
    d = OUTPUT_DIR / today
    d.mkdir(parents=True, exist_ok=True)
    return d

# ── Free API Keys ────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WHATSAPP_PHONE = os.getenv("WHATSAPP_PHONE", "")
WHATSAPP_API_KEY = os.getenv("WHATSAPP_API_KEY", "")

# ── News Settings ────────────────────────────────────────────
NEWS_TOPIC = "India"
NEWS_LANGUAGE = "en"
NEWS_COUNT = 20  # Fetch top 20 headlines
NEWS_SELECT = 8   # AI selects top 8

# Google News RSS URLs (free, no key needed)
NEWS_RSS_FEEDS = [
    # Google News India - Top Stories
    "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en",
    # Google News India - Nation
    "https://news.google.com/rss/topics/CAAqIQgKIhtDQkFTRGdvSUwyMHZNRE55YXpBU0FtVnVLQUFQAQ?hl=en-IN&gl=IN&ceid=IN:en",
    # Google News India - Business
    "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pKVGlnQVAB?hl=en-IN&gl=IN&ceid=IN:en",
]

# ── AI Script Settings ───────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash"  # Newest free tier model
SCRIPT_DURATION_MINUTES = 5
SCRIPT_LANGUAGE = "English"  # or "Hindi" or "Hinglish"

# ── Voiceover Settings (edge-tts — 100% free) ───────────────
TTS_VOICE = "en-IN-NeerjaNeural"  # Options: en-IN-PrabhatNeural (male)
TTS_RATE = "+0%"      # Speed: -50% to +100%
TTS_VOLUME = "+0%"    # Volume: -50% to +100%

# ── Video Settings ───────────────────────────────────────────
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 24
VIDEO_BITRATE = "5000k"

# Shorts (vertical)
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
SHORTS_DURATION = 60  # seconds

# ── Thumbnail Settings ───────────────────────────────────────
THUMB_WIDTH = 1280
THUMB_HEIGHT = 720

# ── Colors & Design ──────────────────────────────────────────
COLORS = {
    "primary": "#FF0000",       # YouTube red
    "secondary": "#1A1A2E",     # Dark blue
    "accent": "#E94560",        # Coral red
    "bg_dark": "#0F0F23",       # Near black
    "bg_gradient_1": "#1A1A2E", # Gradient start
    "bg_gradient_2": "#16213E", # Gradient end
    "text_white": "#FFFFFF",
    "text_light": "#E0E0E0",
    "text_yellow": "#FFD700",
    "ticker_bg": "#CC0000",     # News ticker red
    "overlay_bg": (0, 0, 0, 180),  # Semi-transparent black
}

# ── YouTube Upload Settings ──────────────────────────────────
YOUTUBE_CATEGORY = "25"  # News & Politics
YOUTUBE_PRIVACY = "private"  # Options: public, private, unlisted
YOUTUBE_SCHEDULE_HOUR = 9   # 9:00 AM IST
YOUTUBE_SCHEDULE_MINUTE = 0
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# ── Channel Branding ─────────────────────────────────────────
CHANNEL_NAME = "Daily Current Affairs"
CHANNEL_TAGLINE = "Your Daily News in 5 Minutes"
DEFAULT_TAGS = [
    "current affairs", "daily news", "india news", "today news",
    "news today", "current affairs today", "daily current affairs",
    "upsc current affairs", "news analysis"
]
