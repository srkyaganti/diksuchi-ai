# Diksuchi-AI Setup Script for Windows
# Automates the installation and configuration process

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Diksuchi-AI Platform Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator. Some operations may fail." -ForegroundColor Yellow
    Write-Host "It's recommended to run PowerShell as Administrator." -ForegroundColor Yellow
    Write-Host ""
}

# Check Docker
Write-Host "[1/7] Checking Docker..." -ForegroundColor Green
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker not found!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

$dockerVersion = docker --version
Write-Host "  Found: $dockerVersion" -ForegroundColor Gray

# Check if Docker is running
try {
    docker ps | Out-Null
    Write-Host "  Docker is running" -ForegroundColor Gray
} catch {
    Write-Host "ERROR: Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Check Git
Write-Host "[2/7] Checking Git..." -ForegroundColor Green
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "WARNING: Git not found!" -ForegroundColor Yellow
    Write-Host "Install from: https://git-scm.com/download/win" -ForegroundColor Yellow
} else {
    $gitVersion = git --version
    Write-Host "  Found: $gitVersion" -ForegroundColor Gray
}

# Create .env file if not exists
Write-Host "[3/7] Configuring environment..." -ForegroundColor Green
if (!(Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "  Created .env file from .env.example" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  IMPORTANT: Please edit .env file with your configuration" -ForegroundColor Yellow
    Write-Host "  Required settings:" -ForegroundColor Yellow
    Write-Host "    - BETTER_AUTH_SECRET (generate with: openssl rand -base64 32)" -ForegroundColor Yellow
    Write-Host "    - HF_TOKEN (optional - Hugging Face token for model downloads)" -ForegroundColor Yellow
    Write-Host ""

    $editNow = Read-Host "Open .env in notepad now? (y/n)"
    if ($editNow -eq "y") {
        notepad .env
        Write-Host "  Waiting for you to finish editing..." -ForegroundColor Gray
        Read-Host "Press Enter after editing .env to continue"
    } else {
        Write-Host "  Remember to edit .env before using the application!" -ForegroundColor Yellow
    }
} else {
    Write-Host "  .env file already exists" -ForegroundColor Gray
}

# Create models directories
Write-Host "[4/7] Creating model directories..." -ForegroundColor Green
$modelDirs = @("models/whisper", "models/parler")
foreach ($dir in $modelDirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created $dir" -ForegroundColor Gray
    }
}

# Download models (optional)
Write-Host "[5/7] Model download..." -ForegroundColor Green
$downloadModels = Read-Host "Download embedding models now? This may take 10-15 minutes (y/n)"
if ($downloadModels -eq "y") {
    Write-Host "  Downloading models..." -ForegroundColor Gray
    Push-Location services/rag-service
    if (Test-Path download-model.sh) {
        bash download-model.sh
    } else {
        Write-Host "  download-model.sh not found, skipping" -ForegroundColor Yellow
    }
    Pop-Location
} else {
    Write-Host "  Skipped model download" -ForegroundColor Gray
    Write-Host "  Models will be downloaded on first use (slower startup)" -ForegroundColor Yellow
}

# Build and start services
Write-Host "[6/7] Building and starting services..." -ForegroundColor Green
Write-Host "  This may take 10-20 minutes on first run..." -ForegroundColor Gray

try {
    # Build services
    Write-Host "  Building Docker images..." -ForegroundColor Gray
    docker-compose build --no-cache 2>&1 | Out-Null

    # Start services
    Write-Host "  Starting services..." -ForegroundColor Gray
    docker-compose up -d

    # Wait for services to be healthy
    Write-Host "  Waiting for services to be ready (this may take 2-5 minutes)..." -ForegroundColor Gray
    $maxWait = 300 # 5 minutes
    $waited = 0
    $interval = 10

    while ($waited -lt $maxWait) {
        Start-Sleep -Seconds $interval
        $waited += $interval

        # Check if all services are healthy
        $status = docker-compose ps --format json | ConvertFrom-Json
        $healthy = ($status | Where-Object { $_.Health -ne "healthy" -and $_.State -ne "running" }).Count -eq 0

        if ($healthy) {
            Write-Host "  All services are ready!" -ForegroundColor Gray
            break
        }

        Write-Host "  Still waiting... ($waited seconds)" -ForegroundColor Gray
    }

    if ($waited -ge $maxWait) {
        Write-Host "  WARNING: Services took longer than expected to start" -ForegroundColor Yellow
        Write-Host "  Check status with: docker-compose ps" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: Failed to start services" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# Verify installation
Write-Host "[7/7] Verifying installation..." -ForegroundColor Green
$services = @{
    "Web App" = "http://localhost:3000"
    "RAG Service" = "http://localhost:5001/health"
    "STT Service" = "http://localhost:8001/health"
    "TTS Service" = "http://localhost:8002/health"
}

foreach ($service in $services.Keys) {
    $url = $services[$service]
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "  $service : OK" -ForegroundColor Gray
    } catch {
        Write-Host "  $service : Not responding (may still be starting)" -ForegroundColor Yellow
    }
}

# Display final status
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services are accessible at:" -ForegroundColor White
Write-Host "  Web Application : http://localhost:3000" -ForegroundColor Cyan
Write-Host "  RAG Service     : http://localhost:5001" -ForegroundColor Cyan
Write-Host "  STT Service     : http://localhost:8001" -ForegroundColor Cyan
Write-Host "  TTS Service     : http://localhost:8002" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  View logs       : docker-compose logs -f" -ForegroundColor Gray
Write-Host "  Stop services   : docker-compose down" -ForegroundColor Gray
Write-Host "  Start services  : docker-compose up -d" -ForegroundColor Gray
Write-Host "  Service status  : docker-compose ps" -ForegroundColor Gray
Write-Host ""
Write-Host "Opening web application in browser..." -ForegroundColor Green
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "For troubleshooting, see DEPLOYMENT.md" -ForegroundColor Yellow
Write-Host ""
