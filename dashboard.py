"""
Platform Dashboard — FastAPI Backend
Manages channel, pipeline, videos, analytics, and system health.
Run: python dashboard.py
"""

import json
import logging
import os
import sys
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

# --- PILLOW COMPATIBILITY MONKEY-PATCH ---
# Fixes 'module PIL.Image has no attribute ANTIALIAS' in MoviePy on Pillow 10+
try:
    import PIL.Image
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
except ImportError:
    pass
# -----------------------------------------

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_SCHEDULER = True
except ImportError:
    HAS_SCHEDULER = False

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dashboard")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
ENV_FILE = BASE_DIR / ".env"

app = FastAPI(title="YouTube Current Affairs Platform", version="2.0")

scheduler_state = {
    "enabled": False,
    "schedule_time": "06:00",
    "dry_run": False,
    "last_run": None,
    "next_run": None,
    "history": [],
}

_scheduler = None
SCHEDULE_FILE = BASE_DIR / "schedule_config.json"

# ── State ────────────────────────────────────────────────────
pipeline_state = {
    "status": "idle",          # idle, running, completed, failed
    "current_step": 0,
    "total_steps": 8,
    "step_name": "",
    "started_at": None,
    "completed_at": None,
    "log": [],
    "results": {},
    "error": None,
}


# ── Pydantic Models ─────────────────────────────────────────
class EnvUpdate(BaseModel):
    gemini_api_key: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    whatsapp_phone: str = ""
    whatsapp_api_key: str = ""

class BrandingUpdate(BaseModel):
    title: str = ""
    description: str = ""
    keywords: str = ""

class PipelineRequest(BaseModel):
    dry_run: bool = True
    start_step: int = 1
    end_step: int = 8

class ContentSuggestion(BaseModel):
    topic: str = "India"

class ScheduleRequest(BaseModel):
    enabled: bool = True
    time: str = "06:00"
    dry_run: bool = False


