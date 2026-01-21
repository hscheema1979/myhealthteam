# restore_vps2_backup.ps1
# Quickly restore VPS2 database from a backup
# Use this if the sync goes wrong

param(
    [string]$BackupFile  # Specific backup file to restore (otherwise lists available backups)
)

$ErrorActionPreference = "Stop"

# Configuration
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path (Split-Path -Parent $scriptDir) "config\db-sync.json"
$config = Get-Content $configPath | ConvertFrom-Json

$masterHost = if ($config.sync.master_user) { "$($config.sync.master_user)@$($config.sync.master_host)" } else { $config.sync.master_host }
$masterDbPath = $config.sync.master_db_path
$backupDir = "/opt/myhealthteam/backups"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VPS2 Database Restore" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $BackupFile) {
    # List available backups
    Write-Host "Available backups on VPS2:" -ForegroundColor White
    Write-Host ""

    $backups = ssh $masterHost "ls -lht $backupDir/production_*.db 2>/dev/null | head -20" 2>$null

    if ($backups) {
        Write-Host $backups -ForegroundColor Gray
        Write-Host ""
        Write-Host "To restore a backup, run:" -ForegroundColor White
        Write-Host "  .\restore_vps2_backup.ps1 -BackupFile '<filename>'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Example:" -ForegroundColor White
        $latestBackup = ssh $masterHost "ls -t $backupDir/production_*.db 2>/dev/null | head -1" 2>$null
        if ($latestBackup) {
            $backupName = $latestBackup -replace "$backupDir/", ""
            Write-Host "  .\restore_vps2_backup.ps1 -BackupFile '$backupName'" -ForegroundColor Gray
        }
    } else {
        Write-Host "  No backups found in $backupDir" -ForegroundColor Yellow
    }
} else {
    # Restore specific backup
    Write-Host "WARNING: This will REPLACE the production database on VPS2!" -ForegroundColor Red
    Write-Host ""
    Write-Host "  Backup: $BackupFile" -ForegroundColor White
    Write-Host "  Target: $masterHost:$masterDbPath" -ForegroundColor White
    Write-Host ""

    $confirm = Read-Host "  Type 'RESTORE' to proceed"

    if ($confirm -eq 'RESTORE') {
        Write-Host ""
        Write-Host "  Restoring..." -ForegroundColor Yellow

        # Create a backup of current state first (safety net)
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $preRestoreBackup = "$backupDir/production_before_restore_$timestamp.db"

        Write-Host "  Creating pre-restore backup: $preRestoreBackup" -ForegroundColor Gray
        ssh $masterHost "cp '$masterDbPath' '$preRestoreBackup'" 2>$null

        # Restore the specified backup
        $fullBackupPath = "$backupDir/$BackupFile"
        $result = ssh $masterHost "cp '$fullBackupPath' '$masterDbPath' && echo 'RESTORE_OK' || echo 'RESTORE_FAILED'" 2>&1

        if ($result -match 'RESTORE_OK') {
            Write-Host ""
            Write-Host "  Restore completed successfully!" -ForegroundColor Green
            Write-Host ""
            Write-Host "  Pre-restore backup saved at: ${masterHost}:${preRestoreBackup}" -ForegroundColor Gray
        } else {
            Write-Host ""
            Write-Host "  Restore FAILED!" -ForegroundColor Red
            Write-Host "  Error: $result" -ForegroundColor Red
            Write-Host ""
            Write-Host "  Current database state should be unchanged." -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "  Cancelled by user." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
