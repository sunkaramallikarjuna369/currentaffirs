"""
Channel Manager — Create, configure, and manage YouTube channel from the platform.
Uses YouTube Data API v3 (free) for channel operations.

Features:
- First-time OAuth2 setup (opens browser once, then remembers)
- Channel info display
- Playlist management
- Channel branding/description updates
- Analytics overview
"""

import json
import logging
import pickle
import webbrowser
from pathlib import Path
from datetime import datetime

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
TOKEN_FILE = BASE_DIR / "token.pickle"
CLIENT_SECRETS_FILE = BASE_DIR / "client_secrets.json"

# Extended scopes for channel management
MANAGEMENT_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def setup_oauth(force_new: bool = False):
    """
    Complete OAuth2 setup flow. Opens browser for Google sign-in.
    Only needed once — token is saved and reused.
    
    Returns authenticated YouTube service.
    """
    from config import YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET

    credentials = None

    if not force_new and TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as f:
            credentials = pickle.load(f)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            # Create client_secrets.json if needed
            if not CLIENT_SECRETS_FILE.exists():
                if not YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_ID == "your_youtube_client_id_here":
                    print("\n" + "="*60)
                    print("🔧 YOUTUBE SETUP REQUIRED")
                    print("="*60)
                    print("\n1. Opening Google Cloud Console...")
                    print("2. Create a project → Enable YouTube Data API v3")
                    print("3. Create OAuth 2.0 credentials (Desktop app)")
                    print("4. Copy Client ID & Secret to .env file")
                    print("\nOpening browser...\n")
                    webbrowser.open("https://console.cloud.google.com/apis/library/youtube.googleapis.com")
                    raise ValueError(
                        "Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in .env first"
                    )

                secrets = {
                    "installed": {
                        "client_id": YOUTUBE_CLIENT_ID,
                        "client_secret": YOUTUBE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"],
                    }
                }
                with open(CLIENT_SECRETS_FILE, "w") as f:
                    json.dump(secrets, f, indent=2)

            print("\n🔐 Opening browser for Google sign-in...")
            print("   (Authorize the app to access your YouTube channel)\n")

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), MANAGEMENT_SCOPES
            )
            credentials = flow.run_local_server(port=8080, prompt="consent")

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)
        print("✅ Token saved! You won't need to sign in again.\n")

    return build("youtube", "v3", credentials=credentials)


def get_channel_info(youtube=None) -> dict:
    """Get current channel information."""
    if youtube is None:
        youtube = setup_oauth()

    response = youtube.channels().list(
        part="snippet,statistics,brandingSettings,contentDetails",
        mine=True,
    ).execute()

    if not response.get("items"):
        return {"error": "No channel found for this account"}

    channel = response["items"][0]
    info = {
        "id": channel["id"],
        "title": channel["snippet"]["title"],
        "description": channel["snippet"].get("description", ""),
        "subscribers": channel["statistics"].get("subscriberCount", "0"),
        "views": channel["statistics"].get("viewCount", "0"),
        "videos": channel["statistics"].get("videoCount", "0"),
        "url": f"https://www.youtube.com/channel/{channel['id']}",
        "uploads_playlist": channel["contentDetails"]["relatedPlaylists"]["uploads"],
    }
    return info


def update_channel_branding(
    youtube=None,
    title: str = None,
    description: str = None,
    keywords: str = None,
    default_language: str = "en",
) -> bool:
    """Update channel title, description, and keywords."""
    if youtube is None:
        youtube = setup_oauth()

    # Get current channel
    response = youtube.channels().list(
        part="brandingSettings,snippet",
        mine=True,
    ).execute()

    if not response.get("items"):
        logger.error("No channel found")
        return False

    channel = response["items"][0]
    channel_id = channel["id"]

    # Build update body
    body = {
        "id": channel_id,
        "brandingSettings": channel.get("brandingSettings", {}),
    }

    if title:
        body["brandingSettings"]["channel"]["title"] = title
    if description:
        body["brandingSettings"]["channel"]["description"] = description
    if keywords:
        body["brandingSettings"]["channel"]["keywords"] = keywords
    if default_language:
        body["brandingSettings"]["channel"]["defaultLanguage"] = default_language

    youtube.channels().update(
        part="brandingSettings",
        body=body,
    ).execute()

    logger.info(f"✅ Channel branding updated")
    return True


def create_playlist(
    youtube=None,
    title: str = "Daily Current Affairs",
    description: str = "Daily news roundup videos",
    privacy: str = "public",
) -> str:
    """Create a playlist for organizing daily videos."""
    if youtube is None:
        youtube = setup_oauth()

    body = {
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": privacy,
        },
    }

    response = youtube.playlists().insert(
        part="snippet,status",
        body=body,
    ).execute()

    playlist_id = response["id"]
    logger.info(f"✅ Playlist created: {title} (ID: {playlist_id})")
    return playlist_id


