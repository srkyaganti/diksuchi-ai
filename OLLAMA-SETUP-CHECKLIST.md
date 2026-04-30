# Ollama Keep-Alive Setup Checklist

Complete this checklist to enable instant LLM response times (zero cold-start lag).

## ✅ Quick Setup (5 minutes)

### On Windows (Administrator PowerShell)

- [ ] Open PowerShell as Administrator
  - Press `Win + X` → Select "Windows PowerShell (Admin)"

- [ ] Navigate to the scripts directory
  ```powershell
  cd "C:\Path\To\Your\diksuchi-ai\scripts\windows"
  ```

- [ ] Enable script execution
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
  ```

- [ ] Run the automated setup
  ```powershell
  .\setup-ollama-startup.ps1
  ```

- [ ] Verify the shortcut was created
  - Check: `C:\Users\%USERNAME%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
  - Should see: `Ollama-Keep-Alive.lnk`

### Test Before Restart (Optional)

- [ ] Double-click the `Ollama-Keep-Alive.lnk` shortcut
- [ ] Verify Ollama starts with this message:
  ```
  Setting environment variables:
   - OLLAMA_KEEP_ALIVE = -1 (indefinite keep-alive)
   - OLLAMA_HOST = 0.0.0.0:11434
  ```

### Restart Windows

- [ ] Save any work and restart your computer
- [ ] Ollama should automatically start on boot with keep-alive enabled

---

## ✅ Verification

### From WSL2
```bash
curl http://localhost:11434/api/tags
```

Should return JSON with your models listed.

### From Windows PowerShell
```powershell
curl.exe http://localhost:11434/api/tags
```

---

## ✅ In Diksuchi-AI

The RAG service will now get instant responses from Ollama (no cold-start lag).

### Test LLM Response Time
1. Access Diksuchi-AI at: `http://localhost:3000`
2. Make a chat request
3. First response should be **instant** (no 30-60 second wait)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Script won't run | Right-click PowerShell → Run as Administrator |
| ExecutionPolicy error | Run `Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process` |
| Ollama not found | Edit path in `start-ollama-with-keepalive.bat` |
| Can't access from WSL2 | Verify `OLLAMA_HOST=0.0.0.0:11434` in batch file |
| Want to disable | Delete shortcut from Startup folder |

---

## What Changed

### Before (Default)
```
Request 1: 60 seconds (cold start) ❌
Request 2: 1 second (warm) ✅
Wait 5 minutes...
Request 3: 60 seconds (cold start again) ❌
```

### After (Keep-Alive Enabled)
```
Request 1: 1 second ✅
Request 2: 1 second ✅
Request 3: 1 second ✅
All requests are consistently fast!
```

---

## Files Created

- `scripts/windows/start-ollama-with-keepalive.bat` - Batch file to start Ollama
- `scripts/windows/setup-ollama-startup.ps1` - Automated setup script
- `scripts/windows/README.md` - Detailed documentation
- `OLLAMA-SETUP-CHECKLIST.md` - This file

---

## Next Steps

1. Complete the checklist above
2. Restart Windows
3. Test LLM responses in Diksuchi-AI
4. Enjoy instant inference! ⚡

---

**For questions:** See `scripts/windows/README.md` for detailed troubleshooting.
