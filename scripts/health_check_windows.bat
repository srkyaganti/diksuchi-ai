@echo off
REM Health Check Script - Verify All Services (Windows)

set PROJECT_ROOT=C:\path\to\diksuchi-ai
cd /d %PROJECT_ROOT%

echo ==========================================
echo Diksuchi-AI Platform Health Check
echo ==========================================

REM Check PostgreSQL
echo PostgreSQL:
psql -U postgres -h localhost -p 5432 -d diksuchi -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (echo   X UNHEALTHY) else (echo   OK HEALTHY)

REM Check Redis
echo Redis:
redis-cli -h localhost -p 6379 ping >nul 2>&1
if errorlevel 1 (echo   X UNHEALTHY) else (echo   OK HEALTHY)

REM Check ChromaDB
echo ChromaDB:
curl -s http://localhost:8000/api/v1/heartbeat >nul 2>&1
if errorlevel 1 (echo   X UNHEALTHY) else (echo   OK HEALTHY)

REM Check RAG Service
echo RAG Service:
curl -s http://localhost:5001/health >nul 2>&1
if errorlevel 1 (echo   X UNHEALTHY) else (echo   OK HEALTHY)

REM Check STT Service
echo STT Service:
curl -s http://localhost:8001/health >nul 2>&1
if errorlevel 1 (echo   X UNHEALTHY) else (echo   OK HEALTHY)

REM Check TTS Service
echo TTS Service:
curl -s http://localhost:8002/health >nul 2>&1
if errorlevel 1 (echo   X UNHEALTHY) else (echo   OK HEALTHY)

REM Check Web App
echo Web App:
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (echo   X UNHEALTHY) else (echo   OK HEALTHY)

echo ==========================================
echo Health check complete!
echo.
echo To view logs:
echo   type logs\chromadb.log
echo   type logs\rag-service.log
echo   type logs\stt-service.log
echo   type logs\tts-service.log
echo   type logs\web-app.log
echo.
echo Note: LLM inference provided by LM Studio (localhost:1234)
echo ==========================================
pause
