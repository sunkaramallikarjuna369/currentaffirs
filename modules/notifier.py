"""
Step 8: Notifier — Telegram Bot API (100% free, unlimited)
Sends you a notification when the daily video is ready for review.
"""

import logging
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


def send_notification(
    title: str,
    youtube_url: str = "",
    status: str = "ready",
    extra_info: str = "",
) -> bool:
    """
    Send a Telegram notification about the video status.
    
    Args:
        title: Video title
        youtube_url: YouTube video URL
        status: ready, error, or processing
        extra_info: Additional details
    """
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        logger.warning("⚠ Telegram not configured — notification not sent")
        logger.info(f"Would have sent: Video '{title}' is {status}")
        return False

    now = datetime.now().strftime("%I:%M %p, %B %d, %Y")

    if status == "ready":
        emoji = "✅"
        message = (
            f"{emoji} *Today's video is ready!*\n"
            f"Review before 8:30 AM\n\n"
            f"📺 *Title:* {title}\n"
            f"🔗 *Preview:* {youtube_url}\n"
            f"🕐 *Generated at:* {now}\n"
        )
    elif status == "error":
        emoji = "❌"
        message = (
            f"{emoji} *Video generation failed!*\n\n"
            f"📺 *Title:* {title}\n"
            f"⚠️ *Error:* {extra_info}\n"
            f"🕐 *Time:* {now}\n"
        )
    else:
        emoji = "⏳"
        message = (
            f"{emoji} *Video processing...*\n\n"
            f"📺 *Title:* {title}\n"
            f"📊 *Status:* {extra_info}\n"
            f"🕐 *Time:* {now}\n"
        )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info(f"✅ Telegram notification sent ({status})")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Notification failed: {e}")
        return False


def send_daily_summary(
    results: dict,
) -> bool:
    """Send a comprehensive daily summary notification."""
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        return False

    now = datetime.now().strftime("%I:%M %p, %B %d, %Y")

    message = (
        f"📊 *Daily Pipeline Summary*\n"
        f"🕐 {now}\n\n"
    )

    steps = [
        ("📰", "News Fetched", results.get("news_count", "?")),
        ("📝", "Script Generated", results.get("story_count", "?") + " stories"),
        ("🎤", "Voiceover", results.get("voiceover_status", "?")),
        ("🎬", "Video Built", results.get("video_status", "?")),
        ("🖼️", "Thumbnail", results.get("thumbnail_status", "?")),
        ("📤", "YouTube Upload", results.get("upload_status", "?")),
        ("📱", "Short Clip", results.get("short_status", "?")),
        ("📢", "Telegram Post", results.get("telegram_status", "?")),
    ]

    for emoji, label, value in steps:
        message += f"{emoji} {label}: {value}\n"

    if results.get("youtube_url"):
        message += f"\n🔗 {results['youtube_url']}"

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        return response.status_code == 200
    except Exception:
        return False


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test notification (will warn if not configured)
    send_notification(
        title="Test Video - Daily Current Affairs",
        youtube_url="https://youtube.com/watch?v=test123",
        status="ready",
    )
