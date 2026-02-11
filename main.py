"""
🎬 Automated YouTube Current Affairs Channel — Main Orchestrator
================================================================
Runs the full pipeline: Fetch → Script → Voice → Video → Thumb → Upload → Post → Notify

Usage:
    python main.py                  # Full pipeline
    python main.py --dry-run        # No upload/post (local generation only)
    python main.py --step 1         # Run only step 1 (news fetching)
    python main.py --step 1-3       # Run steps 1 through 3

All Free APIs — $0 total cost.
"""

import argparse
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
import os

# --- PILLOW COMPATIBILITY MONKEY-PATCH ---
# Fixes 'module PIL.Image has no attribute ANTIALIAS' in MoviePy on Pillow 10+
try:
    import PIL.Image
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
except ImportError:
    pass
# -----------------------------------------

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("pipeline")


def run_pipeline(dry_run: bool = False, step_range: tuple = None):
    """
    Run the full automated pipeline.
    
    Args:
        dry_run: If True, skip upload/post/notify steps
        step_range: (start, end) tuple for running specific steps only
    """
    from config import get_today_output_dir

    start_step = step_range[0] if step_range else 1
    end_step = step_range[1] if step_range else 8

    output_dir = get_today_output_dir()
    logger.info(f"{'='*60}")
    logger.info(f"🎬 YouTube Current Affairs Pipeline")
    logger.info(f"📅 Date: {datetime.now().strftime('%B %d, %Y')}")
    logger.info(f"📂 Output: {output_dir}")
    logger.info(f"🔧 Mode: {'DRY RUN' if dry_run else 'FULL PIPELINE'}")
    logger.info(f"📋 Steps: {start_step} → {end_step}")
    logger.info(f"{'='*60}\n")

    results = {}
    articles = []
    script_data = {}
    voiceover_path = None
    video_path = None
    thumbnail_path = None
    short_path = None
    youtube_result = {}

    try:
        # ════════════════════════════════════════════════════
        # STEP 1: Fetch News (FREE — Google News RSS)
        # ════════════════════════════════════════════════════
        if start_step <= 1 <= end_step:
            logger.info("📰 STEP 1: Fetching news headlines...")
            from modules.news_fetcher import fetch_news

            articles = fetch_news()
            results["news_count"] = str(len(articles))
            
            # Save raw articles
            with open(output_dir / "raw_articles.json", "w", encoding="utf-8") as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Step 1 done: {len(articles)} articles fetched\n")

        # ════════════════════════════════════════════════════
        # STEP 2: Generate Script (FREE — Gemini API)
        # ════════════════════════════════════════════════════
        if start_step <= 2 <= end_step:
            logger.info("📝 STEP 2: Generating script with AI...")
            from modules.script_writer import generate_script, save_script

            # Load articles if not from step 1
            if not articles:
                raw_path = output_dir / "raw_articles.json"
                if raw_path.exists():
                    with open(raw_path, encoding="utf-8") as f:
                        articles = json.load(f)
                else:
                    raise ValueError("No articles found. Run step 1 first.")

            script_data = generate_script(articles)
            save_script(script_data, output_dir)
            results["story_count"] = str(len(script_data.get("stories", [])))
            
            logger.info(f"✅ Step 2 done: Script with {results['story_count']} stories\n")

        # ════════════════════════════════════════════════════
        # STEP 3: Generate Voiceover (FREE — edge-tts)
        # ════════════════════════════════════════════════════
        if start_step <= 3 <= end_step:
            logger.info("🎤 STEP 3: Generating voiceover...")
            from modules.voiceover import generate_voiceover

            # Load script if not from step 2
            if not script_data:
                script_path = output_dir / "script_data.json"
                if script_path.exists():
                    with open(script_path, encoding="utf-8") as f:
                        script_data = json.load(f)
                else:
                    raise ValueError("No script found. Run step 2 first.")

            full_script = script_data.get("full_script", "")
            if not full_script:
                raise ValueError("Script is empty!")

            voiceover_path, subtitle_path = generate_voiceover(full_script, output_dir)
            results["voiceover_status"] = "✅ Done"
            
            logger.info(f"✅ Step 3 done: Voiceover at {voiceover_path}\n")

        # ════════════════════════════════════════════════════
        # STEP 4: Build Video (FREE — Pillow + MoviePy)
        # ════════════════════════════════════════════════════
        if start_step <= 4 <= end_step:
            logger.info("🎬 STEP 4: Building video...")
            from modules.video_builder import build_video

            # Load dependencies
            if not script_data:
                with open(output_dir / "script_data.json", encoding="utf-8") as f:
                    script_data = json.load(f)
            if not voiceover_path:
                voiceover_path = output_dir / "voiceover.mp3"
                if not voiceover_path.exists():
                    raise ValueError("No voiceover found. Run step 3 first.")

            video_path = build_video(script_data, voiceover_path, output_dir)
            results["video_status"] = f"✅ {video_path.stat().st_size / 1024 / 1024:.1f} MB"
            
            logger.info(f"✅ Step 4 done: Video at {video_path}\n")

        # ════════════════════════════════════════════════════
        # STEP 5: Generate Thumbnail (FREE — Pillow)
        # ════════════════════════════════════════════════════
        if start_step <= 5 <= end_step:
            logger.info("🖼️ STEP 5: Generating thumbnail...")
            from modules.thumbnail import generate_thumbnail

            if not script_data:
                with open(output_dir / "script_data.json", encoding="utf-8") as f:
                    script_data = json.load(f)

            title = script_data.get("title", "Daily Current Affairs")
            thumbnail_path = generate_thumbnail(title, output_dir)
            results["thumbnail_status"] = "✅ Done"
            
            logger.info(f"✅ Step 5 done: Thumbnail at {thumbnail_path}\n")

        # ════════════════════════════════════════════════════
        # STEP 6: Upload to YouTube (FREE — YouTube Data API v3)
        # ════════════════════════════════════════════════════
        if start_step <= 6 <= end_step:
            if dry_run:
                logger.info("📤 STEP 6: SKIPPED (dry run)\n")
                results["upload_status"] = "⏭ Skipped (dry run)"
            else:
                logger.info("📤 STEP 6: Uploading to YouTube...")
                from modules.uploader import upload_video, get_schedule_time

                if not script_data:
                    with open(output_dir / "script_data.json", encoding="utf-8") as f:
                        script_data = json.load(f)
                if not video_path:
                    video_path = output_dir / "final_video.mp4"
                if not thumbnail_path:
                    thumbnail_path = output_dir / "thumbnail.png"

                schedule = get_schedule_time()
                youtube_result = upload_video(
                    video_path=video_path,
                    title=script_data.get("title", "Daily Current Affairs"),
                    description=script_data.get("description", ""),
                    tags=script_data.get("tags", []),
                    thumbnail_path=thumbnail_path,
                    schedule_time=schedule,
                )
                results["upload_status"] = "✅ Uploaded"
                results["youtube_url"] = youtube_result.get("url", "")
                
                logger.info(f"✅ Step 6 done: {youtube_result.get('url')}\n")

        # ════════════════════════════════════════════════════
        # STEP 7: Cross-post (FREE — Shorts + Telegram)
        # ════════════════════════════════════════════════════
        if start_step <= 7 <= end_step:
            if dry_run:
                logger.info("📱 STEP 7: SKIPPED (dry run)\n")
                results["short_status"] = "⏭ Skipped"
                results["telegram_status"] = "⏭ Skipped"
            else:
                logger.info("📱 STEP 7: Cross-posting...")
                from modules.cross_poster import create_short_clip, upload_short, post_to_telegram

                if not video_path:
                    video_path = output_dir / "final_video.mp4"
                if not script_data:
                    with open(output_dir / "script_data.json", encoding="utf-8") as f:
                        script_data = json.load(f)

                # Create Short clip
                short_path = create_short_clip(video_path, output_dir)
                results["short_status"] = "✅ Created"

                # Upload Short
                try:
                    upload_short(
                        short_path,
                        title=script_data.get("title", ""),
                        description=script_data.get("description", ""),
                        tags=script_data.get("tags", []),
                    )
                    results["short_status"] = "✅ Uploaded"
                except Exception as e:
                    logger.warning(f"Short upload failed: {e}")

                # Post to Telegram
                yt_url = youtube_result.get("url", results.get("youtube_url", ""))
                post_to_telegram(
                    title=script_data.get("title", ""),
                    youtube_url=yt_url,
                    summary=script_data.get("description", "")[:200],
                )
                results["telegram_status"] = "✅ Posted"
                
                logger.info("✅ Step 7 done\n")

        # ════════════════════════════════════════════════════
        # STEP 8: Notify (FREE — Telegram Bot)
        # ════════════════════════════════════════════════════
        if start_step <= 8 <= end_step:
            if dry_run:
                logger.info("🔔 STEP 8: SKIPPED (dry run)\n")
            else:
                logger.info("🔔 STEP 8: Sending notification...")
                from modules.notifier import send_notification, send_daily_summary

                yt_url = youtube_result.get("url", results.get("youtube_url", ""))
                title = script_data.get("title", "Daily Current Affairs")

                send_notification(title=title, youtube_url=yt_url, status="ready")
                send_daily_summary(results)
                
                logger.info("✅ Step 8 done\n")

        # ════════════════════════════════════════════════════
        # SUMMARY
        # ════════════════════════════════════════════════════
        logger.info(f"{'='*60}")
        logger.info("🎉 PIPELINE COMPLETE!")
        logger.info(f"📂 Output: {output_dir}")
        for key, val in results.items():
            logger.info(f"   {key}: {val}")
        logger.info(f"{'='*60}")

        # Save results
        with open(output_dir / "pipeline_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    except Exception as e:
        logger.error(f"\n❌ Pipeline failed at: {e}")
        logger.error(traceback.format_exc())

        # Try to notify about failure
        try:
            from modules.notifier import send_notification
            send_notification(
                title="Pipeline Error",
                status="error",
                extra_info=str(e)[:200],
            )
        except Exception:
            pass

        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="🎬 Automated YouTube Current Affairs Channel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                  Full pipeline (fetch → upload → notify)
  python main.py --dry-run        Generate everything locally, skip upload
  python main.py --step 1         Only fetch news
  python main.py --step 1-3       Run steps 1 through 3
  python main.py --step 4         Only build video (needs prior steps)
        """,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run pipeline without uploading or posting (local only)",
    )
    parser.add_argument(
        "--step", type=str, default=None,
        help="Run specific step(s): '1' for single, '1-3' for range",
    )

    args = parser.parse_args()

    # Parse step range
    step_range = None
    if args.step:
        if "-" in args.step:
            parts = args.step.split("-")
            step_range = (int(parts[0]), int(parts[1]))
        else:
            s = int(args.step)
            step_range = (s, s)

    success = run_pipeline(dry_run=args.dry_run, step_range=step_range)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
