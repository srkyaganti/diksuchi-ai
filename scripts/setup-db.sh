#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="$PROJECT_ROOT/services/web"
ENV_FILE="$WEB_DIR/.env"

cd "$WEB_DIR"

export DATABASE_URL="postgresql://postgres:password@localhost:5432/diksuchi?schema=public"

echo "Running Prisma migrations..."
npx prisma migrate deploy

echo "Running seed script..."
npm run seed

echo "Database setup complete!"
