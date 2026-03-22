# syntax=docker/dockerfile:1.7

FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --omit=dev --no-audit --no-fund

FROM node:20-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY . .

ENV PORT=3000 \
    NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=768"

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=30s \
    CMD node -e "require('http').get('http://localhost:3000/', r => r.statusCode === 200 ? process.exit(0) : process.exit(1)).on('error', () => process.exit(1))"

CMD ["node", "src/index.js"]