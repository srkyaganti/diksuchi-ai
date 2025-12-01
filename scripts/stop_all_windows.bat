@echo off
REM Stop All Services Script (Windows)

set PROJECT_ROOT=C:\path\to\diksuchi-ai
cd /d %PROJECT_ROOT%

echo ==========================================
echo Stopping Diksuchi-AI Platform (Windows)
echo ==========================================

REM Stop services by window title
echo Stopping Web App...
taskkill /FI "WINDOWTITLE eq Web-App*" /F >nul 2>&1

echo Stopping TTS Service...
taskkill /FI "WINDOWTITLE eq TTS-Service*" /F >nul 2>&1

echo Stopping RAG Service...
taskkill /FI "WINDOWTITLE eq RAG-Service*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq RAG-API*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq RQ-Worker*" /F >nul 2>&1

echo Stopping ChromaDB...
taskkill /FI "WINDOWTITLE eq ChromaDB*" /F >nul 2>&1

REM Optional: Stop infrastructure services
echo.
set /p STOP_INFRA="Stop Redis and PostgreSQL? (y/n): "
if /i "%STOP_INFRA%"=="y" (
    echo Stopping Redis...
    net stop Redis >nul 2>&1
    echo Stopping PostgreSQL...
    net stop postgresql-x64-16 >nul 2>&1
)

echo.
echo ==========================================
echo All services stopped!
echo ==========================================
pause
