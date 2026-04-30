# PowerShell Script to Setup Ollama with Keep-Alive on Windows Startup
# Run as Administrator

# Must run as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] 'Administrator')) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Steps:"
    Write-Host "1. Right-click on PowerShell"
    Write-Host "2. Select 'Run as Administrator'"
    Write-Host "3. Navigate to the script directory"
    Write-Host "4. Run: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process"
    Write-Host "5. Run: .\setup-ollama-startup.ps1"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Ollama Keep-Alive Startup Setup" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Get the script directory (where the batch file should be)
$scriptDir = (Get-Item -Path $PSScriptRoot).FullName
$batchFile = Join-Path $scriptDir "start-ollama-with-keepalive.bat"

# Check if batch file exists
if (-NOT (Test-Path $batchFile)) {
    Write-Host "ERROR: Batch file not found at: $batchFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure 'start-ollama-with-keepalive.bat' is in the same directory as this script."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Found batch file: $batchFile" -ForegroundColor Green
Write-Host ""

# Create startup folder path
$startupFolder = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup"

# Create a shortcut to the batch file
$shortcutPath = Join-Path $startupFolder "Ollama-Keep-Alive.lnk"

Write-Host "Creating Windows Startup shortcut..."
Write-Host "Shortcut path: $shortcutPath" -ForegroundColor Cyan
Write-Host ""

# Create the shortcut
$WshShell = New-Object -ComObject WScript.Shell
$shortcut = $WshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $batchFile
$shortcut.WorkingDirectory = Split-Path $batchFile
$shortcut.Description = "Ollama with Keep-Alive (models stay loaded in memory)"
$shortcut.WindowStyle = 1  # Normal window
$shortcut.Save()

Write-Host "✅ Shortcut created successfully!" -ForegroundColor Green
Write-Host ""

# Also set system-wide environment variables for maximum reliability
Write-Host "Setting system-wide environment variables..."
Write-Host ""

# Set OLLAMA_KEEP_ALIVE
[Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE", "-1", "User")
Write-Host "✅ OLLAMA_KEEP_ALIVE = -1 (set for current user)" -ForegroundColor Green

# Set OLLAMA_HOST
[Environment]::SetEnvironmentVariable("OLLAMA_HOST", "0.0.0.0:11434", "User")
Write-Host "✅ OLLAMA_HOST = 0.0.0.0:11434 (set for current user)" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Setup Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "What was configured:" -ForegroundColor Yellow
Write-Host "  1. ✅ Windows Startup shortcut for Ollama"
Write-Host "  2. ✅ System environment: OLLAMA_KEEP_ALIVE = -1"
Write-Host "  3. ✅ System environment: OLLAMA_HOST = 0.0.0.0:11434"
Write-Host ""
Write-Host "What happens next:" -ForegroundColor Yellow
Write-Host "  1. On your next Windows restart, Ollama will start automatically"
Write-Host "  2. Models will stay loaded in memory (OLLAMA_KEEP_ALIVE=-1)"
Write-Host "  3. Accessible from WSL2 via 0.0.0.0:11434"
Write-Host "  4. Zero cold-start lag for LLM requests from Diksuchi-AI"
Write-Host ""
Write-Host "To test manually before restart:" -ForegroundColor Yellow
Write-Host "  1. Run: $batchFile"
Write-Host "  2. Or double-click the shortcut in: $startupFolder"
Write-Host ""
Write-Host "To verify Ollama is running from WSL2:" -ForegroundColor Yellow
Write-Host "  curl http://localhost:11434/api/tags"
Write-Host ""
Write-Host "To disable auto-start:" -ForegroundColor Yellow
Write-Host "  Delete the shortcut from: $startupFolder"
Write-Host ""

Read-Host "Press Enter to exit"
