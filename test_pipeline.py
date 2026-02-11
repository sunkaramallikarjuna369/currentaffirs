"""Quick test — verifies core modules work."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

print("="*60)
print("Testing Automated YouTube Pipeline Modules")
print("="*60)

# Test 1: News Fetcher
print("\n1. Testing News Fetcher (Google News RSS)...")
try:
    from modules.news_fetcher import fetch_news
    articles = fetch_news(max_articles=5)
    print(f"   [OK] Fetched {len(articles)} articles")
    for i, a in enumerate(articles, 1):
        title = a['title'][:70]
        source = a.get('source', 'Unknown')
        print(f"   {i}. {title}... [{source}]")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 2: Voiceover (edge-tts)
print("\n2. Testing Voiceover (edge-tts)...")
try:
    from modules.voiceover import list_available_voices
    voices = list_available_voices("en-IN")
    print(f"   [OK] Found {len(voices)} Indian English voices:")
    for v in voices:
        print(f"      {v['name']} ({v['gender']})")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 3: Thumbnail generation
print("\n3. Testing Thumbnail Generator (Pillow)...")
try:
    from config import get_today_output_dir
    from modules.thumbnail import generate_thumbnail
    out = get_today_output_dir()
    path = generate_thumbnail("Top 8 Headlines Shaking India Today", out)
    size_kb = path.stat().st_size / 1024
    print(f"   [OK] Thumbnail saved: {path} ({size_kb:.0f} KB)")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 4: Video builder frames
print("\n4. Testing Video Frame Generator (Pillow)...")
try:
    from modules.video_builder import create_intro_frame, create_news_card, create_outro_frame
    out = get_today_output_dir()
    
    intro = create_intro_frame("Top 8 Headlines | India News", "February 11, 2026")
    intro.save(out / "test_intro.png")
    
    card = create_news_card(
        "India's Economy Shows Strong Growth at 7.2%",
        "The Indian economy demonstrated resilience with GDP growth reaching 7.2 percent.",
        1, 8
    )
    card.save(out / "test_card.png")
    
    outro = create_outro_frame()
    outro.save(out / "test_outro.png")
    
    print(f"   [OK] Test frames saved to {out}")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 5: Config
print("\n5. Testing Configuration...")
try:
    from config import (GEMINI_API_KEY, TELEGRAM_BOT_TOKEN,
                       YOUTUBE_CLIENT_ID, VIDEO_WIDTH, VIDEO_HEIGHT)
    print(f"   Video: {VIDEO_WIDTH}x{VIDEO_HEIGHT}")
    print(f"   Gemini Key: {'[SET]' if GEMINI_API_KEY and GEMINI_API_KEY != 'your_gemini_api_key_here' else '[NOT SET] (needed for Step 2)'}")
    print(f"   YouTube:    {'[SET]' if YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_ID != 'your_youtube_client_id_here' else '[NOT SET] (needed for Step 6)'}")
    print(f"   Telegram:   {'[SET]' if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != 'your_telegram_bot_token_here' else '[NOT SET] (needed for Step 8)'}")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

# Test 6: Voiceover generation (actual audio)
print("\n6. Testing Voiceover Generation (edge-tts)...")
try:
    from modules.voiceover import generate_voiceover
    out = get_today_output_dir()
    test_text = (
        "Good morning India! Welcome to your daily current affairs update. "
        "Today we bring you the top stories making headlines across the nation."
    )
    audio_path, sub_path = generate_voiceover(test_text, out, filename="test_voiceover.mp3")
    size_kb = audio_path.stat().st_size / 1024
    print(f"   [OK] Audio: {audio_path} ({size_kb:.0f} KB)")
    print(f"   [OK] Subtitles: {sub_path}")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

print("\n" + "="*60)
print("Test complete!")
print("Keys marked [NOT SET] need to be added to .env file.")
print("Run: python setup_keys.py  to get help with free keys")
print("="*60)
