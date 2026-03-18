# cr8-app frontend — TanStack Start + Nitro (Node.js)
FROM node:24-slim AS base
RUN corepack enable && corepack prepare pnpm@latest --activate

# ── Stage 1: Install deps ───────────────────────────────────
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# ── Stage 2: Build ──────────────────────────────────────────
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# VITE_ vars are inlined at build time — pass via --build-arg
ARG VITE_LAUNCH_MODE
ARG VITE_WEBSOCKET_URL
ARG VITE_DISCORD_WEBHOOK_URL
ARG VITE_WEBRTC_SIGNALING_SERVER_URL
ARG VITE_TURN_SERVER

RUN pnpm build

# ── Stage 3: Runtime ────────────────────────────────────────
FROM node:24-slim
WORKDIR /app
COPY --from=builder /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
