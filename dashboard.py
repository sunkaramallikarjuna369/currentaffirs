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
from datetime import datetime
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

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("dashboard")

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
ENV_FILE = BASE_DIR / ".env"

app = FastAPI(title="YouTube Current Affairs Platform", version="1.0")

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


# ── Schedule Info ────────────────────────────────────────────
@app.get("/api/schedule/info")
def schedule_info():
    """Get scheduling command for Windows Task Scheduler."""
    cmd = f'schtasks /create /tn "YouTube_CurrentAffairs" /tr "python {BASE_DIR / "main.py"}" /sc daily /st 06:00'
    check = subprocess.run(["schtasks", "/query", "/tn", "YouTube_CurrentAffairs"],
                           capture_output=True, text=True)
    return {
        "scheduled": check.returncode == 0,
        "command": cmd,
        "time": "06:00 AM daily",
    }


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
        "",
    ]
    ENV_FILE.write_text("\n".join(lines), encoding="utf-8")

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
        print(f"  To fix this on Windows, run:")
        print(f"    stop-process -id (get-netstat -localport {port}).owningprocess -force")
        print("!" * 60 + "\n")
        
        # Try fallback port
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
        print(f"\n❌ Could not start server: {e}")
