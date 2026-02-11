"""
Step 7: Cross-poster — YouTube Shorts + Telegram (100% free)
Extracts 60-sec vertical clip for Shorts, posts to Telegram channel.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def create_short_clip(
    video_path: Path,
    output_dir: Path,
    filename: str = "short_clip.mp4",
    duration: int = None,
) -> Path:
    """
    Extract a 60-second vertical (9:16) clip from the full video for YouTube Shorts.
    Takes the most interesting segment (first story after intro).
    """
    from moviepy.editor import VideoFileClip, CompositeVideoClip
    from config import SHORTS_WIDTH, SHORTS_HEIGHT, SHORTS_DURATION

    duration = duration or SHORTS_DURATION
    output_path = output_dir / filename

    logger.info(f"Creating {duration}s Short clip from {video_path.name}...")

    clip = VideoFileClip(str(video_path))

    # Take segment starting after intro (5s in) for the most engaging content
    start = min(5, clip.duration * 0.05)
    end = min(start + duration, clip.duration)
    segment = clip.subclip(start, end)

    # Crop to vertical (9:16) — center crop
    orig_w, orig_h = segment.size
    target_ratio = SHORTS_WIDTH / SHORTS_HEIGHT  # 9/16 = 0.5625
    
    # Calculate crop dimensions
    new_w = int(orig_h * target_ratio)
    if new_w > orig_w:
        new_w = orig_w
        new_h = int(orig_w / target_ratio)
        x1 = 0
        y1 = (orig_h - new_h) // 2
    else:
        new_h = orig_h
        x1 = (orig_w - new_w) // 2
        y1 = 0

    segment = segment.crop(x1=x1, y1=y1, x2=x1 + new_w, y2=y1 + new_h)
    segment = segment.resize((SHORTS_WIDTH, SHORTS_HEIGHT))

    # Export
    segment.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        logger=None,
    )

    clip.close()
    segment.close()

    logger.info(f"✅ Short clip saved: {output_path} ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return output_path


def upload_short(
    short_path: Path,
    title: str,
    description: str,
    tags: list[str],
) -> dict:
    """Upload the Short clip to YouTube using the same uploader."""
    from modules.uploader import upload_video

    # Add #Shorts to title and description for YouTube to recognize it
    short_title = f"{title} #Shorts"
    short_desc = f"{description}\n\n#Shorts #CurrentAffairs #DailyNews"

    result = upload_video(
        video_path=short_path,
        title=short_title[:100],
        description=short_desc,
        tags=tags + ["Shorts"],
        privacy="public",
    )

    logger.info(f"✅ Short uploaded: {result['url']}")
    return result


def post_to_telegram(
    title: str,
    youtube_url: str,
    summary: str = "",
) -> bool:
    """
    Post the video link and headline to Telegram channel/group.
    Uses Telegram Bot API (100% free, unlimited).
    """
    import requests as req
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        logger.warning("⚠ Telegram not configured, skipping post")
        return False

    message = (
        f"📺 *{title}*\n\n"
        f"{summary[:200] + '...' if len(summary) > 200 else summary}\n\n"
        f"▶️ Watch now: {youtube_url}\n\n"
        f"👍 Like | 🔔 Subscribe | 💬 Comment\n"
        f"#CurrentAffairs #DailyNews #India"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        response = req.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            logger.info("✅ Posted to Telegram")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Telegram post failed: {e}")
        return False


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Cross-poster module ready.")
    print("Use with full pipeline: python main.py")
