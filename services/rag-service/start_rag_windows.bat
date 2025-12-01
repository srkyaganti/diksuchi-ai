@echo off
REM RAG Service Startup Script for Windows

set PROJECT_ROOT=C:\path\to\diksuchi-ai
set SERVICE_DIR=%PROJECT_ROOT%\services\rag-service

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

REM Load environment variables from .env
for /f "tokens=*" %%a in ('type %PROJECT_ROOT%\.env ^| findstr /v "^#"') do set %%a

REM Check Redis connection
echo Checking Redis connection...
redis-cli -h %REDIS_HOST% -p %REDIS_PORT% ping >nul 2>&1
if errorlevel 1 (
    echo ERROR: Redis not running. Start Redis first:
    echo   net start Redis
    exit /b 1
)

REM Check ChromaDB connection
echo Checking ChromaDB connection...
curl -s http://%CHROMADB_HOST%:%CHROMADB_PORT%/api/v1/heartbeat >nul 2>&1
if errorlevel 1 (
    echo ERROR: ChromaDB not running. Start ChromaDB first:
    echo   scripts\start_chromadb_windows.bat
    exit /b 1
)

REM Check embedding model exists
if not exist "models\bge-m3.gguf" (
    echo WARNING: Embedding model not found at models\bge-m3.gguf
    echo Please download from: https://huggingface.co/lm-kit/bge-m3-gguf
)

REM Start uvicorn in background
echo Starting RAG Service API on port 5000...
start "RAG-API" /B uvicorn main:app --host 0.0.0.0 --port 5000

REM Wait for API to be ready
timeout /t 5 /nobreak

REM Start RQ worker
echo Starting RQ Worker...
start "RQ-Worker" /B python worker.py

echo.
echo RAG Service started successfully!
echo   API URL: http://localhost:5001
echo.
echo Press Ctrl+C to stop services
echo To stop manually: taskkill /FI "WINDOWTITLE eq RAG-API*" /F
echo                    taskkill /FI "WINDOWTITLE eq RQ-Worker*" /F

pause
