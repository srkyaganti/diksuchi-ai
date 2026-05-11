#!/usr/bin/env bash
# Cut over from Docker to native Postgres + Redis:
#   1. Stop diksuchi-postgres + diksuchi-redis containers
#   2. Configure Redis to enable AOF (matches old `--appendonly yes`)
#   3. Restart native postgresql + redis-server
#   4. Configure Postgres role + diksuchi database
#   5. Smoke-test both
#
# Idempotent: safe to re-run.
set -euo pipefail

DB_USER=postgres
DB_PASS=password
DB_NAME=diksuchi

log() { echo "[cutover] $*"; }

if [[ $EUID -ne 0 ]]; then
    log "Re-running with sudo..."
    exec sudo -E bash "$0" "$@"
fi

# --- 1. Stop Docker containers ---
DOCKER='/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe'
if [[ -x $DOCKER ]]; then
    log "Stopping Docker containers diksuchi-postgres + diksuchi-redis..."
    "$DOCKER" stop diksuchi-postgres diksuchi-redis 2>&1 | sed 's/^/  /' || true
else
    log "docker.exe not found at $DOCKER -- skipping container stop"
fi

# --- 2. Configure Redis: enable AOF ---
REDIS_CONF=/etc/redis/redis.conf
if [[ -f $REDIS_CONF ]]; then
    if grep -qE '^appendonly[[:space:]]+no' "$REDIS_CONF"; then
        log "Enabling AOF in $REDIS_CONF..."
        sed -i 's/^appendonly[[:space:]]\+no/appendonly yes/' "$REDIS_CONF"
    elif ! grep -qE '^appendonly[[:space:]]+yes' "$REDIS_CONF"; then
        log "Appending 'appendonly yes' to $REDIS_CONF..."
        echo "appendonly yes" >> "$REDIS_CONF"
    else
        log "AOF already enabled."
    fi
fi

# --- 3. Restart native services ---
log "Resetting any failed state, then restarting postgresql + redis-server..."
systemctl reset-failed postgresql redis-server 2>/dev/null || true
systemctl restart postgresql
systemctl restart redis-server

# Give them a moment to bind
sleep 2

log "Service states:"
systemctl is-active postgresql redis-server || true

# --- 4. Configure Postgres ---
log "Configuring postgres role + database..."
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
ALTER USER $DB_USER WITH PASSWORD '$DB_PASS';
SQL

if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q '^1$'; then
    log "Creating database $DB_NAME..."
    sudo -u postgres createdb -O "$DB_USER" "$DB_NAME"
else
    log "Database $DB_NAME already exists."
fi

# --- 5. Verify ---
log "Smoke-testing connectivity..."
echo -n "  postgres ping: "
PGPASSWORD=$DB_PASS psql -h localhost -U "$DB_USER" -d "$DB_NAME" -tAc 'select 1;' || true
echo -n "  redis ping:    "
redis-cli ping || true
echo -n "  port 5432:     "
ss -tln | awk '$4 ~ /:5432$/{print $4; found=1} END{if(!found)print "NOT LISTENING"}'
echo -n "  port 6379:     "
ss -tln | awk '$4 ~ /:6379$/{print $4; found=1} END{if(!found)print "NOT LISTENING"}'

log "Done."