# ── API Key Management ──────────────────────────────────────
@app.get("/api/keys/status")
def get_keys_status():
    """Check which API keys are configured."""
    env = _load_env()
    placeholders = ["", "your_gemini_api_key_here", "your_youtube_client_id_here",
                     "your_youtube_client_secret_here", "your_telegram_bot_token_here",
                     "your_telegram_chat_id_here", "your_whatsapp_phone_here",
                     "your_whatsapp_api_key_here"]
    return {
        "gemini": env.get("GEMINI_API_KEY", "") not in placeholders,
        "youtube_id": env.get("YOUTUBE_CLIENT_ID", "") not in placeholders,
        "youtube_secret": env.get("YOUTUBE_CLIENT_SECRET", "") not in placeholders,
        "telegram_token": env.get("TELEGRAM_BOT_TOKEN", "") not in placeholders,
        "telegram_chat": env.get("TELEGRAM_CHAT_ID", "") not in placeholders,
        "whatsapp_phone": env.get("WHATSAPP_PHONE", "") not in placeholders,
        "whatsapp_key": env.get("WHATSAPP_API_KEY", "") not in placeholders,
        "all_set": all(
            env.get(k, "") not in placeholders
            for k in ["GEMINI_API_KEY", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET",
                       "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
        ),
    }

@app.post("/api/keys/save")
def save_keys(data: EnvUpdate):
    """Save API keys to .env file."""
    env = _load_env()
    if data.gemini_api_key: env["GEMINI_API_KEY"] = data.gemini_api_key
    if data.youtube_client_id: env["YOUTUBE_CLIENT_ID"] = data.youtube_client_id
    if data.youtube_client_secret: env["YOUTUBE_CLIENT_SECRET"] = data.youtube_client_secret
    if data.telegram_bot_token: env["TELEGRAM_BOT_TOKEN"] = data.telegram_bot_token
    if data.telegram_chat_id: env["TELEGRAM_CHAT_ID"] = data.telegram_chat_id
    if data.whatsapp_phone: env["WHATSAPP_PHONE"] = data.whatsapp_phone
    if data.whatsapp_api_key: env["WHATSAPP_API_KEY"] = data.whatsapp_api_key
    _save_env(env)
    return {"status": "saved", "keys": get_keys_status()}

@app.get("/api/keys/urls")
def get_key_urls():
    """Get signup URLs for all free API keys."""
    return {
        "gemini": {"url": "https://aistudio.google.com/apikey", "label": "Google Gemini (Free)"},
        "youtube": {"url": "https://console.cloud.google.com/apis/library/youtube.googleapis.com", "label": "YouTube Data API v3 (Free)"},
        "telegram": {"url": "https://t.me/BotFather", "label": "Telegram Bot (Free)"},
        "telegram_id": {"url": "https://t.me/userinfobot", "label": "Get Telegram Chat ID"},
    }


# ── Channel Management ──────────────────────────────────────
@app.get("/api/channel/info")
def get_channel_info():
    """Get YouTube channel information."""
    try:
        from modules.channel_manager import get_channel_info as _get_info, setup_oauth
        youtube = setup_oauth()
        info = _get_info(youtube)
        return {"status": "ok", "channel": info}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/channel/branding")
def update_branding(data: BrandingUpdate):
    """Update channel branding."""
    try:
        from modules.channel_manager import update_channel_branding, setup_oauth
        youtube = setup_oauth()
        update_channel_branding(youtube, title=data.title or None,
                                description=data.description or None,
                                keywords=data.keywords or None)
        return {"status": "ok", "message": "Branding updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/channel/create-playlist")
def create_playlist():
    """Create a monthly playlist."""
    try:
        from modules.channel_manager import create_playlist as _create, setup_oauth
        youtube = setup_oauth()
        month = datetime.now().strftime("%B %Y")
        pid = _create(youtube, title=f"Daily Current Affairs - {month}",
                      description=f"Daily news roundup for {month}")
        return {"status": "ok", "playlist_id": pid}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/channel/videos")
def list_videos():
    """List recent channel videos."""
    try:
        from modules.channel_manager import list_recent_videos, setup_oauth
        youtube = setup_oauth()
        videos = list_recent_videos(youtube, max_results=20)
        return {"status": "ok", "videos": videos}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/channel/video/{video_id}/stats")
def video_stats(video_id: str):
    """Get video statistics."""
    try:
        from modules.channel_manager import get_video_analytics, setup_oauth
        youtube = setup_oauth()
        stats = get_video_analytics(youtube, video_id=video_id)
        return {"status": "ok", "stats": stats}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Pipeline Control ─────────────────────────────────────────
@app.get("/api/pipeline/status")
def get_pipeline_status():
    """Get current pipeline execution status."""
    return pipeline_state

@app.post("/api/pipeline/run")
def run_pipeline(req: PipelineRequest, bg: BackgroundTasks):
    """Start the pipeline in background."""
    if pipeline_state["status"] == "running":
        raise HTTPException(400, "Pipeline is already running")
    bg.add_task(_run_pipeline_bg, req.dry_run, req.start_step, req.end_step)
    return {"status": "started", "dry_run": req.dry_run}

@app.post("/api/pipeline/stop")
def stop_pipeline():
    """Request pipeline stop."""
    pipeline_state["status"] = "stopping"
    return {"status": "stopping"}


# ── News Preview ─────────────────────────────────────────────
@app.get("/api/news/preview")
def preview_news():
    """Fetch latest news without running full pipeline."""
    try:
        from modules.news_fetcher import fetch_news
        articles = fetch_news(max_articles=10)
        return {"status": "ok", "articles": articles, "count": len(articles)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Output Files ─────────────────────────────────────────────
@app.get("/api/outputs")
def list_outputs():
    """List all output directories (one per day)."""
    dirs = []
    if OUTPUT_DIR.exists():
        for d in sorted(OUTPUT_DIR.iterdir(), reverse=True):
            if d.is_dir() and d.name != "__pycache__":
                files = [{"name": f.name, "size_kb": round(f.stat().st_size / 1024, 1)}
                         for f in d.iterdir() if f.is_file()]
                dirs.append({"date": d.name, "files": files, "file_count": len(files)})
    return {"outputs": dirs}

@app.get("/api/outputs/{date}/{filename}")
def get_output_file(date: str, filename: str):
    """Serve an output file (video, thumbnail, etc)."""
    fp = OUTPUT_DIR / date / filename
    if not fp.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(fp)

@app.post("/api/outputs/{date}/upload")
def upload_manual(date: str, bg: BackgroundTasks):
    """Manually trigger upload for a specific date's output."""
    target_dir = OUTPUT_DIR / date
    if not (target_dir / "final_video.mp4").exists():
        raise HTTPException(404, "Video file not found for this date")
    
    bg.add_task(_upload_manual_bg, date)
    return {"status": "started", "message": f"Upload for {date} started"}

def _upload_manual_bg(date_str: str):
    """Background task for manual upload."""
    from modules.uploader import upload_video
    import json
    
    target_dir = OUTPUT_DIR / date_str
    video_path = target_dir / "final_video.mp4"
    script_path = target_dir / "script_data.json"
    thumb_path = target_dir / "thumbnail.png"
    
    try:
        pipeline_state["status"] = "running"
        pipeline_state["current_step"] = 6
        pipeline_state["step_name"] = f"Manual Upload ({date_str})"
        _log(f"🚀 Starting manual upload for {date_str}...")
        
        if not script_path.exists():
            _log("❌ Metadata missing, using defaults")
            title = f"Current Affairs Update - {date_str}"
            desc = "Daily news update."
            tags = ["news"]
        else:
            with open(script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                title = data.get("title", f"News - {date_str}")
                desc = data.get("description", "")
                tags = data.get("tags", [])

        # Call uploader
        result = upload_video(
            video_path=video_path,
            title=title,
            description=desc,
            tags=tags,
            thumbnail_path=thumb_path if thumb_path.exists() else None
        )
        
        if result and "id" in result:
            url = f"https://youtu.be/{result['id']}"
            pipeline_state["youtube_url"] = url
            _log(f"✅ MANUAL UPLOAD SUCCESS: {url}")
            
            # Try notified if keys exist
            try:
                from modules.notifier import send_notification
                send_notification(title=title, youtube_url=url, status="ready")
            except:
                pass
        
        pipeline_state["status"] = "completed"
    except Exception as e:
        _log(f"❌ Manual upload failed: {str(e)}")
        pipeline_state["status"] = "failed"


# ── System Health ────────────────────────────────────────────
@app.get("/api/system/health")
def system_health():
    """Check system dependencies and health."""
    checks = {}
    # FFmpeg
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        checks["ffmpeg"] = {"ok": r.returncode == 0, "version": r.stdout.split("\n")[0][:60] if r.returncode == 0 else "Not found"}
    except Exception:
        checks["ffmpeg"] = {"ok": False, "version": "Not installed"}

    # Python modules
    for mod in ["feedparser", "edge_tts", "PIL", "moviepy", "google.generativeai"]:
        try:
            __import__(mod)
            checks[mod] = {"ok": True}
        except ImportError:
            checks[mod] = {"ok": False}

    # Disk usage
    import shutil
    total, used, free = shutil.disk_usage(str(BASE_DIR))
    checks["disk"] = {
        "total_gb": round(total / (1024**3), 1),
        "free_gb": round(free / (1024**3), 1),
    }

    # Output size
    out_size = sum(f.stat().st_size for f in OUTPUT_DIR.rglob("*") if f.is_file()) if OUTPUT_DIR.exists() else 0
    checks["output_size_mb"] = round(out_size / (1024**2), 1)

    return checks


# ── AI Content Suggestions (Innovative) ──────────────────────
@app.post("/api/ai/suggest-topics")
def suggest_topics(req: ContentSuggestion):
    """Use Gemini to suggest trending topics and titles."""
    try:
        from config import GEMINI_API_KEY
        import google.generativeai as genai
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            return {"status": "error", "message": "Gemini API key not set"}
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        prompt = (
            f"Suggest 5 trending current affairs topics for a YouTube video about {req.topic} today "
            f"({datetime.now().strftime('%B %d, %Y')}). For each, provide:\n"
            "1. A catchy YouTube title (under 80 chars)\n"
            "2. Why it's trending\n"
            "3. Estimated viewer interest (high/medium/low)\n"
            "Return as JSON array with keys: title, reason, interest"
        )
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        if text.startswith("```"):
            lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
            text = "\n".join(lines)
        import re
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            suggestions = json.loads(match.group())
        else:
            suggestions = [{"title": text[:80], "reason": "AI response", "interest": "medium"}]
        return {"status": "ok", "suggestions": suggestions}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/ai/optimize-title/{video_id}")
def optimize_title(video_id: str):
    """Suggest optimized title for a video based on performance."""
    try:
        from config import GEMINI_API_KEY
        from modules.channel_manager import get_video_analytics, setup_oauth
        import google.generativeai as genai
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
            return {"status": "error", "message": "Gemini API key not set"}
        youtube = setup_oauth()
        stats = get_video_analytics(youtube, video_id=video_id)
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        prompt = (
            f"This YouTube video titled '{stats.get('title', '')}' has {stats.get('views', 0)} views, "
            f"{stats.get('likes', 0)} likes. Suggest 3 alternative SEO-optimized titles that could "
            "get more views. Return as JSON array of strings."
        )
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        if text.startswith("```"):
            lines = [l for l in text.split("\n") if not l.strip().startswith("```")]
            text = "\n".join(lines)
        import re
        match = re.search(r'\[[\s\S]*\]', text)
        titles = json.loads(match.group()) if match else [text]
        return {"status": "ok", "current": stats.get("title"), "suggestions": titles}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ── Scheduler / Automation ────────────────────────────────────

def _load_schedule_config():
    if SCHEDULE_FILE.exists():
        try:
            data = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
            scheduler_state.update(data)
        except Exception:
            pass

def _save_schedule_config():
    data = {
        "enabled": scheduler_state["enabled"],
        "schedule_time": scheduler_state["schedule_time"],
        "dry_run": scheduler_state["dry_run"],
    }
    SCHEDULE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _scheduled_pipeline_run():
    now = datetime.now()
    scheduler_state["last_run"] = now.isoformat()
    scheduler_state["history"].append({
        "time": now.isoformat(),
        "status": "started",
    })
    if len(scheduler_state["history"]) > 50:
        scheduler_state["history"] = scheduler_state["history"][-50:]
    _run_pipeline_bg(scheduler_state["dry_run"], 1, 8)

def _start_scheduler():
    global _scheduler
    if not HAS_SCHEDULER:
        logger.warning("APScheduler not installed, scheduling disabled")
        return False
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
    _scheduler = BackgroundScheduler()
    t = scheduler_state["schedule_time"]
    parts = t.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    _scheduler.add_job(
        _scheduled_pipeline_run,
        CronTrigger(hour=hour, minute=minute),
        id="daily_pipeline",
        replace_existing=True,
    )
    _scheduler.start()
    job = _scheduler.get_job("daily_pipeline")
    if job and job.next_run_time:
        scheduler_state["next_run"] = job.next_run_time.isoformat()
    logger.info(f"Scheduler started: daily at {t}")
    return True

def _stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    scheduler_state["next_run"] = None

@app.get("/api/schedule/status")
def get_schedule_status():
    return scheduler_state

@app.post("/api/schedule/set")
def set_schedule(req: ScheduleRequest):
    scheduler_state["enabled"] = req.enabled
    scheduler_state["schedule_time"] = req.time
    scheduler_state["dry_run"] = req.dry_run
    _save_schedule_config()
    if req.enabled:
        ok = _start_scheduler()
        if not ok:
            return {"status": "error", "message": "APScheduler not installed. Run: pip install apscheduler"}
        return {"status": "ok", "message": f"Scheduled daily at {req.time}", "next_run": scheduler_state.get("next_run")}
    else:
        _stop_scheduler()
        return {"status": "ok", "message": "Scheduler disabled"}

@app.post("/api/schedule/run-now")
def run_now(bg: BackgroundTasks):
    if pipeline_state["status"] == "running":
        raise HTTPException(400, "Pipeline is already running")
    bg.add_task(_scheduled_pipeline_run)
    return {"status": "started", "message": "Pipeline triggered manually"}


# ── YouTube OAuth Diagnostics ─────────────────────────────────

@app.get("/api/youtube/auth-status")
def youtube_auth_status():
    token_file = BASE_DIR / "token.pickle"
    client_secrets = BASE_DIR / "client_secrets.json"
    env = _load_env()
    client_id = env.get("YOUTUBE_CLIENT_ID", "")
    client_secret = env.get("YOUTUBE_CLIENT_SECRET", "")
    placeholders = ["", "your_youtube_client_id_here", "your_youtube_client_secret_here"]

    has_credentials = client_id not in placeholders and client_secret not in placeholders
    has_token = token_file.exists()
    has_client_secrets = client_secrets.exists()
    token_valid = False
    token_expired = False
    token_error = None

    if has_token:
        try:
            import pickle
            with open(token_file, "rb") as f:
                creds = pickle.load(f)
            token_valid = creds.valid if hasattr(creds, 'valid') else False
            token_expired = creds.expired if hasattr(creds, 'expired') else False
            has_refresh = bool(creds.refresh_token) if hasattr(creds, 'refresh_token') else False
            if not token_valid and token_expired and has_refresh:
                try:
                    from google.auth.transport.requests import Request
                    creds.refresh(Request())
                    token_valid = True
                    with open(token_file, "wb") as f:
                        pickle.dump(creds, f)
                except Exception as e:
                    token_error = str(e)
        except Exception as e:
            token_error = str(e)

    return {
        "has_credentials": has_credentials,
        "has_token": has_token,
        "has_client_secrets": has_client_secrets,
        "token_valid": token_valid,
        "token_expired": token_expired,
        "token_error": token_error,
        "ready": has_credentials and has_token and token_valid,
    }

@app.post("/api/youtube/generate-auth-url")
def generate_auth_url():
    env = _load_env()
    client_id = env.get("YOUTUBE_CLIENT_ID", "")
    client_secret = env.get("YOUTUBE_CLIENT_SECRET", "")
    if not client_id or client_id == "your_youtube_client_id_here":
        return {"status": "error", "message": "YouTube Client ID not set. Add it in API Keys first."}

    client_secrets_file = BASE_DIR / "client_secrets.json"
    secrets = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"]
        }
    }
    with open(client_secrets_file, "w") as f:
        json.dump(secrets, f, indent=2)

    scopes = [
        "https://www.googleapis.com/auth/youtube",
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]
    from urllib.parse import urlencode
    params = {
        "client_id": client_id,
        "redirect_uri": "http://localhost",
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    return {
        "status": "ok",
        "auth_url": auth_url,
        "message": "Open this URL in your browser to authorize. After authorizing, you will be redirected to localhost with a code parameter.",
    }

@app.post("/api/youtube/exchange-code")
def exchange_code(data: dict):
    code = data.get("code", "").strip()
    if not code:
        return {"status": "error", "message": "No authorization code provided"}

    env = _load_env()
    client_id = env.get("YOUTUBE_CLIENT_ID", "")
    client_secret = env.get("YOUTUBE_CLIENT_SECRET", "")

    try:
        import requests as req
        resp = req.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": "http://localhost",
            "grant_type": "authorization_code",
        }, timeout=30)
        token_data = resp.json()

        if "error" in token_data:
            return {"status": "error", "message": f"{token_data.get('error')}: {token_data.get('error_description', '')}"}

        from google.oauth2.credentials import Credentials
        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=token_data.get("scope", "").split(" "),
        )
        import pickle
        token_file = BASE_DIR / "token.pickle"
        with open(token_file, "wb") as f:
            pickle.dump(creds, f)

        return {"status": "ok", "message": "YouTube authorized successfully! Token saved."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/youtube/reset-token")
def reset_youtube_token():
    token_file = BASE_DIR / "token.pickle"
    if token_file.exists():
        token_file.unlink()
    return {"status": "ok", "message": "Token removed. You will need to re-authorize."}


# ── Helpers ──────────────────────────────────────────────────
def _load_env() -> dict:
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                values[k.strip()] = v.strip()
    return values

def _save_env(values: dict):
    lines = [
        "# Auto-generated by YouTube Current Affairs Platform",
        f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"GEMINI_API_KEY={values.get('GEMINI_API_KEY', '')}",
        f"YOUTUBE_CLIENT_ID={values.get('YOUTUBE_CLIENT_ID', '')}",
        f"YOUTUBE_CLIENT_SECRET={values.get('YOUTUBE_CLIENT_SECRET', '')}",
        f"TELEGRAM_BOT_TOKEN={values.get('TELEGRAM_BOT_TOKEN', '')}",
        f"TELEGRAM_CHAT_ID={values.get('TELEGRAM_CHAT_ID', '')}",
        f"WHATSAPP_PHONE={values.get('WHATSAPP_PHONE', '')}",
        f"WHATSAPP_API_KEY={values.get('WHATSAPP_API_KEY', '')}",
        "",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")

def _log(msg: str):
    pipeline_state["log"].append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})
    logger.info(msg)

