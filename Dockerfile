# ═════════════════════════════════════════════════════════════
# Dockerfile — Sen_parcelle (Single Container)
# docker build -t sen-parcelle .
# docker run -p 80:80 -v sen_data:/data sen-parcelle
# ═════════════════════════════════════════════════════════════

# ─── Stage 1: Angular builder ───
FROM node:22-alpine AS angular-builder
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# ─── Stage 2: Python builder ───
FROM python:3.12-slim AS python-builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/pyproject.toml backend/poetry.lock* ./
RUN pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --without dev --no-root --no-interaction --no-ansi 2>&1

# ─── Stage 3: Final image ───
FROM python:3.12-slim
LABEL maintainer="Sen_parcelle" \
      description="Sen_parcelle — Plateforme foncière sécurisée"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.single \
    SQLITE_PATH=/data/db.sqlite3 \
    SECRET_KEY=change-me-in-production

RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* && \
    rm -f /etc/nginx/sites-enabled/default && \
    mkdir -p /data /var/log/supervisor /var/run

COPY --from=python-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin
COPY backend/ /app/backend/

COPY --from=angular-builder /app/dist/sen-parcelle-admin/browser /var/www/html

COPY mobile/build/web /var/www/mobile

COPY infra/nginx/nginx-single.conf /etc/nginx/conf.d/default.conf
COPY infra/docker/supervisord.conf /etc/supervisor/conf.d/senparcelle.conf
COPY infra/docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh && \
    addgroup --system --gid 1001 sen_parcelle && \
    adduser --system --uid 1001 --ingroup sen_parcelle --no-create-home sen_parcelle && \
    chown -R sen_parcelle:sen_parcelle /data /var/log/supervisor /var/run

WORKDIR /app/backend
EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]
