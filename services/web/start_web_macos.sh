#!/bin/bash

# Next.js Web App Startup Script for macOS

PROJECT_ROOT="/Users/srikaryaganti/workspaces/drdo/diksuchi-ai"
SERVICE_DIR="$PROJECT_ROOT/services/web"

cd "$SERVICE_DIR"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source <(cat "$PROJECT_ROOT/.env" | grep -v '^#' | grep -v '^$' | sed 's/#.*$//')
    set +a
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "ERROR: Node modules not found. Please install dependencies first:"
    echo "  pnpm install"
    exit 1
fi

# Check PostgreSQL connection
echo "Checking PostgreSQL connection..."
psql -U postgres -h localhost -p 5432 -d diksuchi -c "SELECT 1;" > /dev/null 2>&1 || {
    echo "ERROR: PostgreSQL not running or not accessible."
    echo "Start PostgreSQL with: brew services start postgresql@16"
    echo "Or create database: psql postgres -c \"CREATE DATABASE diksuchi;\""
    exit 1
}

# Run Prisma migrations
echo "Running Prisma migrations..."
pnpm prisma migrate deploy

# Generate Prisma client
echo "Generating Prisma client..."
pnpm prisma generate

# Choose mode
echo ""
echo "Starting Next.js Web App on port 3000..."
echo ""
echo "Choose mode:"
echo "  1) Development (pnpm dev) - Hot reload enabled"
echo "  2) Production (pnpm build && pnpm start) - Optimized build"
echo ""
read -p "Enter choice [1-2]: " MODE_CHOICE

case $MODE_CHOICE in
    1)
        echo "Starting in development mode..."
        pnpm dev
        ;;
    2)
        echo "Building for production..."
        pnpm build
        echo "Starting production server..."
        pnpm start
        ;;
    *)
        echo "Invalid choice. Starting in development mode..."
        pnpm dev
        ;;
esac
