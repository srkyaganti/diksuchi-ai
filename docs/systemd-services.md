# Diksuchi AI — systemd Services Guide

All services run as **systemd user services** under the `avision` user in WSL2. They start automatically on boot (no terminal needed).

## Services

| Service | Unit Name | What it does | Port |
|---------|-----------|-------------|------|
| Infrastructure | `diksuchi-infra` | Waits for Ollama + Docker Desktop, starts postgres + redis | — |
| RAG API | `diksuchi-rag-api` | FastAPI retrieval service | 5001 |
| RAG Worker | `diksuchi-rag-worker` | Document processing (Redis queue consumer) | — |
| Voice | `diksuchi-voice` | STT (Whisper) + TTS (Indic Parler) | 8001 |
| Web | `diksuchi-web` | Next.js frontend (production build) | 3000 |

## Startup Order

```
Boot → diksuchi-infra (Ollama → Docker → postgres → redis)
         ↓
       diksuchi-rag-api
       diksuchi-rag-worker
       diksuchi-voice
         ↓
       diksuchi-web (builds first, then starts)
```

## Common Commands

```bash
# --- Status ---
systemctl --user status diksuchi-*                    # All services
systemctl --user status diksuchi-web                  # Single service

# --- Restart after code changes ---
systemctl --user restart diksuchi-web                 # Rebuilds + restarts
systemctl --user restart diksuchi-rag-api             # RAG API
systemctl --user restart diksuchi-rag-worker          # Worker pipeline
systemctl --user restart diksuchi-voice               # Voice service
systemctl --user restart diksuchi-rag-worker diksuchi-rag-api diksuchi-voice diksuchi-web  # All apps

# --- Stop / Start ---
systemctl --user stop diksuchi-web                    # Stop one
systemctl --user start diksuchi-web                   # Start one
systemctl --user stop diksuchi-web diksuchi-voice diksuchi-rag-api diksuchi-rag-worker diksuchi-infra  # Stop all

# --- Logs ---
journalctl --user -fu diksuchi-rag-api                # Follow one service's logs
journalctl --user -fu diksuchi-web                    # Follow web logs
journalctl --user -eu diksuchi-infra                  # View infra boot logs
journalctl --user --since "5 min ago" -u diksuchi-*   # Recent logs from all

# --- After editing service files ---
systemctl --user daemon-reload                        # Reload unit definitions
```

## Service Files Location

```
~/.config/systemd/user/
├── diksuchi-infra.service
├── diksuchi-rag-api.service
├── diksuchi-rag-worker.service
├── diksuchi-voice.service
└── diksuchi-web.service
```

Boot readiness script: `scripts/wait-infra.sh`

## How It Works

- **systemd user services** run under your user account, no root needed
- **`loginctl enable-linger avision`** makes them start at WSL boot without logging in
- **`diksuchi-infra`** is a oneshot service that gates all others — it waits for Ollama (Windows host), Docker Desktop WSL integration, then starts postgres + redis via docker compose
- **App services** use `Requires=diksuchi-infra.service` so they won't start until infrastructure is healthy
- **`diksuchi-web`** uses `ExecStartPre=pnpm build` to build before starting in production mode
- **Python services** use the full venv path (`.venv/bin/python`) so no activation needed
- All services have `Restart=on-failure` with a 5-second delay

## Prerequisites

These must be configured on the Windows host:

1. **Ollama** — set to start on boot, with system env var `OLLAMA_HOST=0.0.0.0:11434`
2. **Docker Desktop** — set to start on boot, with WSL integration enabled
3. **Linger** — run once: `sudo loginctl enable-linger avision`

## Disabling Auto-Start

```bash
# Disable a single service
systemctl --user disable diksuchi-voice

# Re-enable it
systemctl --user enable diksuchi-voice

# Disable everything
systemctl --user disable diksuchi-infra diksuchi-rag-api diksuchi-rag-worker diksuchi-voice diksuchi-web
```
