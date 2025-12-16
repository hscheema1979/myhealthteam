# Enhanced Hourly Database Backup System
# Automatically backs up production.db with timestamped zip files
# Supports hourly backups with retention policies
# Integrates with GitHub auto-commit for complete backup strategy

param(
    [string]$SourceDB = "D:\Git\myhealthteam2\Streamlit\production.db",
    [string]$BackupFolder = "D:\Git\myhealthteam2\Streamlit\backups",
    [int]$HourlyRetentionHours = 168,  # Keep hourly backups for 7 days
    [int]$DailyRetentionDays = 90,     # Keep daily backups for 90 days
    [int]$WeeklyRetentionWeeks = 26,   # Keep weekly backups for 6 months
    [switch]$EnableGitCommit,
    [string]$GitCommitScript = "D:\Git\myhealthteam2\Streamlit\scripts\auto_git_commit_with_db.ps1"
)

# Enhanced logging function
function Write-EnhancedLog {
    param(
        [string]$Message,
        [string]$Level = "INFO",
        [string]$LogFile = "D:\Git\myhealthteam2\Streamlit\backups\hourly_backup_log.txt"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    # Write to console
    switch ($Level) {
        "ERROR" { Write-Error $Message }
        "WARN" { Write-Warning $Message }
        "SUCCESS" { Write-Host $Message -ForegroundColor Green }
        default { Write-Host $Message }
    }
    
    # Write to log file
    Add-Content -Path $LogFile -Value $logEntry
}

try {
    Write-EnhancedLog "=== Hourly Database Backup Started ===" -Level "INFO"
    
    # Create backup folder if it doesn't exist
    if (!(Test-Path $BackupFolder)) {
        New-Item -ItemType Directory -Path $BackupFolder -Force
        Write-EnhancedLog "Created backup folder: $BackupFolder" -Level "SUCCESS"
    }
    
    # Check if source database exists
    if (!(Test-Path $SourceDB)) {
        throw "Source database not found: $SourceDB"
    }
    
    # Generate timestamp and backup name
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $backupName = "hourly_bkup_db_$timestamp.zip"
    $backupPath = Join-Path $BackupFolder $backupName
    
    Write-EnhancedLog "Creating backup: $backupName" -Level "INFO"
    
    # Create compressed backup
    Compress-Archive -Path $SourceDB -DestinationPath $backupPath -Force
    
    # Verify backup was created successfully
    if (!(Test-Path $backupPath)) {
        throw "Backup verification failed - zip file was not created"
    }
    
    # Get file sizes for verification
    $sourceSize = (Get-Item $SourceDB).Length
    $backupSize = (Get-Item $backupPath).Length
    $sourceSizeMB = [math]::Round($sourceSize/1MB, 2)
    $backupSizeMB = [math]::Round($backupSize/1MB, 2)
    $compressionRatio = [math]::Round((1 - $backupSize/$sourceSize) * 100, 1)
    
    Write-EnhancedLog "Backup created successfully!" -Level "SUCCESS"
    Write-EnhancedLog "Source: $SourceDB ($sourceSizeMB MB)" -Level "INFO"
    Write-EnhancedLog "Backup: $backupPath ($backupSizeMB MB - $compressionRatio% compression)" -Level "INFO"
    
    # Backup cleanup and retention management
    Write-EnhancedLog "Starting retention policy cleanup..." -Level "INFO"
    
    # Get all backup files
    $backupFiles = Get-ChildItem -Path $BackupFolder -Filter "hourly_bkup_db_*.zip" | Sort-Object CreationTime -Descending
    
    if ($backupFiles.Count -gt 0) {
        $currentTime = Get-Date
        
        # Cleanup hourly backups (older than retention period)
        $hourlyRetentionDate = $currentTime.AddHours(-$HourlyRetentionHours)
        $hourlyBackups = $backupFiles | Where-Object { $_.CreationTime -lt $hourlyRetentionDate }
        
        foreach ($oldBackup in $hourlyBackups) {
            Remove-Item -Path $oldBackup.FullName -Force
            Write-EnhancedLog "Removed old hourly backup: $($oldBackup.Name)" -Level "INFO"
        }
        
        # Create daily backup reference for longer retention
        $dailyBackups = $backupFiles | Where-Object {
            $_.CreationTime.Date -eq $currentTime.Date -and
            $_.CreationTime.Hour -eq 23  # Keep the 11 PM backup as daily reference
        }
        
        if ($dailyBackups.Count -eq 0) {
            $dailyBackupName = $backupName -replace "hourly_bkup_db_", "daily_bkup_db_"
            $dailyBackupPath = Join-Path $BackupFolder $dailyBackupName
            Copy-Item -Path $backupPath -Destination $dailyBackupPath -Force
            Write-EnhancedLog "Created daily backup reference: $dailyBackupName" -Level "INFO"
        }
        
        # Cleanup daily backups (older than daily retention period)
        $dailyRetentionDate = $currentTime.AddDays(-$DailyRetentionDays)
        $dailyBackupFiles = Get-ChildItem -Path $BackupFolder -Filter "daily_bkup_db_*.zip"
        $oldDailyBackups = $dailyBackupFiles | Where-Object { $_.CreationTime -lt $dailyRetentionDate }
        
        foreach ($oldBackup in $oldDailyBackups) {
            Remove-Item -Path $oldBackup.FullName -Force
            Write-EnhancedLog "Removed old daily backup: $($oldBackup.Name)" -Level "INFO"
        }
        
        # Cleanup weekly backups (older than weekly retention period) - keep only Sunday backups
        $weeklyRetentionDate = $currentTime.AddDays(-($WeeklyRetentionWeeks * 7))
        $weeklyBackupFiles = Get-ChildItem -Path $BackupFolder -Filter "weekly_bkup_db_*.zip"
        $oldWeeklyBackups = $weeklyBackupFiles | Where-Object { $_.CreationTime -lt $weeklyRetentionDate }
        
        foreach ($oldBackup in $oldWeeklyBackups) {
            Remove-Item -Path $oldBackup.FullName -Force
            Write-EnhancedLog "Removed old weekly backup: $($oldBackup.Name)" -Level "INFO"
        }
    }
    
    Write-EnhancedLog "Retention policy cleanup completed" -Level "SUCCESS"
    
    # GitHub auto-commit (if enabled)
    if ($EnableGitCommit -and (Test-Path $GitCommitScript)) {
        Write-EnhancedLog "Triggering GitHub auto-commit..." -Level "INFO"
        
        try {
            & $GitCommitScript -Message "Hourly backup: $backupName"
            Write-EnhancedLog "GitHub auto-commit completed successfully" -Level "SUCCESS"
        } catch {
            Write-EnhancedLog "GitHub auto-commit failed: $($_.Exception.Message)" -Level "WARN"
        }
    }
    
    # Backup statistics
    $totalBackups = (Get-ChildItem -Path $BackupFolder -Filter "*.zip").Count
    $backupFolderSize = (Get-ChildItem -Path $BackupFolder -Filter "*.zip" | Measure-Object -Property Length -Sum).Sum / 1GB
    $backupFolderSizeGB = [math]::Round($backupFolderSize, 2)
    
    Write-EnhancedLog "=== Backup Summary ===" -Level "INFO"
    Write-EnhancedLog "Current backup: $backupName" -Level "INFO"
    Write-EnhancedLog "Total backup files: $totalBackups" -Level "INFO"
    Write-EnhancedLog "Total backup size: $backupFolderSizeGB GB" -Level "INFO"
    Write-EnhancedLog "=== Hourly Backup Completed Successfully ===" -Level "SUCCESS"
    
    # Exit with success
    exit 0
    
} catch {
    Write-EnhancedLog "Backup failed with error: $($_.Exception.Message)" -Level "ERROR"
    Write-EnhancedLog "Stack trace: $($_.ScriptStackTrace)" -Level "ERROR"
    exit 1
}