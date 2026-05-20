# ═════════════════════════════════════════════════════════════
# Dockerfile (multi-stage) — Sen_parcelle Admin Angular
# ═════════════════════════════════════════════════════════════

# ─── Stage 1: Builder ───
FROM node:22-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm config set fetch-timeout 60000 && \
    npm config set fetch-retries 5 && \
    npm install --no-optional --no-audit --no-fund 2>&1
COPY . .
RUN npm run build

# ─── Stage 2: Production ───
FROM nginx:alpine AS production
COPY --from=builder /app/dist/sen-parcelle-admin/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
