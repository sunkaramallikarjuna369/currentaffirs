"""
Step 2: AI Script Writer — Google Gemini Free Tier
Selects top stories and writes a professional news script.
Free: 15 requests/min, 1M+ tokens/day on gemini-2.0-flash.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import google.generativeai as genai

logger = logging.getLogger(__name__)


def generate_script(
    articles: list[dict],
    api_key: str = None,
    model_name: str = None,
    select_count: int = None,
    duration_minutes: int = None,
    language: str = None,
) -> dict:
    """
    Use Gemini to select top stories and write a news script.
    
    Args:
        articles: List of news articles from news_fetcher
    
    Returns:
        dict with keys: title, description, tags, stories, intro_script,
        outro_script, timestamps, full_script
    """
    from config import (
        GEMINI_API_KEY, GEMINI_MODEL, NEWS_SELECT,
        SCRIPT_DURATION_MINUTES, SCRIPT_LANGUAGE, CHANNEL_NAME,
        TEMPLATES_DIR
    )

    api_key = api_key or GEMINI_API_KEY
    model_name = model_name or GEMINI_MODEL
    select_count = select_count or NEWS_SELECT
    duration_minutes = duration_minutes or SCRIPT_DURATION_MINUTES
    language = language or SCRIPT_LANGUAGE

    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "❌ GEMINI_API_KEY not set!\n"
            "Get your FREE key at: https://aistudio.google.com/apikey\n"
            "Then add it to your .env file."
        )

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)

    # Load script template
    template_path = TEMPLATES_DIR / "script_template.txt"
    template = template_path.read_text(encoding="utf-8")

    # Format the template
    prompt_template = template.format(
        channel_name=CHANNEL_NAME,
        select_count=select_count,
        language=language,
        duration=duration_minutes,
    )

    # Build headlines summary for the AI
    today = datetime.now().strftime("%B %d, %Y")
    headlines_text = f"\nTODAY'S DATE: {today}\n\nHEADLINES:\n"
    for i, article in enumerate(articles, 1):
        headlines_text += (
            f"\n{i}. {article['title']}\n"
            f"   Source: {article.get('source', 'Unknown')}\n"
            f"   Summary: {article.get('summary', 'No summary')}\n"
        )

    full_prompt = prompt_template + headlines_text

    logger.info(f"Sending {len(articles)} headlines to Gemini ({model_name})...")

    # Generate with retry logic for rate limits
    import time
    models_to_try = [model_name, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
    # Remove duplicates while preserving order
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]
    
    response = None
    last_error = None
    for try_model in models_to_try:
        model = genai.GenerativeModel(try_model)
        for attempt in range(3):
            try:
                logger.info(f"Trying model {try_model} (attempt {attempt + 1}/3)...")
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=8192,
                        response_mime_type="application/json",
                    ),
                )
                logger.info(f"Success with model {try_model}!")
                break  # Success
            except Exception as e:
                last_error = e
                # ... (rest of retry logic)
                err_str = str(e)
                if "429" in err_str or "quota" in err_str.lower():
                    wait = [5, 15, 30][attempt]
                    logger.warning(f"Rate limited on {try_model}, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"Model {try_model} error: {e}")
                    break  # Non-rate-limit error, try next model
        if response:
            break
    
    if not response:
        raise last_error or ValueError("All Gemini models failed")

    # Safety check
    try:
        if not response.candidates or not response.candidates[0].content.parts:
            # Check for safety filter blocks
            if response.prompt_feedback and hasattr(response.prompt_feedback, "block_reason"):
                reason = response.prompt_feedback.block_reason
                raise ValueError(f"Gemini blocked the request due to safety filters (Reason: {reason})")
            raise ValueError("Gemini returned an empty response (no parts found)")
        
        response_text = response.text.strip()
    except Exception as e:
        logger.error(f"Error accessing Gemini response text: {e}")
        # Log feedback if possible
        if hasattr(response, 'prompt_feedback'):
            logger.debug(f"Prompt feedback: {response.prompt_feedback}")
        raise ValueError(f"Could not retrieve text from Gemini: {e}")
    
    # Handle markdown code blocks in response
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        # Remove first and last lines (```json and ```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        response_text = "\n".join(lines)

    def _clean_json(text):
        """Fix common AI JSON issues: trailing commas, bad escapes, etc."""
        import re
        # Remove trailing commas before } or ]
        text = re.sub(r',\s*([}\]])', r'\1', text)
        # Fix unescaped newlines inside string values
        # Replace actual newlines between quotes with \\n
        text = re.sub(r'(?<=": ")(.*?)(?=")', 
                       lambda m: m.group(0).replace('\n', '\\n'), 
                       text, flags=re.DOTALL)
        return text

    def _extract_json(text, output_dir_for_debug=None):
        """Robustly extract and clean JSON from AI response."""
        import re
        import json
        import unicodedata

        if not text:
            return None

        # Emergency save function
        def save_failed(raw_text):
            if output_dir_for_debug:
                try:
                    debug_path = output_dir_for_debug / "failed_response.txt"
                    debug_path.write_text(raw_text, encoding="utf-8")
                    logger.error(f"🚨 Raw response saved to: {debug_path}")
                except Exception as ex:
                    logger.error(f"Failed to save debug file: {ex}")

        # 1. Extraction: Find the first '{' and the last '}'
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1 or end <= start:
            logger.error("No JSON braces found in response.")
            save_failed(text)
            return None
            
        content = text[start:end+1]

        def clean_json_string(s):
            """Aggressively clean JSON string."""
            # Remove trailing commas
            s = re.sub(r',\s*([}\]])', r'\1', s)
            # Remove comments
            s = re.sub(r'//.*?\n', '\n', s)
            s = re.sub(r'/\*.*?\*/', '', s, flags=re.DOTALL)
            # Escape newlines and tabs in string values
            # (only those that aren't already escaped)
            def fix_escapes(m):
                val = m.group(1)
                val = val.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                return f'": "{val}"'
            s = re.sub(r'":\s*"([^"\\]*(?:\\.[^"\\]*)*)"', fix_escapes, s, flags=re.DOTALL)
            return s

        def _rescue_truncated_json(s):
            """Attempts to fix truncated JSON by closing open quotes and braces."""
            # 1. Fix unclosed quotes
            open_quote = False
            for i, char in enumerate(s):
                if char == '"' and (i == 0 or s[i-1] != '\\'):
                    open_quote = not open_quote
            if open_quote:
                s += '"'
            
            # 2. Fix unclosed braces/brackets
            stack = []
            for char in s:
                if char == '{': stack.append('}')
                elif char == '[': stack.append(']')
                elif char in '} ]':
                    if stack and char == stack[-1]:
                        stack.pop()
            
            # Close in reverse order
            while stack:
                s += stack.pop()
            return s

        # Try multiple cleaning iterations
        attempt = content
        for i in range(4):
            try:
                return json.loads(attempt)
            except json.JSONDecodeError:
                if i == 0: attempt = clean_json_string(content)
                elif i == 1: # Last ditch: remove all non-printable characters
                    attempt = "".join(ch for ch in attempt if unicodedata.category(ch)[0] != "C" or ch in "\n\r\t")
                elif i == 2: # Rescue truncation
                    attempt = _rescue_truncated_json(attempt)
                else: pass
        
        save_failed(text)
        return None

    # Get output dir for debug
    from config import get_today_output_dir
    debug_dir = get_today_output_dir()

    script_data = _extract_json(response_text, debug_dir)
    if not script_data:
        raise ValueError(
            "Could not extract valid JSON from Gemini response. "
            f"Please check {debug_dir / 'failed_response.txt'} to see what the AI produced."
        )

    # Build full script text (for voiceover)
    full_script = script_data.get("intro_script", "")
    for story in script_data.get("stories", []):
        full_script += "\n\n" + story.get("script", "")
    full_script += "\n\n" + script_data.get("outro_script", "")

    script_data["full_script"] = full_script
    script_data["date"] = today

    logger.info(
        f"✅ Script generated: {len(script_data.get('stories', []))} stories, "
        f"~{len(full_script.split())} words"
    )

    return script_data


def save_script(script_data: dict, output_dir: Path) -> Path:
    """Save script data as JSON to output directory."""
    output_path = output_dir / "script_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2, ensure_ascii=False)
    
    # Also save plain text script
    text_path = output_dir / "script.txt"
    text_path.write_text(script_data.get("full_script", ""), encoding="utf-8")
    
    logger.info(f"Script saved to {output_path}")
    return output_path


# ── Test ─────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from modules.news_fetcher import fetch_news
    from config import get_today_output_dir

    articles = fetch_news(max_articles=15)
    script = generate_script(articles)
    
    out_dir = get_today_output_dir()
    save_script(script, out_dir)
    
    print(f"\n{'='*60}")
    print(f"🎬 Title: {script.get('title')}")
    print(f"📝 Stories: {len(script.get('stories', []))}")
    print(f"📏 Word count: {len(script.get('full_script', '').split())}")
    print(f"{'='*60}")
