# systemd unit files

Reference copies of the systemd **user** unit files that supervise the
Diksuchi AI services on the deployment host. Operational commands
(start / stop / restart / logs) are documented in
[`docs/systemd-services.md`](../../docs/systemd-services.md).

## Units

| File | Type | What it does |
|---|---|---|
| `diksuchi-infra.service` | oneshot | Runs `scripts/wait-infra.sh` — gates everything else until Ollama, postgres, redis are reachable |
| `diksuchi-ollama-preload.service` | oneshot | Runs `scripts/preload-ollama-models.sh` to pull `gemma4:e4b` into Ollama |
| `diksuchi-rag-api.service` | simple | FastAPI retrieval service on port 5001 |
| `diksuchi-rag-worker.service` | simple | Redis queue consumer for document processing |
| `diksuchi-voice.service` | simple | STT (Whisper) + TTS (Indic Parler) on port 8001 |
| `diksuchi-web.service` | simple | Next.js frontend on port 3000 (rebuilds via `ExecStartPre=pnpm build`) |

## Install on a fresh machine

```bash
# 1. One-time prerequisite: enable lingering so user services start at boot
#    without needing an interactive login.
sudo loginctl enable-linger "$USER"

# 2. Copy the unit files into the systemd user directory.
mkdir -p ~/.config/systemd/user
cp deploy/systemd/*.service ~/.config/systemd/user/

# 3. Reload systemd and enable + start the units.
systemctl --user daemon-reload
systemctl --user enable --now \
  diksuchi-infra \
  diksuchi-ollama-preload \
  diksuchi-rag-api \
  diksuchi-rag-worker \
  diksuchi-voice \
  diksuchi-web

# 4. Verify.
systemctl --user status 'diksuchi-*' --no-pager
```

## Paths to substitute on a new machine

The unit files use absolute paths hardcoded for the current setup. Before
copying, update these placeholders to match the new host:

| Hardcoded value | Replace with |
|---|---|
| `/home/avision/workspace/diksuchi-ai` | wherever you cloned the repo |
| `/home/avision/.nvm/versions/node/v22.22.1` | output of `dirname $(which node)` (look one level up — e.g. `~/.nvm/versions/node/<your-version>`) |

A quick `sed` covers both at once, run before `cp`:

```bash
REPO_DIR=/path/to/your/diksuchi-ai
NODE_BIN_DIR=$(dirname "$(which node)")  # e.g. ~/.nvm/versions/node/v22.x.x/bin
NODE_PREFIX=${NODE_BIN_DIR%/bin}

sed -e "s|/home/avision/workspace/diksuchi-ai|$REPO_DIR|g" \
    -e "s|/home/avision/.nvm/versions/node/v22.22.1|$NODE_PREFIX|g" \
    deploy/systemd/diksuchi-*.service \
  | tee >(cat > /dev/null)  # preview; pipe to actual install when satisfied
```

Then write the substituted versions into `~/.config/systemd/user/` and
proceed with `daemon-reload` + `enable --now`.

## Prerequisites assumed by the units

- **Linux + systemd** with user-level service support (most distros do).
- **Per-service Python virtualenvs** present at the paths above:
  - `services/rag-service/.venv` (used by `diksuchi-rag-api` and
    `diksuchi-rag-worker`)
  - `services/voice-service/.venv` (used by `diksuchi-voice`)
- **Node.js + pnpm** available via the `Environment=PATH=` declared in
  `diksuchi-web.service`. Adjust if not using nvm.
- **Ollama** installed on the Windows host (WSL2 deployments) with
  `OLLAMA_HOST=0.0.0.0:11434` so Linux-side services can reach it. Native
  Linux deployments would adapt or remove `diksuchi-ollama-preload`.
- **Postgres + Redis** as system-level systemd services (`postgresql`,
  `redis-server`) installed via apt — see
  `scripts/install-native-pg-redis.sh`. They auto-start at boot;
  `wait-infra.sh` only verifies reachability before app services start.

## Updating the units

If you edit a unit file in `~/.config/systemd/user/`, mirror the change
into this directory and commit, so the repo stays the canonical record.
The flow:

```bash
# Edit live unit, test it
$EDITOR ~/.config/systemd/user/diksuchi-web.service
systemctl --user daemon-reload
systemctl --user restart diksuchi-web

# Mirror to repo
cp ~/.config/systemd/user/diksuchi-web.service deploy/systemd/
git add deploy/systemd/diksuchi-web.service
git commit -m "..."
```
