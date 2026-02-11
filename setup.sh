#!/bin/bash
# setup.sh — Create virtual environment and install all dependencies
# Usage: bash setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="venv"
PYTHON_CMD=""

for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Python not found. Please install Python 3.9+ first."
    exit 1
fi

echo "============================================================"
echo "  YouTube Current Affairs Platform — Setup"
echo "============================================================"
echo ""

PY_VERSION=$($PYTHON_CMD --version 2>&1)
echo "Using: $PY_VERSION"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR/"
    echo "To recreate, delete it first: rm -rf $VENV_DIR"
else
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "Virtual environment created at $VENV_DIR/"
fi

echo ""
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Upgrading pip..."
pip install --upgrade pip --quiet

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "Checking for ffmpeg..."
if command -v ffmpeg &>/dev/null; then
    echo "ffmpeg: $(ffmpeg -version 2>&1 | head -1)"
else
    echo "WARNING: ffmpeg not found. Install it:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS:         brew install ffmpeg"
    echo "  Windows:       choco install ffmpeg"
fi

if [ ! -f .env ]; then
    if [ -f .env.template ]; then
        cp .env.template .env
        echo ""
        echo "Created .env from template. Edit it with your API keys."
    fi
fi

echo ""
echo "============================================================"
echo "  Setup complete!"
echo ""
echo "  Activate the virtual environment:"
echo "    source venv/bin/activate"
echo ""
echo "  Start the dashboard:"
echo "    python dashboard.py"
echo ""
echo "  Run the pipeline:"
echo "    python main.py"
echo "    python main.py --dry-run"
echo "============================================================"
