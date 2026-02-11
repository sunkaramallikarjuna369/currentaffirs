"""
Step 6: YouTube Uploader — YouTube Data API v3 (Free: 10,000 units/day)
Handles OAuth2 authentication and video upload with metadata.
"""

import logging
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

TOKEN_FILE = Path(__file__).parent.parent / "token.pickle"
CLIENT_SECRETS_FILE = Path(__file__).parent.parent / "client_secrets.json"


def get_authenticated_service():
    """
    Authenticate with YouTube Data API v3 using OAuth2.
    First run opens browser for consent. Token is saved for reuse.
    """
    from config import YOUTUBE_SCOPES, YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET

    credentials = None

    # Load saved token
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            credentials = pickle.load(f)

    # Refresh or get new credentials
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            logger.info("Refreshing expired token...")
            credentials.refresh(Request())
        else:
            # Check if client_secrets.json exists, if not create it
            if not CLIENT_SECRETS_FILE.exists():
                if not YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_ID == "your_youtube_client_id_here":
                    raise ValueError(
                        "❌ YouTube credentials not set!\n"
                        "1. Go to https://console.cloud.google.com\n"
                        "2. Create a project → Enable YouTube Data API v3\n"
                        "3. Create OAuth 2.0 credentials (Desktop App)\n"
                        "4. Download client_secrets.json OR set YOUTUBE_CLIENT_ID/SECRET in .env"
                    )
                
                # Create client_secrets.json from env vars
                secrets = {
                    "installed": {
                        "client_id": YOUTUBE_CLIENT_ID,
                        "client_secret": YOUTUBE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"]
                    }
                }
                with open(CLIENT_SECRETS_FILE, "w") as f:
                    json.dump(secrets, f, indent=2)
                logger.info(f"Created {CLIENT_SECRETS_FILE} from .env credentials")

            logger.info("Starting OAuth2 flow (browser will open)...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), YOUTUBE_SCOPES
            )
            credentials = flow.run_local_server(port=0)

        # Save token
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)
        logger.info("Token saved for future use")

    return build("youtube", "v3", credentials=credentials)


def upload_video(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_path: Path = None,
    category: str = None,
    privacy: str = None,
    schedule_time: datetime = None,
) -> dict:
    """
    Upload a video to YouTube.
    
    Args:
        video_path: Path to the video file
        title: Video title
        description: Video description
        tags: List of tags
        thumbnail_path: Optional thumbnail image path
        category: YouTube category ID (default: News & Politics = 25)
        privacy: public, private, or unlisted
        schedule_time: If set, schedules the video for this time
    
    Returns:
        dict with video_id and url
    """
    from config import YOUTUBE_CATEGORY, YOUTUBE_PRIVACY

    category = category or YOUTUBE_CATEGORY
    privacy = privacy or YOUTUBE_PRIVACY

    youtube = get_authenticated_service()

    # Build request body
    body = {
        "snippet": {
            "title": title[:100],  # YouTube max 100 chars
            "description": description[:5000],  # Max 5000 chars
            "tags": tags[:500],  # Max 500 tags
            "categoryId": category,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    # Schedule if time provided
    if schedule_time:
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = schedule_time.isoformat()
        logger.info(f"Video will be scheduled for: {schedule_time}")

    # Upload video
    logger.info(f"Uploading video: {video_path.name} ({video_path.stat().st_size / 1024 / 1024:.1f} MB)")
    
    media = MediaFileUpload(
        str(video_path),
        chunksize=10 * 1024 * 1024,  # 10MB chunks
        resumable=True,
        mimetype="video/mp4",
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    logger.info(f"✅ Video uploaded: {video_url}")

    # Set thumbnail
    if thumbnail_path and thumbnail_path.exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
            ).execute()
            logger.info("✅ Thumbnail set successfully")
        except Exception as e:
            logger.warning(f"Could not set thumbnail (may need channel verification): {e}")

    return {
        "video_id": video_id,
        "url": video_url,
        "title": title,
    }


def get_schedule_time(hour: int = None, minute: int = None) -> datetime:
    """Get the next scheduled time in IST (UTC+5:30)."""
    from config import YOUTUBE_SCHEDULE_HOUR, YOUTUBE_SCHEDULE_MINUTE

    hour = hour or YOUTUBE_SCHEDULE_HOUR
    minute = minute or YOUTUBE_SCHEDULE_MINUTE

    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    
    schedule = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # If time has passed today, schedule for tomorrow
    if schedule <= now:
        schedule += timedelta(days=1)

    return schedule


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("YouTube Uploader - Test Mode")
    print(f"Schedule time: {get_schedule_time()}")
    print("\nTo test upload, run the full pipeline with: python main.py")
