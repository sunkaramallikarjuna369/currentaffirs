@echo off
REM setup.bat — Create virtual environment and install all dependencies (Windows)
REM Usage: Double-click this file or run: setup.bat

cd /d "%~dp0"

echo ============================================================
echo   YouTube Current Affairs Platform — Setup (Windows)
echo ============================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PY_VERSION=%%i
echo Using: %PY_VERSION%
echo.

if exist venv (
    echo Virtual environment already exists at venv\
    echo To recreate, delete it first: rmdir /s /q venv
) else (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created at venv\
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip --quiet

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Checking for ffmpeg...
where ffmpeg >nul 2>nul
if %errorlevel% equ 0 (
    ffmpeg -version 2>&1 | findstr /i "ffmpeg version"
) else (
    echo WARNING: ffmpeg not found. Install it:
    echo   Option 1: choco install ffmpeg  (if you have Chocolatey)
    echo   Option 2: Download from https://ffmpeg.org/download.html
    echo   After installing, make sure ffmpeg is in your PATH.
)

if not exist .env (
    if exist .env.template (
        copy .env.template .env >nul
        echo.
        echo Created .env from template. Edit it with your API keys.
    )
)

echo.
echo ============================================================
echo   Setup complete!
echo.
echo   Activate the virtual environment:
echo     venv\Scripts\activate
echo.
echo   Start the dashboard:
echo     python dashboard.py
echo.
echo   Run the pipeline:
echo     python main.py
echo     python main.py --dry-run
echo ============================================================
echo.
pause
