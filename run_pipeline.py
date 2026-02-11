"""
🚀 Automated YouTube Current Affairs — Pipeline Runner
======================================================
This is a standard wrapper for main.py to simplify command line usage
and ensure compatibility with documentation and scheduled tasks.

Usage:
    python run_pipeline.py           # Full pipeline
    python run_pipeline.py --dry-run # Local test only
"""

import sys

# --- PILLOW COMPATIBILITY MONKEY-PATCH ---
# Fixes 'module PIL.Image has no attribute ANTIALIAS' in MoviePy on Pillow 10+
try:
    import PIL.Image
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
except ImportError:
    pass
# -----------------------------------------

# Fix Windows encoding for emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, IOError):
        pass

from main import main

if __name__ == "__main__":
    main()
