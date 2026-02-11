# 🎬 YouTube Current Affairs — Automated Channel Platform

> Fully automated YouTube channel that publishes daily current affairs videos — **100% FREE**, no paid APIs or subscriptions.

---

## ✨ What It Does

Every day, this platform automatically:

1. **Fetches** top news headlines from Google News (free RSS)
2. **Writes** an AI-powered video script using Google Gemini (free tier)
3. **Generates** professional voiceover using edge-tts (free, unlimited)
4. **Creates** video with animated visuals using MoviePy + Pillow (free)
5. **Designs** an eye-catching thumbnail (free, automated)
6. **Uploads** to YouTube via YouTube Data API v3 (free, 10K quota/day)
7. **Cross-posts** to Telegram and WhatsApp (free, unlimited)
8. **Notifies** you when the video is live

---

## 🖥️ Dashboard

A premium dark-themed web dashboard to manage everything:

| Page | Features |
|---|---|
| **Dashboard** | Overview stats, quick actions, setup checklist |
| **Setup Guide** | Step-by-step wizard with instructions for each API key |
| **Pipeline** | Run/stop pipeline, live progress bar, step-by-step log |
| **News Preview** | Live Google News headlines |
| **Channel** | Channel info, branding, playlists |
| **Videos** | Monitor all uploads with status |
| **Analytics** | Channel growth and stats |
| **AI Suggestions** | Gemini-powered trending topics & title ideas |
| **Output Files** | Browse generated videos, thumbnails, scripts |
| **API Keys** | Configure all keys with signup links |
| **System Health** | FFmpeg, modules, disk diagnostics |

---

## 🚀 Quick Start (5 minutes)

### 1. Clone / Download
```bash
cd d:\youtube_free_current_affirs
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install FFmpeg
```bash
winget install FFmpeg
```

### 4. Launch Dashboard
```bash
python dashboard.py
```
Open **http://localhost:8000** in your browser.

### 5. Set Up API Keys
Go to the **Setup Guide** page in the dashboard and follow all 5 steps —
each step has detailed instructions and direct links to the signup pages.

### 6. Run Your First Video!
Click **"Dry Run"** on the dashboard to test locally, then **"Full Pipeline"** to upload.

---

## 💰 Cost: $0.00 / month

| Service | Free Limit | Daily Usage | Cost |
|---|---|---|---|
| Google News RSS | Unlimited | ~20 requests | **FREE** |
| Google Gemini API | 15 req/min, 1M tokens/day | 1 request | **FREE** |
| edge-tts (Microsoft) | Unlimited | 1 generation | **FREE** |
| Pillow + MoviePy | Unlimited | 1 video | **FREE** |
| YouTube Data API v3 | 10,000 units/day | ~3,200 units | **FREE** |
| Telegram Bot API | Unlimited | ~3 messages | **FREE** |
| WhatsApp (CallMeBot) | Unlimited | ~3 messages | **FREE** |
| **TOTAL** | | | **$0.00** |

---

## 📁 Project Structure

```
youtube_free_current_affirs/
├── dashboard.py          # FastAPI backend (18+ API endpoints)
├── run_pipeline.py       # Main pipeline orchestrator
├── config.py             # Centralized configuration
├── setup_keys.py         # Interactive API key setup helper
├── test_pipeline.py      # Tests for all modules
├── requirements.txt      # Python dependencies
├── .env.template         # API key template
├── .env                  # Your actual keys (git-ignored)
│
├── modules/
│   ├── news_fetcher.py       # Google News RSS scraper
│   ├── script_writer.py      # Gemini AI script generator
│   ├── voiceover.py          # edge-tts neural voices
│   ├── video_builder.py      # MoviePy video compositor
│   ├── thumbnail_gen.py      # Pillow thumbnail creator
│   ├── uploader.py           # YouTube Data API uploader
│   ├── cross_poster.py       # Telegram auto-poster
│   ├── whatsapp_notifier.py  # WhatsApp via CallMeBot
│   └── notifier.py           # Notification coordinator
│
├── templates/
│   └── dashboard.html    # Premium dark-themed UI
│
├── assets/
│   └── fonts/            # Custom fonts for thumbnails
│
└── output/               # Generated videos (by date)
    └── 2026-02-11/
        ├── script.json
        ├── voiceover.mp3
        ├── subtitles.srt
        ├── video.mp4
        └── thumbnail.png
```

---

## 🔑 API Keys (All FREE)

| # | Service | What It Does | Where to Get |
|---|---|---|---|
| 1 | **Gemini API** | AI script writing | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| 2 | **YouTube API v3** | Video upload & management | [Google Cloud Console](https://console.cloud.google.com/apis/library/youtube.googleapis.com) |
| 3 | **Telegram Bot** | Pipeline notifications | [@BotFather](https://t.me/BotFather) on Telegram |
| 4 | **WhatsApp** | Phone notifications | [CallMeBot](https://www.callmebot.com/blog/free-api-whatsapp-messages/) (optional) |

> **Detailed setup instructions** are built into the dashboard → **Setup Guide** page.

---

## ⚙️ API Endpoints

The dashboard runs a FastAPI server at `http://localhost:8000` with auto-generated docs at `/docs`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/keys/status` | Check configured API keys |
| POST | `/api/keys/save` | Save API keys to .env |
| GET | `/api/pipeline/status` | Pipeline execution status |
| POST | `/api/pipeline/run` | Start pipeline |
| POST | `/api/pipeline/stop` | Stop pipeline |
| GET | `/api/news/preview` | Fetch latest news |
| GET | `/api/channel/info` | YouTube channel info |
| POST | `/api/channel/branding` | Update channel branding |
| GET | `/api/channel/videos` | List channel videos |
| GET | `/api/system/health` | System health check |
| POST | `/api/ai/suggest-topics` | AI topic suggestions |
| GET | `/api/outputs` | Browse output files |

---

## 🕐 Schedule Daily Runs (Windows)

Use Windows Task Scheduler to run automatically every day:

```powershell
# Create a daily task at 6:00 AM
schtasks /create /tn "YouTubePipeline" /tr "python d:\youtube_free_current_affirs\run_pipeline.py" /sc daily /st 06:00
```

Or from the dashboard → **Pipeline** page → copy the schedule command.

---

## 🧪 Testing

```bash
python test_pipeline.py
```

Tests all 6 modules: news fetching, voiceover, thumbnail, video building, config, and voiceover generation.

---

## 📋 Requirements

- **Python** 3.9+
- **FFmpeg** (installed via `winget install FFmpeg`)
- **Windows** 10/11 (uses edge-tts which works on all platforms)
- **Internet** connection (for news fetching and API calls)

---

## 🤝 Tech Stack

| Technology | Purpose | License |
|---|---|---|
| FastAPI + Uvicorn | Dashboard backend | MIT |
| edge-tts | Neural text-to-speech | MIT |
| Pillow | Image/thumbnail generation | HPND |
| MoviePy | Video composition | MIT |
| feedparser | RSS news fetching | BSD |
| google-generativeai | Gemini AI scripts | Apache 2.0 |
| google-api-python-client | YouTube uploads | Apache 2.0 |
| python-dotenv | Environment management | BSD |

---

**Made with ❤️ — 100% free, fully automated, runs daily.**
