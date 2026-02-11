# 🔧 Setup Guide — Free API Keys

All APIs used in this project are **100% free**. Here's how to get your keys.

## Prerequisites

1. **Python 3.10+** installed
2. **FFmpeg** installed and on PATH
   - Download: https://ffmpeg.org/download.html
   - Or via winget: `winget install FFmpeg`

## Step 1: Install Dependencies

```powershell
cd d:\youtube_free_current_affirs
pip install -r requirements.txt
```

## Step 2: Copy `.env.template` to `.env`

```powershell
copy .env.template .env
```

## Step 3: Get Free API Keys

### 🤖 Google Gemini API Key (Free: 15 RPM, 1M tokens/day)

1. Go to https://aistudio.google.com/apikey
2. Sign in with Google account
3. Click **"Create API Key"**
4. Copy the key → paste in `.env` as `GEMINI_API_KEY`

### 📺 YouTube Data API v3 (Free: 10,000 units/day)

1. Go to https://console.cloud.google.com
2. Create a new project (or select existing)
3. Go to **APIs & Services → Library**
4. Search "YouTube Data API v3" → **Enable**
5. Go to **APIs & Services → Credentials**
6. Click **+ CREATE CREDENTIALS → OAuth 2.0 Client ID**
7. Application type: **Desktop app**
8. Download the JSON → save as `client_secrets.json` in project root
   - OR copy Client ID & Secret → paste in `.env`
9. Go to **OAuth consent screen** → Add your email as test user

### 🔔 Telegram Bot (Free: Unlimited)

1. Open Telegram → search **@BotFather**
2. Send `/newbot` → follow prompts → get your **Bot Token**
3. Paste token in `.env` as `TELEGRAM_BOT_TOKEN`
4. To get your Chat ID:
   - Search **@userinfobot** → send `/start`
   - Copy your ID → paste in `.env` as `TELEGRAM_CHAT_ID`
5. **Start a chat with your bot** (important! Send it any message)

## Step 4: Test the Pipeline

```powershell
# Test news fetching (no API key needed)
python -c "from modules.news_fetcher import fetch_news; print(fetch_news(max_articles=3))"

# Test voiceover (no API key needed)
python -m modules.voiceover

# Full dry run (generates everything locally, no upload)
python main.py --dry-run

# Full pipeline with upload
python main.py
```

## Step 5: Schedule Daily Runs (Optional)

### Windows Task Scheduler

```powershell
# Create a scheduled task to run at 6:00 AM daily
schtasks /create /tn "YouTube_CurrentAffairs" /tr "python d:\youtube_free_current_affirs\main.py" /sc daily /st 06:00
```

## 💰 Cost Summary: $0

| Service | Free Limit | Our Usage |
|---|---|---|
| Google News RSS | Unlimited | ~20 requests/day |
| Gemini API | 15 RPM, 1M tokens/day | 1 request/day |
| edge-tts | Unlimited | 1 generation/day |
| YouTube Data API | 10,000 units/day | ~3,200 units/day |
| Telegram Bot API | Unlimited | ~3 messages/day |
