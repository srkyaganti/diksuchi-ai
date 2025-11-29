# Multi-stage Dockerfile for Next.js app and worker
FROM node:22-slim AS base

# Enable corepack for pnpm
RUN corepack enable

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Install OpenSSL for Prisma
RUN apt-get update -y && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Copy package files
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set dummy DATABASE_URL for build-time Prisma generation
ENV DATABASE_URL="postgresql://postgres:password@localhost:5432/drdo"

# Generate Prisma Client
RUN pnpm exec prisma generate

# Build Next.js (for standalone output)
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm run build

# Production image for Next.js app
FROM base AS runner-app
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Install OpenSSL for Prisma
RUN apt-get update -y && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/prisma ./prisma
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules

# Copy entrypoint script for auto-migrations
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && chown nextjs:nodejs /app/entrypoint.sh

# Create uploads directory (will be mounted as shared volume in docker-compose)
RUN mkdir -p /app/uploads && chown nextjs:nodejs /app/uploads

# Create home directory for nextjs user (needed for pnpm/corepack cache)
RUN mkdir -p /home/nextjs && chown nextjs:nodejs /home/nextjs

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
ENV HOME=/home/nextjs

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["node", "server.js"]
