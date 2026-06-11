@echo off
REM Backup SQLite pour Sen_Parcelle (single container, Windows)
REM Usage: backup.bat
REM Lance le script PowerShell équivalent.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0backup.ps1" %*
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Echec du backup. Verifiez que Docker est en marche.
    exit /b 1
)
