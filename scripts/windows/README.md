# Windows Setup Scripts for Diksuchi-AI

This directory contains scripts to set up Ollama with persistent model loading on Windows.

## Quick Start (Automated Setup)

### Prerequisites
- Windows 10/11 with Ollama installed
- Administrator access (for creating startup shortcuts)

### Steps

1. **Open PowerShell as Administrator**
   - Press `Win + X`, select "Windows PowerShell (Admin)"
   - Or: Right-click PowerShell → "Run as Administrator"

2. **Navigate to this directory**
   ```powershell
   cd "C:\path\to\diksuchi-ai\scripts\windows"
   ```

3. **Allow script execution** (one-time)
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
   ```

4. **Run the setup script**
   ```powershell
   .\setup-ollama-startup.ps1
   ```

5. **Verify success**
   - A shortcut "Ollama-Keep-Alive.lnk" should appear in:
     - `C:\Users\YourUsername\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

6. **Restart Windows** or test immediately by running the shortcut

---

## Manual Setup (If PowerShell Script Fails)

### Step 1: Copy the Batch File
1. Copy `start-ollama-with-keepalive.bat` to your desired location
   - Recommended: `C:\Users\%USERNAME%\AppData\Local\Ollama\`

### Step 2: Add to Windows Startup
1. Press `Win + R`, type: `shell:startup`
2. Right-click in the folder → New → Shortcut
3. For location, enter the path to the batch file
4. Name it: `Ollama-Keep-Alive`
5. Click Finish

### Step 3: Test
Double-click the shortcut and verify Ollama starts with the keep-alive message.

### Step 4: Restart Windows
Ollama should now start automatically with keep-alive enabled.

---

## What This Does

### Default Ollama Behavior
- Models unload from memory after **5 minutes** of inactivity
- Next request triggers a **cold start** (30-120 second lag)

### With Keep-Alive (-1)
- Models stay in **GPU/CPU memory indefinitely**
- All requests execute at **full speed** (0.5-2 seconds)
- Zero cold-start lag

### Example Performance Impact
```
Without Keep-Alive:
  Request 1 (cold): 60 seconds ❌
  Request 2 (warm): 1 second  ✅
  Wait 5+ minutes...
  Request 3 (cold): 60 seconds ❌

With Keep-Alive:
  Request 1: 1 second ✅
  Request 2: 1 second ✅
  Request 3: 1 second ✅
  (Always fast!)
```

---

## Environment Variables Set

```batch
OLLAMA_KEEP_ALIVE=-1
```
- **-1** = Keep models loaded indefinitely
- **0** = Unload immediately
- **1h** = Keep for 1 hour
- **5m** = Keep for 5 minutes (default)

```batch
OLLAMA_HOST=0.0.0.0:11434
```
- Makes Ollama accessible from WSL2/network
- Not just localhost (which WSL2 can't reach)

---

## Verification

### From Windows PowerShell
```powershell
curl.exe http://localhost:11434/api/tags | ConvertFrom-Json
```

### From WSL2
```bash
curl http://localhost:11434/api/tags
```

Expected output:
```json
{
  "models": [
    {"name": "gemma4:e4b", "size": 5000000000, ...}
  ]
}
```

---

## Troubleshooting

### Script Won't Run (ExecutionPolicy Error)
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

### Ollama Not Found Error
The script couldn't find Ollama. Check the path in `start-ollama-with-keepalive.bat`:
```batch
set OLLAMA_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe
```

Common locations:
- `C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe` ← Most common
- `C:\Program Files\Ollama\ollama.exe`

### Can't Access from WSL2
Make sure the batch file includes:
```batch
set OLLAMA_HOST=0.0.0.0:11434
```

Not `localhost:11434` (WSL2 can't reach Windows localhost).

### Want to Disable Auto-Start
Delete the shortcut from:
```
C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

---

## Integration with Diksuchi-AI

The RAG service at `services/rag-service` will automatically use Ollama at:
```
http://localhost:11434
```

With models staying loaded, inference will be **instant** rather than waiting for cold starts.

---

## References

- [Ollama Keep-Alive Configuration](https://markaicode.com/ollama-keep-alive-memory-management/)
- [Ollama FAQ - Memory Management](https://docs.ollama.com/faq/)
- [Speed Up Ollama - Preload Models](https://medium.com/@rafal.kedziorski/speed-up-ollama-how-i-preload-local-llms-into-ram-for-lightning-fast-ai-experiments)
