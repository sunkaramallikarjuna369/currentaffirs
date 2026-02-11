"""
Step 4: Video Builder — Pillow + MoviePy (100% free, no API key)
Creates news video segments with gradient backgrounds, text overlays,
and Ken Burns motion effects. No external image API needed.
"""

import logging
import math
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont
import numpy as np

logger = logging.getLogger(__name__)

# ── Font helpers ─────────────────────────────────────────────

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if custom fonts not available."""
    from config import FONTS_DIR
    
    font_names = [
        "Roboto-Bold.ttf" if bold else "Roboto-Regular.ttf",
        "arial.ttf", "Arial.ttf",
    ]
    
    # Try custom fonts directory
    for name in font_names:
        font_path = FONTS_DIR / name
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)
    
    # Try system fonts (Windows)
    import os
    system_fonts = Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"
    for name in ["arialbd.ttf" if bold else "arial.ttf", "segoeui.ttf", "calibri.ttf"]:
        fp = system_fonts / name
        if fp.exists():
            return ImageFont.truetype(str(fp), size)
    
    # Final fallback
    return ImageFont.load_default()


# ── Frame generators ─────────────────────────────────────────

def create_gradient_bg(
    width: int, height: int,
    color1: tuple = (26, 26, 46),
    color2: tuple = (22, 33, 62),
    direction: str = "diagonal"
) -> Image.Image:
    """Create a smooth gradient background."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    for y in range(height):
        for x in range(width):
            if direction == "diagonal":
                t = (x / width + y / height) / 2
            elif direction == "vertical":
                t = y / height
            else:
                t = x / width
            
            r = int(color1[0] + (color2[0] - color1[0]) * t)
            g = int(color1[1] + (color2[1] - color1[1]) * t)
            b = int(color1[2] + (color2[2] - color1[2]) * t)
            pixels[x, y] = (r, g, b)
    
    return img


def create_news_card(
    headline: str,
    body_text: str,
    story_number: int,
    total_stories: int,
    width: int = 1920,
    height: int = 1080,
    channel_name: str = None,
) -> Image.Image:
    """Create a professional news story card."""
    from config import COLORS, CHANNEL_NAME
    channel_name = channel_name or CHANNEL_NAME

    # Create gradient background
    img = create_gradient_bg(width, height, (15, 15, 35), (25, 40, 75))
    draw = ImageDraw.Draw(img)

    # ── Top bar (channel branding) ──
    draw.rectangle([(0, 0), (width, 60)], fill="#CC0000")
    top_font = get_font(28, bold=True)
    draw.text((30, 14), f"📺 {channel_name}", fill="white", font=top_font)
    
    # Story counter on right
    counter_text = f"STORY {story_number}/{total_stories}"
    counter_font = get_font(24, bold=True)
    bbox = draw.textbbox((0, 0), counter_text, font=counter_font)
    draw.text((width - (bbox[2] - bbox[0]) - 30, 18), counter_text, fill="#FFD700", font=counter_font)

    # ── Breaking news banner ──
    banner_y = 100
    draw.rectangle([(50, banner_y), (width - 50, banner_y + 6)], fill="#E94560")

    # ── Headline ──
    headline_font = get_font(52, bold=True)
    
    # Word wrap headline
    headline_lines = wrap_text(draw, headline, headline_font, width - 160)
    y = banner_y + 40
    for line in headline_lines[:3]:  # Max 3 lines
        draw.text((80, y), line, fill="#FFFFFF", font=headline_font)
        y += 65

    # ── Separator line ──
    y += 20
    draw.rectangle([(80, y), (width - 80, y + 3)], fill="#E94560")
    y += 30

    # ── Body text ──
    body_font = get_font(36)
    body_lines = wrap_text(draw, body_text, body_font, width - 200)
    for line in body_lines[:10]:  # Max 10 lines
        draw.text((100, y), line, fill="#E0E0E0", font=body_font)
        y += 48

    # ── Bottom ticker bar ──
    ticker_h = 50
    draw.rectangle([(0, height - ticker_h), (width, height)], fill="#CC0000")
    ticker_font = get_font(26, bold=True)
    from datetime import datetime
    date_str = datetime.now().strftime("%B %d, %Y")
    draw.text((30, height - ticker_h + 12), f"🔴 LIVE  |  {date_str}  |  {channel_name}", fill="white", font=ticker_font)

    # ── Decorative elements ──
    # Corner accents
    accent_color = "#E94560"
    draw.rectangle([(0, 0), (8, 60)], fill=accent_color)
    draw.rectangle([(width-8, 0), (width, 60)], fill=accent_color)

    return img


