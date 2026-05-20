#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# deploy.sh — Sen_Parcelle Production Deployment
# ═══════════════════════════════════════════════════════════════
# Prerequisites:
#   - Docker & Docker Compose installed on target
#   - .env.production configured in infra/docker/
#   - SSL certificates in infra/nginx/ssl/
#
# Usage:
#   ./deploy.sh                  # pull & restart stack
#   ./deploy.sh --build          # rebuild backend locally
#   ./deploy.sh --rollback       # rollback to previous tag
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/infra/docker/docker-compose.yml"
ENV_FILE="$PROJECT_DIR/infra/docker/.env.production"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ─── Validation ───────────────────────────────────────────────

validate_prereqs() {
  if ! command -v docker &>/dev/null; then
    log_error "Docker is not installed."
    exit 1
  fi

  if ! docker compose version &>/dev/null; then
    log_error "Docker Compose plugin is not installed."
    exit 1
  fi

  if [ ! -f "$ENV_FILE" ]; then
    log_error ".env.production not found at $ENV_FILE"
    log_error "Copy from .env.production.example and configure all values."
    exit 1
  fi

  if [ ! -f "$PROJECT_DIR/infra/nginx/ssl/sen-parcelle-dev.crt" ]; then
    log_warn "SSL certificate not found. Run gen-ssl-dev.sh first."
  fi
}

# ─── Backup ───────────────────────────────────────────────────

take_backup() {
  log_info "Taking database backup before deployment..."
  if [ -f "$BACKUP_SCRIPT" ]; then
    bash "$BACKUP_SCRIPT" || log_warn "Backup failed but continuing deployment."
  else
    log_warn "Backup script not found at $BACKUP_SCRIPT — skipping."
  fi
}

# ─── Build (optional) ─────────────────────────────────────────

build_backend() {
  log_info "Building backend Docker image..."
  docker build \
    -t sen-parcelle-backend:latest \
    -f "$PROJECT_DIR/backend/Dockerfile" \
    --target production \
    "$PROJECT_DIR/backend"
}

# ─── Deploy ───────────────────────────────────────────────────

deploy_stack() {
  log_info "Building and starting stack..."
  docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans

  log_info "Waiting for backend health check..."
  sleep 10
  if docker compose -f "$COMPOSE_FILE" exec -T backend curl -sf http://localhost:8000/api/health/; then
    log_info "Backend is healthy."
  else
    log_error "Backend health check failed. Check logs: docker compose logs backend"
    exit 1
  fi

  log_info "Cleaning up old images..."
  docker image prune -f

  log_info "Deployment complete."
}

# ─── Rollback ─────────────────────────────────────────────────

rollback() {
  log_warn "Rolling back to previous version..."
  cd "$PROJECT_DIR/infra/docker"
  docker compose -f "$COMPOSE_FILE" down
  # Re-pull previous stable tag
  docker compose -f "$COMPOSE_FILE" pull
  docker compose -f "$COMPOSE_FILE" up -d
  log_info "Rollback complete."
}

# ─── Main ─────────────────────────────────────────────────────

main() {
  case "${1:-}" in
    --build)
      validate_prereqs
      take_backup
      build_backend
      deploy_stack
      ;;
    --rollback)
      rollback
      ;;
    --help|-h)
      echo "Usage: $0 [--build|--rollback|--help]"
      echo ""
      echo "  (no flag)   Pull images & restart stack (Docker Compose build gère Angular)"
      echo "  --build     Build backend image + deploy"
      echo "  --rollback  Rollback to previous version"
      exit 0
      ;;
    *)
      validate_prereqs
      take_backup
      deploy_stack
      ;;
  esac
}

main "$@"
