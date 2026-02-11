"""
Step 3: Voiceover Generator — edge-tts (100% free, no API key)
Uses Microsoft Edge's neural TTS voices — high quality, unlimited usage.
Also generates word-level subtitles for video sync.
"""

import asyncio
import logging
from pathlib import Path

import edge_tts

logger = logging.getLogger(__name__)


async def _generate_voiceover_async(
    text: str,
    output_path: Path,
    subtitle_path: Path = None,
    voice: str = None,
    rate: str = None,
    volume: str = None,
) -> Path:
    """Internal async voiceover generation."""
    from config import TTS_VOICE, TTS_RATE, TTS_VOLUME

    voice = voice or TTS_VOICE
    rate = rate or TTS_RATE
    volume = volume or TTS_VOLUME

    logger.info(f"Generating voiceover with voice: {voice}")
    logger.info(f"Text length: {len(text)} chars, ~{len(text.split())} words")

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        volume=volume,
    )

    # Generate audio + subtitles
    sub_maker = edge_tts.SubMaker()
    
    with open(output_path, "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.feed(
                    (chunk["offset"], chunk["duration"]),
                    chunk["text"]
                )

    # Save subtitles
    if subtitle_path:
        srt_content = sub_maker.get_srt()
        subtitle_path.write_text(srt_content, encoding="utf-8")
        logger.info(f"Subtitles saved: {subtitle_path}")

    logger.info(f"✅ Voiceover saved: {output_path}")
    return output_path


def generate_voiceover(
    text: str,
    output_dir: Path,
    filename: str = "voiceover.mp3",
    subtitle_filename: str = "subtitles.vtt",
    voice: str = None,
    rate: str = None,
    volume: str = None,
) -> tuple[Path, Path]:
    """
    Generate voiceover from text using edge-tts.
    
    Returns:
        Tuple of (audio_path, subtitle_path)
    """
    output_path = output_dir / filename
    subtitle_path = output_dir / subtitle_filename

    asyncio.run(
        _generate_voiceover_async(
            text=text,
            output_path=output_path,
            subtitle_path=subtitle_path,
            voice=voice,
            rate=rate,
            volume=volume,
        )
    )

    return output_path, subtitle_path


def list_available_voices(language_filter: str = "en-IN") -> list[dict]:
    """List available edge-tts voices for a language."""
    async def _list():
        voices = await edge_tts.list_voices()
        return [
            {"name": v["ShortName"], "gender": v["Gender"]}
            for v in voices
            if language_filter in v["ShortName"]
        ]
    return asyncio.run(_list())


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from config import get_today_output_dir

    test_text = (
        "Good morning India! Welcome to your daily current affairs update. "
        "Today we bring you the top stories making headlines across the nation. "
        "Let's dive right in. "
        "In our first story today, the Indian economy continues to show strong growth. "
        "Thank you for watching. Don't forget to like, subscribe, and hit the bell icon!"
    )

    out_dir = get_today_output_dir()
    audio_path, sub_path = generate_voiceover(test_text, out_dir)
    
    print(f"\n✅ Audio: {audio_path}")
    print(f"✅ Subtitles: {sub_path}")
    
    # List available Indian English voices
    print("\n🎤 Available Indian English voices:")
    for v in list_available_voices("en-IN"):
        print(f"   {v['name']} ({v['gender']})")
