#!/usr/bin/env bash
# Install native Postgres 16 (Ubuntu apt) + Redis 8 (official packages.redis.io)
# Idempotent: safe to re-run.
set -euo pipefail

log() { echo "[install] $*"; }

if [[ $EUID -ne 0 ]]; then
    log "Re-running with sudo..."
    exec sudo -E bash "$0" "$@"
fi

# --- Postgres 16 (Ubuntu noble has v16 in main) ---
log "Installing postgresql + postgresql-contrib..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq postgresql postgresql-contrib

# --- Redis 8 from official packages.redis.io ---
KEYRING=/usr/share/keyrings/redis-archive-keyring.gpg
SOURCES=/etc/apt/sources.list.d/redis.list

if [[ ! -f $KEYRING ]]; then
    log "Adding Redis official GPG key..."
    curl -fsSL https://packages.redis.io/gpg | gpg --dearmor -o "$KEYRING"
    chmod 644 "$KEYRING"
fi

CODENAME=$(lsb_release -cs)
DESIRED="deb [signed-by=$KEYRING] https://packages.redis.io/deb $CODENAME main"
if [[ ! -f $SOURCES ]] || ! grep -qxF "$DESIRED" "$SOURCES"; then
    log "Adding Redis APT source for $CODENAME..."
    echo "$DESIRED" > "$SOURCES"
fi

log "Installing redis (8.x)..."
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq redis

log "Done."
log ""
log "Service status:"
systemctl is-active postgresql || true
systemctl is-active redis-server || true
log ""
log "Versions:"
sudo -u postgres psql -tAc 'select version();' 2>/dev/null || true
redis-server --version || true
