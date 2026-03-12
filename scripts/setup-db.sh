#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/services/web"
ENV_FILE="$WEB_DIR/.env"

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-password}"
DB_NAME="${DB_NAME:-diksuchi}"

echo "Waiting for PostgreSQL at $DB_HOST:$DB_PORT..."

for i in {1..30}; do
  if PGPASSWORD="$DB_PASSWORD" pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
    echo "PostgreSQL is ready!"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "Error: PostgreSQL not ready after 30 seconds"
    exit 1
  fi
  sleep 1
done

cd "$WEB_DIR"

export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

echo "Running Prisma migrations..."
npx prisma migrate deploy

echo "Running seed script..."
npm run seed

echo "Database setup complete!"
