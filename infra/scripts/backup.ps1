# Backup SQLite pour Sen_Parcelle (single container, Windows)
# Usage: .\backup.ps1
# Sauvegarde la base SQLite depuis le volume Docker.
# Prérequis : conteneur "sen-parcelle" en cours d'exécution.

param(
    [string]$Container = "sen-parcelle"
)

$BackupDir = Join-Path $PSScriptRoot "..\backups"
$Date = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupFile = Join-Path $BackupDir "sen_parcelle_${Date}.sqlite3"

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] Backup SQLite depuis ${Container}..."

docker exec $Container sqlite3 /data/db.sqlite3 ".backup '/tmp/sen-parcelle-backup-tmp.sqlite3'"
if (-not $?) { Write-Error "Echec du backup SQLite"; exit 1 }

docker cp "${Container}:/tmp/sen-parcelle-backup-tmp.sqlite3" $BackupFile
if (-not $?) { Write-Error "Echec du copie docker cp"; exit 1 }

docker exec $Container rm -f /tmp/sen-parcelle-backup-tmp.sqlite3

Write-Host "[OK] Backup créé : ${BackupFile}"

# Compression (zip natif PowerShell, pas de gzip requis)
$ZipFile = "${BackupFile}.zip"
Compress-Archive -Path $BackupFile -DestinationPath $ZipFile -CompressionLevel Optimal
Remove-Item -Force $BackupFile
$BackupFile = $ZipFile
Write-Host "[OK] Compressé : ${ZipFile}"

# Nettoyage : backups > 30 jours
$limit = (Get-Date).AddDays(-30)
Get-ChildItem -Path $BackupDir -Filter *.zip -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt $limit } | Remove-Item -Force
Write-Host "[OK] Anciens backups (>30 jours) nettoyés"

# Rotation : garder les 7 derniers
Get-ChildItem -Path $BackupDir -Filter *.zip -ErrorAction SilentlyContinue | Sort-Object CreationTime -Descending | Select-Object -Skip 7 | Remove-Item -Force
Write-Host "[OK] Rotation effectuée (7 derniers gardés)"
