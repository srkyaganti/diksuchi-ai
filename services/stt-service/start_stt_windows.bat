@echo off
REM STT Service Startup Script for Windows with GPU

set PROJECT_ROOT=C:\path\to\diksuchi-ai
set SERVICE_DIR=%PROJECT_ROOT%\services\stt-service

cd /d %SERVICE_DIR%

REM Check if virtual environment exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found. Please create it first:
    echo   python -m venv venv
    echo   .\venv\Scripts\Activate.ps1
    echo   pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cu121
    echo   pip install -r requirements.txt
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Load environment variables
for /f "tokens=*" %%a in ('type %PROJECT_ROOT%\.env ^| findstr /v "^#"') do set %%a

REM Set API port
set API_PORT=8001

REM Check FFmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo WARNING: FFmpeg not found in PATH
    echo Install FFmpeg and add to PATH
)

REM Check CUDA (optional)
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo WARNING: nvidia-smi not found. GPU acceleration may not work.
) else (
    echo GPU detected: Using CUDA acceleration
)

REM Start STT service
echo Starting STT Service on port 8001...
echo Model: %WHISPER_MODEL%
echo Device: CUDA (Windows GPU)
echo.
echo Note: First run will download Whisper model (~6GB)
echo       Make sure HF_TOKEN is set in .env if needed
echo.

python stt_server.py
