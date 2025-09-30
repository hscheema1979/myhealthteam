# Database Backup Script
# Automatically backs up production.db with timestamp in a zip file
# Designed to run every weekday at 7pm via Task Scheduler

param(
    [string]$SourceDB = "D:\Git\myhealthteam2\Streamlit\production.db",
    [string]$BackupFolder = "D:\Git\myhealthteam2\Streamlit\backups",
    [int]$RetentionDays = 30
)

# Get current timestamp
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupName = "bkup_db_$timestamp.zip"
$backupPath = Join-Path $BackupFolder $backupName

# Create backup folder if it doesn't exist
if (!(Test-Path $BackupFolder)) {
    New-Item -ItemType Directory -Path $BackupFolder -Force
    Write-Host "Created backup folder: $BackupFolder"
}

# Check if source database exists
if (!(Test-Path $SourceDB)) {
    Write-Error "Source database not found: $SourceDB"
    exit 1
}

try {
    # Create zip file containing the database
    Compress-Archive -Path $SourceDB -DestinationPath $backupPath -Force
    
    # Get file sizes for verification
    $sourceSize = (Get-Item $SourceDB).Length
    $backupSize = (Get-Item $backupPath).Length
    
    # Verify backup was created successfully
    if (Test-Path $backupPath) {
        $sourceSizeMB = [math]::Round($sourceSize/1MB, 2)
        $backupSizeMB = [math]::Round($backupSize/1MB, 2)
        
        Write-Host "Database backup successful!"
        Write-Host "Source: $SourceDB ($sourceSizeMB MB)"  
        Write-Host "Backup: $backupPath ($backupSizeMB MB compressed)"
        Write-Host "Timestamp: $(Get-Date)"
    } else {
        Write-Error "Backup verification failed - zip file was not created"
        exit 1
    }
    
    # Clean up old backups (older than retention period)
    $cutoffDate = (Get-Date).AddDays(-$RetentionDays)
    $oldBackups = Get-ChildItem -Path $BackupFolder -Filter "bkup_db_*.zip" | Where-Object { $_.CreationTime -lt $cutoffDate }
    
    if ($oldBackups.Count -gt 0) {
        Write-Host "Cleaning up $($oldBackups.Count) old backups (older than $RetentionDays days)..."
        $oldBackups | ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "Deleted: $($_.Name)"
        }
    } else {
        Write-Host "No old backups to clean up"
    }
    
    # Show current backup inventory
    $allBackups = Get-ChildItem -Path $BackupFolder -Filter "bkup_db_*.zip" | Sort-Object CreationTime -Descending
    
    Write-Host ""
    Write-Host "Current backup inventory ($($allBackups.Count) files):"
    if ($allBackups.Count -gt 0) {
        $allBackups | ForEach-Object {
            try {
                $ageInDays = [math]::Round((Get-Date - $_.CreationTime).TotalDays, 1)
                $sizeMB = [math]::Round($_.Length/1MB, 2)
                Write-Host "$($_.Name) - $sizeMB MB - $ageInDays days old"
            } catch {
                $sizeMB = [math]::Round($_.Length/1MB, 2)
                Write-Host "$($_.Name) - $sizeMB MB - (date error)"
            }
        }
    } else {
        Write-Host "No backup files found"
    }
    
    # Log the backup operation
    $logFile = Join-Path $BackupFolder "backup_log.txt"
    $logBackupSizeMB = [math]::Round($backupSize/1MB, 2)
    $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Backup created: $backupName - Size: $logBackupSizeMB MB"
    Add-Content -Path $logFile -Value $logEntry
    
    Write-Host ""
    Write-Host "Backup operation completed successfully!"
    
} catch {
    Write-Error "Backup failed: $($_.Exception.Message)"
    exit 1
}