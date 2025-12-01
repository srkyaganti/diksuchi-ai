@echo off
REM Next.js Web App Startup Script for Windows

set PROJECT_ROOT=C:\path\to\diksuchi-ai
set SERVICE_DIR=%PROJECT_ROOT%\services\web

cd /d %SERVICE_DIR%

REM Load environment variables
for /f "tokens=*" %%a in ('type %PROJECT_ROOT%\.env ^| findstr /v "^#"') do set %%a

REM Check if node_modules exists
if not exist "node_modules\" (
    echo ERROR: Node modules not found. Please install dependencies first:
    echo   pnpm install
    exit /b 1
)

REM Check PostgreSQL connection
echo Checking PostgreSQL connection...
psql -U postgres -h localhost -p 5432 -d diksuchi -c "SELECT 1;" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PostgreSQL not running or not accessible.
    echo Start PostgreSQL with: net start postgresql-x64-16
    echo Or create database: psql postgres -c "CREATE DATABASE diksuchi;"
    exit /b 1
)

REM Run Prisma migrations
echo Running Prisma migrations...
pnpm prisma migrate deploy

REM Generate Prisma client
echo Generating Prisma client...
pnpm prisma generate

REM Choose mode
echo.
echo Starting Next.js Web App on port 3000...
echo.
echo Choose mode:
echo   1) Development (pnpm dev) - Hot reload enabled
echo   2) Production (pnpm build ^&^& pnpm start) - Optimized build
echo.
set /p MODE_CHOICE="Enter choice [1-2]: "

if "%MODE_CHOICE%"=="1" (
    echo Starting in development mode...
    pnpm dev
) else if "%MODE_CHOICE%"=="2" (
    echo Building for production...
    pnpm build
    echo Starting production server...
    pnpm start
) else (
    echo Invalid choice. Starting in development mode...
    pnpm dev
)