def _run_pipeline_bg(dry_run: bool, start: int, end: int):
    """Run pipeline in background thread."""
    global pipeline_state
    pipeline_state.update({
        "status": "running", "current_step": start, "started_at": datetime.now().isoformat(),
        "completed_at": None, "log": [], "results": {}, "error": None,
    })
    step_names = {1:"Fetching News", 2:"Writing Script", 3:"Generating Voiceover",
                  4:"Building Video", 5:"Creating Thumbnail", 6:"Uploading to YouTube",
                  7:"Cross-posting", 8:"Sending Notifications"}
    # Reload .env so newly saved keys are picked up
    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)
        import importlib, config
        importlib.reload(config)
    except Exception:
        pass
    try:
        from main import run_pipeline
        # Capture step progress by overriding logger
        class StepHandler(logging.Handler):
            def emit(self, record):
                msg = record.getMessage()
                pipeline_state["log"].append({"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})
                for s, name in step_names.items():
                    if f"STEP {s}" in msg:
                        pipeline_state["current_step"] = s
                        pipeline_state["step_name"] = name
        handler = StepHandler()
        logging.getLogger("pipeline").addHandler(handler)
        
        success = run_pipeline(dry_run=dry_run, step_range=(start, end))
        pipeline_state["status"] = "completed" if success else "failed"
        pipeline_state["completed_at"] = datetime.now().isoformat()
        
        # Load results
        from config import get_today_output_dir
        results_file = get_today_output_dir() / "pipeline_results.json"
        if results_file.exists():
            pipeline_state["results"] = json.loads(results_file.read_text(encoding="utf-8"))
        
        logging.getLogger("pipeline").removeHandler(handler)
    except Exception as e:
        pipeline_state["status"] = "failed"
        pipeline_state["error"] = str(e)
        pipeline_state["completed_at"] = datetime.now().isoformat()


# ── Serve Dashboard UI ───────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def dashboard_page():
    """Serve the dashboard HTML."""
    html_path = BASE_DIR / "templates" / "dashboard.html"
    if html_path.exists():
        return HTMLResponse(html_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Dashboard HTML not found. Create templates/dashboard.html</h1>")


@app.on_event("startup")
def on_startup():
    _load_schedule_config()
    if scheduler_state["enabled"] and HAS_SCHEDULER:
        _start_scheduler()
        logger.info(f"Auto-started scheduler: daily at {scheduler_state['schedule_time']}")


if __name__ == "__main__":
    import uvicorn
    import socket

    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    port = 8000
    if is_port_in_use(port):
        print("\n" + "!" * 60)
        print(f"  ERROR: Port {port} is already in use!")
        print(f"  A version of the dashboard might already be running.")
        print("!" * 60 + "\n")
        port = 8001
        print(f"  Attempting to start on fallback port: {port}...")

    print("\n" + "=" * 60)
    print("  YouTube Current Affairs Platform")
    print(f"  Dashboard: http://localhost:{port}")
    print(f"  API Docs:  http://localhost:{port}/docs")
    print("=" * 60 + "\n")

    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        print(f"\n Could not start server: {e}")
