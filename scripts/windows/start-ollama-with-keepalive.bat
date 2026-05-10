@echo off
REM Ollama with Keep-Alive - Start Ollama and keep models loaded in memory indefinitely
REM This eliminates cold-start latency for LLM requests
REM
REM To use:
REM 1. Place this file in: C:\Users\%USERNAME%\AppData\Local\Ollama\
REM 2. Or any convenient location on your Windows machine
REM 3. Add to Windows Startup (Win+R > shell:startup, create shortcut)
REM 4. Run this batch file whenever you want to start Ollama with keep-alive enabled

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo  Ollama with Keep-Alive Configuration
echo ============================================================
echo.
echo Setting environment variables:
echo  - OLLAMA_KEEP_ALIVE = -1 (indefinite keep-alive)
echo  - OLLAMA_HOST = 0.0.0.0:11434 (accessible from WSL2)
echo.

REM Set environment variables for this process
set OLLAMA_KEEP_ALIVE=-1
set OLLAMA_HOST=0.0.0.0:11434

REM Ollama binary location - adjust if your installation is different
set OLLAMA_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe

REM Check if Ollama exists
if not exist "!OLLAMA_PATH!" (
    echo ERROR: Ollama not found at: !OLLAMA_PATH!
    echo.
    echo Please check your Ollama installation path and update this script.
    echo Typical locations:
    echo   - C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe
    echo   - C:\Program Files\Ollama\ollama.exe
    echo.
    pause
    exit /b 1
)

echo Starting Ollama from: !OLLAMA_PATH!
echo Models will stay loaded in memory indefinitely (no unload timeout)
echo.
echo Accessing from WSL2:
echo   curl http://localhost:11434/api/tags
echo.
echo Press Ctrl+C to stop Ollama
echo ============================================================
echo.

REM Wake WSL in parallel so systemd + linger bring up diksuchi services
echo Triggering WSL boot (default distro)...
start "" /B wsl.exe --exec /bin/true

REM Start Ollama in foreground
"!OLLAMA_PATH!" serve

echo.
echo Ollama stopped.
pause
