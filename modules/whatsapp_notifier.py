"""
WhatsApp Notifier — Free notifications via CallMeBot API.
No server needed, just a phone number and free API key.

Setup (one-time, 2 minutes):
1. Save +34 644 71 98 38 in your phone contacts as "CallMeBot"
2. Send this WhatsApp message to that number: "I allow callmebot to send me messages"
3. You'll receive an API key — paste it in .env as WHATSAPP_API_KEY
4. Add your phone number (with country code) as WHATSAPP_PHONE in .env

Cost: 100% FREE, unlimited messages.
"""

import logging
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)


def send_whatsapp_message(message: str, phone: str = None, api_key: str = None) -> bool:
    """
    Send a WhatsApp message via CallMeBot (free).
    
    Args:
        message: Text message to send
        phone: Phone number with country code (e.g., 919876543210)
        api_key: CallMeBot API key
    
    Returns:
        True if sent successfully
    """
    from config import WHATSAPP_PHONE, WHATSAPP_API_KEY
    
    phone = phone or WHATSAPP_PHONE
    api_key = api_key or WHATSAPP_API_KEY
    
    if not phone or phone == "your_whatsapp_phone_here":
        logger.warning("WhatsApp phone not configured")
        return False
    if not api_key or api_key == "your_whatsapp_api_key_here":
        logger.warning("WhatsApp API key not configured")
        return False
    
    encoded_msg = urllib.parse.quote(message)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_msg}&apikey={api_key}"
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as response:
            result = response.read().decode("utf-8")
            if response.status == 200:
                logger.info(f"WhatsApp message sent to {phone[:4]}****")
                return True
            else:
                logger.error(f"WhatsApp send failed: {result}")
                return False
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        return False


def send_pipeline_notification(
    status: str,
    video_title: str = None,
    video_url: str = None,
    error: str = None,
) -> bool:
    """Send pipeline status notification via WhatsApp."""
    
    if status == "completed":
        message = (
            f"*YouTube Pipeline Complete!*\n\n"
            f"Video: {video_title or 'Daily Current Affairs'}\n"
            f"Link: {video_url or 'Processing...'}\n\n"
            f"Your daily video has been uploaded successfully!"
        )
    elif status == "failed":
        message = (
            f"*Pipeline Failed*\n\n"
            f"Error: {error or 'Unknown error'}\n\n"
            f"Please check the dashboard for details."
        )
    else:
        message = f"*Pipeline Status: {status}*"
    
    return send_whatsapp_message(message)


def send_daily_summary(
    articles_count: int = 0,
    video_duration: str = "0:00",
    views: int = 0,
) -> bool:
    """Send daily summary via WhatsApp."""
    from datetime import datetime
    
    today = datetime.now().strftime("%B %d, %Y")
    message = (
        f"*Daily Summary - {today}*\n\n"
        f"Articles Covered: {articles_count}\n"
        f"Video Duration: {video_duration}\n"
        f"Channel Views Today: {views}\n\n"
        f"Keep growing!"
    )
    return send_whatsapp_message(message)


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing WhatsApp notification...")
    result = send_whatsapp_message("Hello from YouTube Current Affairs Platform! This is a test message.")
    print(f"Result: {'Sent!' if result else 'Failed - check .env settings'}")
