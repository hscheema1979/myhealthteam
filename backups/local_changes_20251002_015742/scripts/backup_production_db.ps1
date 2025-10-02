# Production Database Backup Script
# Backs up only production.db as compressed ZIP file
# Target location: d:\git\backups\myhealthteam\
# Naming convention: YYYY_MM_DD_hh_prod_bkup.zip

param(
    [string]$BackupRoot = "d:\git\backups\myhealthteam",
    [int]$RetentionDays = 30,
    [switch]$Verbose = $false
)

# Database file
$dbFile = "production.db"

# Get current timestamp
$timestamp = Get-Date -Format "yyyy_MM_dd_HH"
$logTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Create backup directory if it doesn't exist
if (!(Test-Path $BackupRoot)) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    Write-Host "Created backup directory: $BackupRoot" -ForegroundColor Green
}

# Backup file name and path
$backupName = "${timestamp}_prod_bkup.zip"
$backupPath = Join-Path $BackupRoot $backupName

Write-Host "Starting production database backup..." -ForegroundColor Cyan
Write-Host "Timestamp: $logTimestamp" -ForegroundColor Gray
Write-Host "Target: $backupPath" -ForegroundColor Gray
Write-Host ""

# Check if source database exists
if (!(Test-Path $dbFile)) {
    Write-Host "ERROR: Production database not found: $dbFile" -ForegroundColor Red
    exit 1
}

try {
    # Get source file size
    $sourceSize = (Get-Item $dbFile).Length
    $sourceSizeMB = [math]::Round($sourceSize/1MB, 2)

    if ($Verbose) {
        Write-Host "Source: $dbFile ($sourceSizeMB MB)" -ForegroundColor Gray
    }

    # Create ZIP file containing the database
    Write-Host "Compressing database..." -ForegroundColor Yellow
    Compress-Archive -Path $dbFile -DestinationPath $backupPath -Force

    # Verify backup was created and get compressed size
    if (Test-Path $backupPath) {
        $backupSize = (Get-Item $backupPath).Length
        $backupSizeMB = [math]::Round($backupSize/1MB, 2)
        
        # Calculate compression ratio
        if ($sourceSize -gt 0) {
            $compressionRatio = [math]::Round((1 - ($backupSize / $sourceSize)) * 100, 1)
        } else {
            $compressionRatio = 0
        }

        Write-Host "SUCCESS: Backup created!" -ForegroundColor Green
        Write-Host "  File: $backupName" -ForegroundColor White
        Write-Host "  Size: $backupSizeMB MB (was $sourceSizeMB MB)" -ForegroundColor White
        Write-Host "  Compression: $compressionRatio%" -ForegroundColor White

    } else {
        throw "Backup file was not created"
    }

} catch {
    Write-Host "ERROR: Backup failed - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Cleanup old backups
Write-Host ""
Write-Host "Cleaning up old backups (retention: $RetentionDays days)..." -ForegroundColor Cyan

$cutoffDate = (Get-Date).AddDays(-$RetentionDays)
$oldBackups = Get-ChildItem -Path $BackupRoot -Name "*_prod_bkup.zip" | Where-Object {
    $file = Get-Item (Join-Path $BackupRoot $_)
    $file.LastWriteTime -lt $cutoffDate
}

if ($oldBackups.Count -gt 0) {
    Write-Host "Removing $($oldBackups.Count) old backup(s):" -ForegroundColor Yellow
    foreach ($oldBackup in $oldBackups) {
        $oldBackupPath = Join-Path $BackupRoot $oldBackup
        $fileInfo = Get-Item $oldBackupPath
        $sizeMB = [math]::Round($fileInfo.Length/1MB, 2)
        
        Remove-Item $oldBackupPath -Force
        Write-Host "  Removed: $oldBackup ($sizeMB MB)" -ForegroundColor Gray
    }
} else {
    Write-Host "No old backups found to clean up" -ForegroundColor Green
}

# Create backup log entry
$logFile = Join-Path $BackupRoot "backup_log.txt"
$logEntry = "$logTimestamp - Production backup: $backupName - Size: $backupSizeMB MB - Compression: $compressionRatio%"
Add-Content -Path $logFile -Value $logEntry

Write-Host ""
Write-Host "Backup completed successfully!" -ForegroundColor Green
Write-Host "Log updated: $logFile" -ForegroundColor Gray

exit 0