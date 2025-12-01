@echo off
REM TTS Service Startup Script for Windows

set PROJECT_ROOT=C:\path\to\diksuchi-ai
set SERVICE_DIR=%PROJECT_ROOT%\services\tts-service

cd /d %SERVICE_DIR%

REM Check if virtual environment exists
if not exist "venv\" (
    echo ERROR: Virtual environment not found. Please create it first:
    echo   python -m venv venv
    echo   .\venv\Scripts\Activate.ps1
    echo   pip install -r requirements.txt
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Load environment variables
for /f "tokens=*" %%a in ('type %PROJECT_ROOT%\.env ^| findstr /v "^#"') do set %%a

REM Set API port
set API_PORT=8002

REM Check CUDA (optional)
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo WARNING: nvidia-smi not found. GPU acceleration may not work.
) else (
    echo GPU detected: Using CUDA acceleration
)

REM Start TTS service
echo Starting TTS Service on port 8002...
echo Default Language: %TTS_DEFAULT_LANGUAGE%
echo.
echo Note: First run will download ParlerTTS model (~2-3GB)
echo       Make sure HF_TOKEN is set in .env if needed
echo.

python server.py
