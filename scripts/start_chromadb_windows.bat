@echo off
REM ChromaDB Startup Script for Windows

set PROJECT_ROOT=C:\path\to\diksuchi-ai
cd /d %PROJECT_ROOT%

REM Check if virtual environment exists
if not exist "venv_chromadb\" (
    echo ERROR: ChromaDB virtual environment not found. Please create it first:
    echo   python -m venv venv_chromadb
    echo   .\venv_chromadb\Scripts\Activate.ps1
    echo   pip install chromadb==1.3.5
    exit /b 1
)

REM Activate virtual environment
call venv_chromadb\Scripts\activate.bat

REM Set environment variables
set CHROMA_DATA_PATH=%PROJECT_ROOT%\data\chromadb_data
set IS_PERSISTENT=TRUE
set ANONYMIZED_TELEMETRY=FALSE

REM Create data directory if it doesn't exist
if not exist "%CHROMA_DATA_PATH%" mkdir "%CHROMA_DATA_PATH%"

REM Start ChromaDB server
echo Starting ChromaDB on port 8000...
echo Data path: %CHROMA_DATA_PATH%
echo.

chroma run --host 0.0.0.0 --port 8000 --path %CHROMA_DATA_PATH%
