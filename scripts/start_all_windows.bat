@echo off
REM Master Startup Script for All Services (Windows)

set PROJECT_ROOT=C:\path\to\diksuchi-ai
cd /d %PROJECT_ROOT%

echo ==========================================
echo Starting Diksuchi-AI Platform (Windows)
echo ==========================================

REM 1. Start PostgreSQL (if not already running)
echo [1/7] Starting PostgreSQL...
net start postgresql-x64-16 >nul 2>&1
timeout /t 2 /nobreak >nul

REM 2. Start Redis (if not already running)
echo [2/7] Starting Redis...
net start Redis >nul 2>&1
timeout /t 2 /nobreak >nul

REM 3. Start ChromaDB
echo [3/7] Starting ChromaDB...
start "ChromaDB" /MIN cmd /c "scripts\start_chromadb_windows.bat > logs\chromadb.log 2>&1"
timeout /t 5 /nobreak >nul

REM 4. Start RAG Service
echo [4/6] Starting RAG Service...
start "RAG-Service" /MIN cmd /c "cd services\rag-service && start_rag_windows.bat > ..\..\logs\rag-service.log 2>&1"
timeout /t 5 /nobreak >nul

REM 5. Start TTS Service
echo [5/6] Starting TTS Service...
start "TTS-Service" /MIN cmd /c "cd services\tts-service && start_tts_windows.bat > ..\..\logs\tts-service.log 2>&1"
timeout /t 5 /nobreak >nul

REM 6. Start Next.js Web App
echo [6/6] Starting Next.js Web App...
start "Web-App" /MIN cmd /c "cd services\web && pnpm dev > ..\..\logs\web-app.log 2>&1"
timeout /t 5 /nobreak >nul

echo.
echo ==========================================
echo All services started!
echo ==========================================
echo Service URLs:
echo   Web App:     http://localhost:3000
echo   ChromaDB:    http://localhost:8000
echo   RAG:         http://localhost:5001
echo   TTS:         http://localhost:8002
echo.
echo External Services (manage separately):
echo   LM Studio:   http://localhost:1234 (LLM inference)
echo   whisper.cpp: http://localhost:8080 (Speech-to-Text)
echo.
echo Commands:
echo   Stop all:    scripts\stop_all_windows.bat
echo   Check logs:  type logs\*.log
echo   Health:      scripts\health_check_windows.bat
echo ==========================================
pause