def create_intro_frame(
    title: str,
    date_str: str,
    width: int = 1920,
    height: int = 1080,
    channel_name: str = None,
) -> Image.Image:
    """Create the intro title card."""
    from config import CHANNEL_NAME
    channel_name = channel_name or CHANNEL_NAME

    img = create_gradient_bg(width, height, (10, 10, 30), (40, 20, 60), "diagonal")
    draw = ImageDraw.Draw(img)

    # Large channel name
    name_font = get_font(72, bold=True)
    name_bbox = draw.textbbox((0, 0), channel_name, font=name_font)
    name_w = name_bbox[2] - name_bbox[0]
    draw.text(((width - name_w) // 2, 250), channel_name, fill="#FFFFFF", font=name_font)

    # Separator
    sep_w = 400
    draw.rectangle([((width - sep_w) // 2, 360), ((width + sep_w) // 2, 364)], fill="#E94560")

    # Date
    date_font = get_font(42)
    date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
    date_w = date_bbox[2] - date_bbox[0]
    draw.text(((width - date_w) // 2, 400), date_str, fill="#FFD700", font=date_font)

    # Title
    title_font = get_font(48, bold=True)
    title_lines = wrap_text(draw, title, title_font, width - 200)
    y = 500
    for line in title_lines[:3]:
        line_bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = line_bbox[2] - line_bbox[0]
        draw.text(((width - line_w) // 2, y), line, fill="#FFFFFF", font=title_font)
        y += 60

    # "BREAKING NEWS" badge
    badge_font = get_font(36, bold=True)
    badge_text = "🔴 TOP STORIES TODAY"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = badge_bbox[2] - badge_bbox[0]
    badge_x = (width - badge_w) // 2
    draw.rectangle([(badge_x - 20, 700), (badge_x + badge_w + 20, 755)], fill="#CC0000")
    draw.text((badge_x, 708), badge_text, fill="white", font=badge_font)

    # Bottom bar
    draw.rectangle([(0, height - 8), (width, height)], fill="#E94560")

    return img


def create_outro_frame(
    width: int = 1920,
    height: int = 1080,
    channel_name: str = None,
) -> Image.Image:
    """Create the outro card."""
    from config import CHANNEL_NAME, CHANNEL_TAGLINE
    channel_name = channel_name or CHANNEL_NAME

    img = create_gradient_bg(width, height, (10, 10, 30), (30, 15, 50), "diagonal")
    draw = ImageDraw.Draw(img)

    # Thank you
    thanks_font = get_font(64, bold=True)
    text = "Thanks for Watching!"
    bbox = draw.textbbox((0, 0), text, font=thanks_font)
    w = bbox[2] - bbox[0]
    draw.text(((width - w) // 2, 300), text, fill="#FFFFFF", font=thanks_font)

    # Subscribe CTA
    sub_font = get_font(44, bold=True)
    sub_text = "👍 LIKE  |  🔔 SUBSCRIBE  |  💬 COMMENT"
    bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    w = bbox[2] - bbox[0]
    draw.rectangle([((width - w) // 2 - 30, 440), ((width + w) // 2 + 30, 510)], fill="#CC0000")
    draw.text(((width - w) // 2, 450), sub_text, fill="white", font=sub_font)

    # Channel name
    ch_font = get_font(36)
    bbox = draw.textbbox((0, 0), channel_name, font=ch_font)
    w = bbox[2] - bbox[0]
    draw.text(((width - w) // 2, 580), channel_name, fill="#FFD700", font=ch_font)

    # Tagline
    tag_font = get_font(28)
    bbox = draw.textbbox((0, 0), CHANNEL_TAGLINE, font=tag_font)
    w = bbox[2] - bbox[0]
    draw.text(((width - w) // 2, 640), CHANNEL_TAGLINE, fill="#E0E0E0", font=tag_font)

    return img


def wrap_text(draw: ImageDraw.Draw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Word-wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


# ── Video assembly ───────────────────────────────────────────

def build_video(
    script_data: dict,
    voiceover_path: Path,
    output_dir: Path,
    filename: str = "final_video.mp4",
) -> Path:
    """
    Assemble the full news video from script data + voiceover.
    
    Creates: intro → story cards → outro, synced with voiceover audio.
    """
    from moviepy.editor import (
        ImageClip, AudioFileClip, CompositeVideoClip,
        concatenate_videoclips
    )
    from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS, VIDEO_BITRATE
    from datetime import datetime

    logger.info("🎬 Building video...")

    # Load voiceover audio to determine total duration
    audio = AudioFileClip(str(voiceover_path))
    total_duration = audio.duration
    
    stories = script_data.get("stories", [])
    num_stories = len(stories)
    
    # Calculate timing
    intro_duration = 5.0  # seconds
    outro_duration = 5.0
    story_total_time = total_duration - intro_duration - outro_duration
    if story_total_time < 0:
        story_total_time = total_duration * 0.85
        intro_duration = total_duration * 0.075
        outro_duration = total_duration * 0.075
    
    time_per_story = story_total_time / max(num_stories, 1)

    clips = []

    # ── Intro clip ──
    logger.info("Creating intro frame...")
    intro_img = create_intro_frame(
        title=script_data.get("title", "Daily Current Affairs"),
        date_str=script_data.get("date", datetime.now().strftime("%B %d, %Y")),
        width=VIDEO_WIDTH,
        height=VIDEO_HEIGHT,
    )
    intro_array = np.array(intro_img)
    intro_clip = ImageClip(intro_array).set_duration(intro_duration)
    # Ken Burns zoom-in effect
    intro_clip = intro_clip.resize(lambda t: 1 + 0.04 * t / intro_duration)
    intro_clip = intro_clip.set_position("center")
    intro_clip = CompositeVideoClip(
        [ImageClip(np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)).set_duration(intro_duration),
         intro_clip],
        size=(VIDEO_WIDTH, VIDEO_HEIGHT)
    )
    clips.append(intro_clip)

    # ── Story clips ──
    for i, story in enumerate(stories):
        logger.info(f"Creating story {i+1}/{num_stories}: {story.get('headline', '')[:50]}...")
        
        card_img = create_news_card(
            headline=story.get("headline", f"Story {i+1}"),
            body_text=story.get("script", ""),
            story_number=i + 1,
            total_stories=num_stories,
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT,
        )
        card_array = np.array(card_img)
        
        story_clip = ImageClip(card_array).set_duration(time_per_story)
        
        # Subtle zoom effect (Ken Burns)
        zoom_factor = 0.03
        story_clip = story_clip.resize(lambda t, zf=zoom_factor, d=time_per_story: 1 + zf * t / d)
        story_clip = story_clip.set_position("center")
        story_clip = CompositeVideoClip(
            [ImageClip(np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)).set_duration(time_per_story),
             story_clip],
            size=(VIDEO_WIDTH, VIDEO_HEIGHT)
        )
        clips.append(story_clip)

    # ── Outro clip ──
    logger.info("Creating outro frame...")
    outro_img = create_outro_frame(width=VIDEO_WIDTH, height=VIDEO_HEIGHT)
    outro_array = np.array(outro_img)
    outro_clip = ImageClip(outro_array).set_duration(outro_duration)
    outro_clip = outro_clip.resize(lambda t: 1 + 0.02 * t / outro_duration)
    outro_clip = outro_clip.set_position("center")
    outro_clip = CompositeVideoClip(
        [ImageClip(np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)).set_duration(outro_duration),
         outro_clip],
        size=(VIDEO_WIDTH, VIDEO_HEIGHT)
    )
    clips.append(outro_clip)

    # ── Concatenate all clips ──
    logger.info("Concatenating clips...")
    final = concatenate_videoclips(clips, method="compose")
    
    # Set audio
    # Match video duration to audio or vice versa
    if final.duration > audio.duration:
        final = final.subclip(0, audio.duration)
    elif audio.duration > final.duration:
        audio = audio.subclip(0, final.duration)
    
    final = final.set_audio(audio)

    # ── Export ──
    output_path = output_dir / filename
    logger.info(f"Exporting video to {output_path}...")
    final.write_videofile(
        str(output_path),
        fps=VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate=VIDEO_BITRATE,
        preset="medium",
        threads=4,
        logger=None,
    )

    # Cleanup
    audio.close()
    final.close()

    logger.info(f"✅ Video saved: {output_path} ({output_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return output_path


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from config import get_today_output_dir, VIDEO_WIDTH, VIDEO_HEIGHT

    out_dir = get_today_output_dir()

    # Test: generate sample frames
    intro = create_intro_frame("Top 8 Headlines | India News", "February 11, 2026")
    intro.save(out_dir / "test_intro.png")

    card = create_news_card(
        "India's GDP Growth Surges to 7.2% in Latest Quarter",
        "The Indian economy showed remarkable resilience as GDP growth "
        "reached 7.2% in the latest quarter, exceeding analyst expectations. "
        "Key sectors driving growth include manufacturing, services, and agriculture.",
        story_number=1, total_stories=8,
    )
    card.save(out_dir / "test_card.png")

    outro = create_outro_frame()
    outro.save(out_dir / "test_outro.png")

    print(f"✅ Test frames saved to {out_dir}")
