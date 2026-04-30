# Ollama Model Preloading Guide

## Problem
By default, Ollama unloads models from memory after 5 minutes of inactivity. When you make a request to a model that's unloaded, there's a cold start delay (30s-2m+) while the model loads into GPU/CPU memory.

## Solution Overview

There are **3 approaches** (ranked by effectiveness):

### 1. ✅ **Recommended: Set OLLAMA_KEEP_ALIVE on Windows (Best)**

Set the environment variable when starting Ollama so models stay in memory indefinitely.

#### Steps:

**Create a batch file** to start Ollama with keep-alive:

```batch
@echo off
REM Save as: C:\Ollama\start-ollama-with-keepalive.bat

set OLLAMA_KEEP_ALIVE=-1
set OLLAMA_HOST=0.0.0.0:11434

"C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe" serve
pause
```

**Add to Windows Startup:**
1. Press `Win + R`, type `shell:startup`
2. Create a shortcut to the batch file
3. Restart Windows to verify Ollama starts automatically with keep-alive

**Verify in Windows PowerShell:**
```powershell
# Check Ollama is running with keep-alive
curl -s http://localhost:11434/api/tags | ConvertFrom-Json
```

---

### 2. Alternative: API Parameter (Per-Request)

Set `keep_alive: -1` in your API calls to keep models loaded after use:

```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gemma4:e4b",
    "stream": false,
    "keep_alive": -1,
    "prompt": "What is Ollama?"
  }'
```

The RAG service should use this in all Ollama calls.

---

### 3. Manual Preload Script (Dev/Testing)

When Ollama is running on Windows and accessible from WSL2:

```bash
bash /home/avision/workspace/diksuchi-ai/scripts/preload-ollama-models.sh
```

This script:
- Waits for Ollama to be ready at `localhost:11434`
- Loads `gemma4:e4b` into memory
- Sets `keep_alive: -1` to keep it loaded

---

## Configuration Reference

### OLLAMA_KEEP_ALIVE Values

| Value | Behavior |
|-------|----------|
| `-1` | Keep model loaded indefinitely (recommended) |
| `1h` | Keep loaded for 1 hour |
| `30m` | Keep loaded for 30 minutes |
| `5m` | Default (5 minutes) |
| `0` | Unload immediately after request |

### OLLAMA_MAX_LOADED_MODELS

Control how many models stay loaded simultaneously:

```bash
set OLLAMA_MAX_LOADED_MODELS=2  # Keep 2 models in memory
```

---

## Performance Impact

### Without Keep-Alive (Default)
- First request: **30-120 seconds** (cold start)
- Subsequent requests (within 5min): **0.5-2 seconds**
- After 5min idle: Cold start again

### With OLLAMA_KEEP_ALIVE=-1
- All requests: **0.5-2 seconds** (consistent)
- Model stays loaded in GPU/CPU memory
- Zero cold start lag

---

## Verification

Check current Ollama models and their memory status:

```bash
# From Windows PowerShell
curl -s http://localhost:11434/api/tags | ConvertFrom-Json

# From WSL2 (if curl available)
curl -s http://localhost:11434/api/tags
```

---

## Troubleshooting

### Models Unload Too Quickly
→ Increase `OLLAMA_KEEP_ALIVE` value (set to `-1`)

### Out of Memory Errors
→ Reduce `OLLAMA_MAX_LOADED_MODELS` or reduce model count

### Ollama Not Accessible from WSL2
→ Verify `OLLAMA_HOST=0.0.0.0:11434` (not localhost)
→ Check Windows Firewall allows port 11434

---

## For Your Setup (gemma4:e4b)

**Recommended configuration:**

```bash
# Windows environment variables (use one of these methods):

# Option 1: Batch file (recommended)
set OLLAMA_KEEP_ALIVE=-1
set OLLAMA_HOST=0.0.0.0:11434

# Option 2: Windows System Environment Variables
# Control Panel > System > Environment Variables > New
# Variable name: OLLAMA_KEEP_ALIVE
# Variable value: -1
```

After setting, restart Ollama and your models will stay loaded permanently.

---

## References

- [Ollama Keep-Alive and Model Preloading](https://markaicode.com/ollama-keep-alive-memory-management/)
- [Ollama FAQ - Memory Management](https://docs.ollama.com/faq/)
- [Speed Up Ollama - Preload Models](https://medium.com/@rafal.kedziorski/speed-up-ollama-how-i-preload-local-llms-into-ram-for-lightning-fast-ai-experiments)
