#!/usr/bin/env bash
# Move postgres cluster 16/main back to port 5432.
# (apt install picked 5433 because Docker was holding 5432 at install time.)
set -euo pipefail

log() { echo "[fix-pg-port] $*"; }

if [[ $EUID -ne 0 ]]; then
    log "Re-running with sudo..."
    exec sudo -E bash "$0" "$@"
fi

CONF=/etc/postgresql/16/main/postgresql.conf
sed -i 's/^port[[:space:]]*=.*/port = 5432\t\t\t\t# (change requires restart)/' "$CONF"

log "Restarting postgresql@16-main..."
systemctl restart postgresql@16-main

sleep 1
log "pg_lsclusters:"
pg_lsclusters

log "Smoke test on 5432..."
PGPASSWORD=password psql -h localhost -U postgres -d diksuchi -tAc 'select version();'
