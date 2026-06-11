#!/bin/bash
# Backup SQLite pour Sen_Parcelle (single container, Linux/Mac)
# Usage: ./backup.sh
# Sauvegarde la base SQLite depuis le volume Docker.
# Prérequis : conteneur "sen-parcelle" en cours d'exécution.

set -euo pipefail

CONTAINER="${1:-sen-parcelle}"
BACKUP_DIR="$(dirname "$0")/../backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/sen_parcelle_${DATE}.sqlite3"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Backup SQLite depuis ${CONTAINER}..."

docker exec "$CONTAINER" sqlite3 /data/db.sqlite3 \
    ".backup '/tmp/sen-parcelle-backup-tmp.sqlite3'"

docker cp "$CONTAINER":/tmp/sen-parcelle-backup-tmp.sqlite3 "$BACKUP_FILE"

docker exec "$CONTAINER" rm -f /tmp/sen-parcelle-backup-tmp.sqlite3

echo "[OK] Backup créé : ${BACKUP_FILE}"
gzip "$BACKUP_FILE"
echo "[OK] Compressé : ${BACKUP_FILE}.gz"

# Nettoyage : backups > 30 jours
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
echo "[OK] Anciens backups (>30 jours) nettoyés"

# Rotation : garder les 7 derniers
ls -t "$BACKUP_DIR"/*.gz 2>/dev/null | tail -n +8 | xargs -r rm -f
echo "[OK] Rotation effectuée (7 derniers gardés)"
