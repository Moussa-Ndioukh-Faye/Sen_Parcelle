@echo off
REM Script de backup PostgreSQL pour Sen_Parcelle
REM Usage: backup.bat [staging|production]

if "%DB_PASSWORD%"=="" (
    echo [ERREUR] DB_PASSWORD non definie. Chargez le fichier .env.production.
    exit /b 1
)
if "%DB_HOST%"=="" set DB_HOST=localhost
if "%DB_PORT%"=="" set DB_PORT=5432
if "%DB_USER%"=="" set DB_USER=sen_parcelle

set PGUSER=%DB_USER%
set PGPASSWORD=%DB_PASSWORD%
set PGHOST=%DB_HOST%
set PGPORT=%DB_PORT%
set BACKUP_DIR=.\backups
set DATE=%DATE:~6,4%%DATE:~3,2%%DATE:~0,2%
set TIME=%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

if "%1"=="" (
    set DB_NAME=sen_parcelle
    set BACKUP_FILE=%BACKUP_DIR%\sen_parcelle_%DATE%_%TIME%.sql
) else (
    set DB_NAME=sen_parcelle_%1
    set BACKUP_FILE=%BACKUP_DIR%\sen_parcelle_%1_%DATE%_%TIME%.sql
)

echo [%DATE% %TIME%] Backup de %DB_NAME%...
pg_dump -h %PGHOST% -p %PGPORT% -U %PGUSER% -d %DB_NAME% -F c -f "%BACKUP_FILE%" -v

if %ERRORLEVEL% EQU 0 (
    echo [OK] Backup créé : %BACKUP_FILE%
    echo Compression...
    gzip "%BACKUP_FILE%"
    echo [OK] Backup compressé : %BACKUP_FILE%.gz

    forfiles -p "%BACKUP_DIR%" -m *.gz -d -30 -c "cmd /c del @path"
    echo [OK] Anciens backups (>30 jours) nettoyés
) else (
    echo [ERREUR] Echec du backup !
    exit /b 1
)
