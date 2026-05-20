#!/bin/bash
# Script de backup PostgreSQL pour Sen_Parcelle (Linux/Mac)
# Usage: ./backup.sh [staging|production]
# Requiert : DB_PASSWORD, DB_HOST, DB_USER, DB_PORT dans l'environnement

set -euo pipefail

: "${DB_PASSWORD:?DB_PASSWORD non definie. Sourcez .env.proroduction.}"
: "${DB_HOST:=localhost}"
: "${DB_PORT:=5432}"
: "${DB_USER:=sen_parcelle}"

DB_NAME="${1:-sen_parcelle}"
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sen_parcelle_${DB_NAME}_${DATE}.sql"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Backup de ${DB_NAME}..."
PGPASSWORD="${DB_PASSWORD}" pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "$DB_NAME" \
    -F c \
    -f "$BACKUP_FILE" \
    -v

echo "[OK] Backup créé : ${BACKUP_FILE}"
gzip "$BACKUP_FILE"
echo "[OK] Compressé : ${BACKUP_FILE}.gz"

# Nettoyage des backups de plus de 30 jours
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
echo "[OK] Anciens backups nettoyés"

# Rotation : garder les 7 derniers
ls -t "$BACKUP_DIR"/*.gz | tail -n +8 | xargs -r rm
echo "[OK] Rotation effectuée (7 derniers gardés)"
