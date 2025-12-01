# Diksuchi-AI - Windows Deployment Guide

Complete guide for deploying Diksuchi-AI platform on Windows machines.

## Prerequisites

### Required Software

1. **Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop/
   - Minimum version: 4.0+
   - Enable WSL2 backend during installation
   - Allocate minimum 8GB RAM, 16GB recommended

2. **Git for Windows**
   - Download: https://git-scm.com/download/win
   - Use default installation settings

3. **System Requirements**
   - Windows 10/11 (64-bit)
   - 16GB RAM minimum (32GB recommended)
   - 50GB free disk space
   - Internet connection for initial setup

### Optional Software

- **Windows Terminal** (recommended for better PowerShell experience)
- **VS Code** for configuration file editing

## Installation Steps

### 1. Clone the Repository

Open PowerShell and run:

```powershell
# Navigate to your desired directory
cd C:\Projects  # or your preferred location

# Clone repository
git clone https://github.com/srkyaganti/diksuchi-ai.git
cd diksuchi-ai
```

### 2. Configure Environment

```powershell
# Copy environment template
copy .env.example .env

# Edit .env file
notepad .env
```

**Required Configuration:**

```env
# Set a secure secret (minimum 32 characters)
BETTER_AUTH_SECRET=your-generated-secret-here

# Optional: Add Hugging Face token for model downloads
HF_TOKEN=your_huggingface_token

# Optional: Add LlamaParse API key for advanced PDF parsing
LLAMAPARSE_API_KEY=your_llamaparse_key
```

**Generate secure secrets:**

```powershell
# Using OpenSSL (if installed)
openssl rand -base64 32

# Or use PowerShell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### 3. Download Models (Optional)

For offline mode or faster startup:

```powershell
cd services\rag-service
bash download-model.sh
cd ..\..
```

### 4. Start Services

```powershell
# Start all services in background
docker-compose up -d

# View startup logs
docker-compose logs -f

# Wait for all services to be healthy (2-5 minutes)
```

### 5. Verify Installation

```powershell
# Check service status
docker-compose ps

# All services should show "healthy" or "running"
```

Open browser and navigate to:
- **Web Application:** http://localhost:3000

## Service Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| Web App | http://localhost:3000 | Main application |
| RAG API | http://localhost:5001 | Document processing |
| STT Service | http://localhost:8001 | Speech-to-text |
| TTS Service | http://localhost:8002 | Text-to-speech |
| ChromaDB | http://localhost:8000 | Vector database |
| PostgreSQL | localhost:5432 | Database (user: postgres, password: password) |

## Common Operations

### Starting Services

```powershell
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d app

# Start with logs (foreground)
docker-compose up
```

### Stopping Services

```powershell
# Stop all services (preserves data)
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v

# Stop specific service
docker-compose stop app
```

### Viewing Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f rag-service

# Last 100 lines
docker-compose logs --tail=100
```

### Restarting Services

```powershell
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart app
```

### Updating Application

```powershell
# Pull latest changes
git pull

# Rebuild and restart services
docker-compose down
docker-compose build
docker-compose up -d
```

## Troubleshooting

### Issue: Docker Desktop not starting

**Solution:**
1. Enable WSL2 in Windows Features
2. Update WSL: `wsl --update`
3. Restart computer
4. Start Docker Desktop

### Issue: Port already in use

**Error:** `port is already allocated`

**Solution:**
```powershell
# Find process using port (e.g., 3000)
netstat -ano | findstr :3000

# Kill process by PID
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
```

### Issue: Services not healthy

**Solution:**
```powershell
# Check logs for errors
docker-compose logs [service-name]

# Common fixes:
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Database connection errors

**Solution:**
```powershell
# Reset database
docker-compose down -v
docker-compose up -d postgres
# Wait 10 seconds
docker-compose up -d
```

### Issue: Out of memory

**Error:** Service containers crashing

**Solution:**
1. Open Docker Desktop
2. Settings → Resources
3. Increase Memory limit to 8GB minimum (16GB recommended)
4. Apply & Restart

### Issue: Model download fails

**Solution:**
```powershell
# Manually download models
cd services\rag-service
bash download-model.sh

# Or download from Hugging Face:
# https://huggingface.co/BAAI/bge-m3
```

### Issue: Permission denied errors

**Solution:**
```powershell
# Run PowerShell as Administrator
# Right-click PowerShell → Run as Administrator

# Or set execution policy
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Performance Optimization

### Docker Desktop Settings

1. **Resources:**
   - Memory: 16GB (minimum 8GB)
   - CPUs: 4-8 cores
   - Disk: 50GB

2. **WSL Integration:**
   - Enable integration with your WSL distro
   - Use WSL2 backend for better performance

### Database Optimization

```powershell
# Access PostgreSQL
docker exec -it diksuchi-postgres psql -U postgres -d diksuchi

# Run vacuum (maintenance)
VACUUM ANALYZE;
```

## Backup and Restore

### Backup Data

```powershell
# Create backup directory
mkdir backups

# Backup database
docker exec diksuchi-postgres pg_dump -U postgres diksuchi > backups\database-$(Get-Date -Format "yyyy-MM-dd").sql

# Backup uploads
docker cp diksuchi-app:/app/uploads backups\uploads
```

### Restore Data

```powershell
# Restore database
Get-Content backups\database-2024-01-01.sql | docker exec -i diksuchi-postgres psql -U postgres -d diksuchi

# Restore uploads
docker cp backups\uploads diksuchi-app:/app/uploads
```

## Security Considerations

### Production Deployment

1. **Change Default Passwords:**
   ```env
   # In .env file
   DATABASE_URL=postgresql://postgres:STRONG_PASSWORD@postgres:5432/diksuchi
   BETTER_AUTH_SECRET=generated-64-character-secret
   INTERNAL_API_SECRET=generated-64-character-secret
   ```

2. **Enable HTTPS:**
   - Use reverse proxy (nginx, Caddy)
   - Configure SSL certificates
   - Update `.env` URLs to use https://

3. **Firewall Configuration:**
   - Only expose necessary ports (3000)
   - Block direct access to 5001, 8001, 8002, 5432

4. **Regular Updates:**
   ```powershell
   # Update Docker images
   docker-compose pull
   docker-compose up -d
   ```

## Monitoring

### Health Checks

```powershell
# Check all service health
docker-compose ps

# Test endpoints
curl http://localhost:3000
curl http://localhost:5001/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

### Resource Usage

```powershell
# View container stats
docker stats

# View disk usage
docker system df
```

## Uninstallation

```powershell
# Stop and remove everything
docker-compose down -v

# Remove images
docker rmi $(docker images "diksuchi-*" -q)

# Remove project directory
cd ..
Remove-Item -Recurse -Force diksuchi-ai
```

## Support

### Getting Help

1. **Check logs first:**
   ```powershell
   docker-compose logs
   ```

2. **GitHub Issues:**
   https://github.com/srkyaganti/diksuchi-ai/issues

3. **Documentation:**
   See README.md for architecture details

### Reporting Issues

Include:
- Windows version
- Docker Desktop version
- Error logs (`docker-compose logs`)
- Steps to reproduce

## Automated Setup Script

For automated setup, use the provided PowerShell script:

```powershell
# Run setup script
.\scripts\setup-windows.ps1
```

This script will:
- Check prerequisites
- Configure environment
- Download models (optional)
- Start all services
- Verify installation

See `scripts/setup-windows.ps1` for details.