def add_video_to_playlist(youtube=None, playlist_id: str = None, video_id: str = None) -> bool:
    """Add an uploaded video to a playlist."""
    if youtube is None:
        youtube = setup_oauth()

    body = {
        "snippet": {
            "playlistId": playlist_id,
            "resourceId": {
                "kind": "youtube#video",
                "videoId": video_id,
            },
        },
    }

    youtube.playlistItems().insert(
        part="snippet",
        body=body,
    ).execute()

    logger.info(f"✅ Video {video_id} added to playlist {playlist_id}")
    return True


def list_recent_videos(youtube=None, max_results: int = 10) -> list[dict]:
    """List recent uploads on the channel."""
    if youtube is None:
        youtube = setup_oauth()

    info = get_channel_info(youtube)
    uploads_id = info.get("uploads_playlist")
    if not uploads_id:
        return []

    response = youtube.playlistItems().list(
        part="snippet,status",
        playlistId=uploads_id,
        maxResults=max_results,
    ).execute()

    videos = []
    for item in response.get("items", []):
        videos.append({
            "title": item["snippet"]["title"],
            "video_id": item["snippet"]["resourceId"]["videoId"],
            "url": f"https://youtu.be/{item['snippet']['resourceId']['videoId']}",
            "published": item["snippet"]["publishedAt"],
            "status": item.get("status", {}).get("privacyStatus", "unknown"),
        })

    return videos


def get_video_analytics(youtube=None, video_id: str = None) -> dict:
    """Get basic video statistics."""
    if youtube is None:
        youtube = setup_oauth()

    response = youtube.videos().list(
        part="statistics,snippet",
        id=video_id,
    ).execute()

    if not response.get("items"):
        return {}

    video = response["items"][0]
    stats = video.get("statistics", {})
    return {
        "title": video["snippet"]["title"],
        "views": stats.get("viewCount", "0"),
        "likes": stats.get("likeCount", "0"),
        "comments": stats.get("commentCount", "0"),
    }


# ── Interactive Channel Setup ────────────────────────────────

def interactive_setup():
    """
    Interactive channel setup wizard — run once to configure everything.
    Opens browser for OAuth and sets up channel branding.
    """
    print("\n" + "="*60)
    print("📺 YOUTUBE CHANNEL SETUP WIZARD")
    print("="*60)
    print("\nThis will:")
    print("  1. Authenticate with your Google/YouTube account")
    print("  2. Display your channel info")
    print("  3. Optionally update channel branding")
    print("  4. Create a playlist for daily uploads")
    print()

    # Step 1: Authenticate
    print("🔐 Step 1: Authenticating...")
    try:
        youtube = setup_oauth()
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return

    # Step 2: Show channel info
    print("\n📊 Step 2: Your Channel Info:")
    info = get_channel_info(youtube)
    if "error" in info:
        print(f"  ❌ {info['error']}")
        return

    print(f"  📺 Channel: {info['title']}")
    print(f"  👥 Subscribers: {info['subscribers']}")
    print(f"  👁️ Total Views: {info['views']}")
    print(f"  🎬 Videos: {info['videos']}")
    print(f"  🔗 URL: {info['url']}")

    # Step 3: Update branding
    print("\n🎨 Step 3: Channel Branding")
    from config import CHANNEL_NAME, CHANNEL_TAGLINE, DEFAULT_TAGS

    update = input(f"  Update channel name to '{CHANNEL_NAME}'? (y/n): ").strip().lower()
    if update == "y":
        description = (
            f"{CHANNEL_TAGLINE}\n\n"
            "📰 Get your daily dose of current affairs in just 5 minutes!\n"
            "📺 New video every day at 9:00 AM IST\n\n"
            "Topics: India News, World News, Economy, Politics, Science, Sports\n\n"
            "👍 Like | 🔔 Subscribe | 💬 Comment\n\n"
            "#CurrentAffairs #DailyNews #India"
        )
        keywords = " ".join(DEFAULT_TAGS)
        
        update_channel_branding(
            youtube, title=CHANNEL_NAME,
            description=description, keywords=keywords,
        )
        print("  ✅ Channel branding updated!")

    # Step 4: Create playlist
    print("\n📋 Step 4: Playlist Setup")
    create_pl = input("  Create 'Daily Current Affairs' playlist? (y/n): ").strip().lower()
    if create_pl == "y":
        from datetime import datetime
        month = datetime.now().strftime("%B %Y")
        playlist_id = create_playlist(
            youtube,
            title=f"Daily Current Affairs - {month}",
            description=f"Daily current affairs updates for {month}",
        )
        print(f"  ✅ Playlist created: {playlist_id}")

    # Show recent videos
    print("\n🎬 Recent Videos:")
    videos = list_recent_videos(youtube, max_results=5)
    if videos:
        for v in videos:
            print(f"  • {v['title']} ({v['status']}) — {v['url']}")
    else:
        print("  No videos yet. Run `python main.py` to create your first!")

    print(f"\n{'='*60}")
    print("✅ SETUP COMPLETE! You're ready to run the pipeline.")
    print(f"{'='*60}\n")


# ── Test / Run ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    interactive_setup()
