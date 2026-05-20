# ═════════════════════════════════════════════════════════════
# Dockerfile (multi-stage) — Sen_parcelle Backend
# ═════════════════════════════════════════════════════════════

# ─── Stage 1: Builder ───
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system build dependencies for GDAL/PostGIS
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc gdal-bin libgdal-dev python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install Poetry and install dependencies globally (no virtualenv)
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --without dev --no-root

# ─── Stage 2: Production ───
FROM python:3.11-slim AS production

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 gdal-bin curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create static/media directories before switching user
RUN mkdir -p /app/staticfiles /app/media

# Create non-root user and ensure write access to static/media
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

ENV DJANGO_SETTINGS_MODULE=config.settings.production

CMD ["gunicorn", "config.wsgi:application", \
      "--bind", "0.0.0.0:8000", \
      "--workers", "4", \
      "--worker-class", "gthread", \
      "--threads", "2", \
      "--timeout", "120"]
