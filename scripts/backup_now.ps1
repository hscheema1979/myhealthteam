# Simple hourly backup with cleanup

param(
    [string]$DatabasePath = "D:\Git\myhealthteam2\Streamlit\production.db",
    [string]$BackupFolder = "D:\Git\myhealthteam2\Streamlit\backups",
    [int]$CleanupDays = 30  # Remove backups older than 30 days
)

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupName = "db_backup_$timestamp.zip"
$backupPath = Join-Path $BackupFolder $backupName

Write-Host "Creating backup: $backupName"

# Create backup
Compress-Archive -Path $DatabasePath -DestinationPath $backupPath -Force

# Get file sizes
$sourceSize = (Get-Item $DatabasePath).Length / 1MB
$backupSize = (Get-Item $backupPath).Length / 1MB

Write-Host "Backup created: $backupPath"
Write-Host "Source: $sourceSize MB, Backup: $backupSize MB"

# Cleanup old backups
Write-Host "Cleaning up backups older than $CleanupDays days..."

$cutoffDate = (Get-Date).AddDays(-$CleanupDays)
$oldBackups = Get-ChildItem -Path $BackupFolder -Filter "db_backup_*.zip" | Where-Object { $_.LastWriteTime -lt $cutoffDate }

$deletedCount = 0
foreach ($oldBackup in $oldBackups) {
    Remove-Item -Path $oldBackup.FullName -Force
    Write-Host "Deleted: $($oldBackup.Name)"
    $deletedCount++
}

if ($deletedCount -eq 0) {
    Write-Host "No old backups to delete"
} else {
    Write-Host "Deleted $deletedCount old backup(s)"
}

# Show backup count
$backupCount = (Get-ChildItem -Path $BackupFolder -Filter "db_backup_*.zip").Count
Write-Host "Total backups: $backupCount"