"""
Step 5: Thumbnail Generator — Pillow (100% free, no API key)
Creates YouTube-optimized 1280x720 thumbnail with headline + date + branding.
"""

import logging
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get best available font."""
    import os
    from config import FONTS_DIR
    
    attempts = []
    if bold:
        attempts = ["Roboto-Bold.ttf", "arialbd.ttf", "Impact.ttf"]
    else:
        attempts = ["Roboto-Regular.ttf", "arial.ttf", "segoeui.ttf"]
    
    for name in attempts:
        for directory in [FONTS_DIR, Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts"]:
            fp = directory / name
            if fp.exists():
                return ImageFont.truetype(str(fp), size)
    
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    """Word-wrap text."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def generate_thumbnail(
    headline: str,
    output_dir: Path,
    filename: str = "thumbnail.png",
    date_str: str = None,
) -> Path:
    """
    Generate a YouTube thumbnail (1280x720).
    
    Professional design with:
    - Gradient background
    - Bold headline text
    - Date badge
    - Channel branding
    - "Breaking News" visual elements
    """
    from config import THUMB_WIDTH, THUMB_HEIGHT, CHANNEL_NAME

    W, H = THUMB_WIDTH, THUMB_HEIGHT
    date_str = date_str or datetime.now().strftime("%d %b %Y")

    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # ── Gradient background ──
    for y in range(H):
        t = y / H
        r = int(15 + (45 - 15) * t)
        g = int(10 + (20 - 10) * t)
        b = int(40 + (70 - 40) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

    # ── Red accent bar (top) ──
    draw.rectangle([(0, 0), (W, 8)], fill="#FF0000")
    
    # ── "BREAKING NEWS" / "DAILY NEWS" badge ──
    badge_font = get_font(38, bold=True)
    badge_text = "🔴 DAILY CURRENT AFFAIRS"
    badge_bbox = draw.textbbox((0, 0), badge_text, font=badge_font)
    badge_w = badge_bbox[2] - badge_bbox[0]
    badge_h = badge_bbox[3] - badge_bbox[1]
    
    # Badge background
    bx = 40
    by = 40
    draw.rectangle([(bx - 10, by - 8), (bx + badge_w + 20, by + badge_h + 16)], fill="#CC0000")
    draw.text((bx + 5, by), badge_text, fill="white", font=badge_font)

    # ── Date badge (top right) ──
    date_font = get_font(32, bold=True)
    date_bbox = draw.textbbox((0, 0), date_str, font=date_font)
    date_w = date_bbox[2] - date_bbox[0]
    dx = W - date_w - 50
    draw.rectangle([(dx - 15, by - 8), (dx + date_w + 15, by + badge_h + 16)], fill="#FFD700")
    draw.text((dx, by), date_str, fill="#1A1A2E", font=date_font)

    # ── Main headline ──
    headline_font = get_font(62, bold=True)
    headline_lines = wrap_text(draw, headline.upper(), headline_font, W - 120)
    
    # Center vertically
    total_text_h = len(headline_lines[:4]) * 78
    start_y = (H - total_text_h) // 2 + 20
    
    for line in headline_lines[:4]:
        # Text shadow
        draw.text((62, start_y + 3), line, fill="#000000", font=headline_font)
        # Main text
        draw.text((60, start_y), line, fill="#FFFFFF", font=headline_font)
        start_y += 78

    # ── Separator line ──
    sep_y = start_y + 15
    draw.rectangle([(60, sep_y), (W - 60, sep_y + 4)], fill="#E94560")

    # ── Channel name (bottom) ──
    ch_font = get_font(30, bold=True)
    ch_text = f"📺 {CHANNEL_NAME}"
    ch_bbox = draw.textbbox((0, 0), ch_text, font=ch_font)
    ch_w = ch_bbox[2] - ch_bbox[0]
    
    # Bottom bar
    draw.rectangle([(0, H - 60), (W, H)], fill=(0, 0, 0, 200))
    draw.text(((W - ch_w) // 2, H - 50), ch_text, fill="#FFD700", font=ch_font)

    # ── Bottom red accent ──
    draw.rectangle([(0, H - 6), (W, H)], fill="#FF0000")

    # ── Save ──
    output_path = output_dir / filename
    img.save(output_path, "PNG", quality=95)
    
    logger.info(f"✅ Thumbnail saved: {output_path}")
    return output_path


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from config import get_today_output_dir

    out_dir = get_today_output_dir()
    path = generate_thumbnail(
        headline="Top 8 Headlines That Shook India Today | Budget 2026 Special",
        output_dir=out_dir,
    )
    print(f"✅ Thumbnail: {path}")
