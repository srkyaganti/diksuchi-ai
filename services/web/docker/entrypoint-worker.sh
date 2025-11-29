#!/bin/sh
set -e

echo "Generating Prisma Client..."
pnpm exec prisma generate

echo "Starting worker..."
exec "$@"
