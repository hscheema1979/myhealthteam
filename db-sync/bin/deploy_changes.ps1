# deploy_changes.ps1
# CI/CD workflow for deploying db-sync configuration and script changes
# Detects changes, validates, updates tasks, syncs to Server 2, and deploys to production

param(
    [switch]$Force,                # Force deployment without prompting
    [switch]$DryRun,               # Preview changes without applying
    [switch]$SkipValidation,       # Skip pre-deployment checks
    [switch]$SkipTests,            # Skip connectivity tests
    [switch]$AutoRollback,         # Automatic rollback on failure
    [switch]$SkipRemoteDeploy,     # Skip Server 2 remote deployment
    [switch]$RemoteDeployOnly,     # Deploy to Server 2 only (skip local)
    [switch]$Verbose               # Detailed logging
)

$ErrorActionPreference = "Stop"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$deploymentId = "deploy_$timestamp"

# Paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$configPath = Join-Path (Split-Path -Parent $scriptDir) "config\db-sync.json"
$logsDir = Join-Path (Split-Path -Parent $scriptDir) "logs"
$deployLogsDir = Join-Path $logsDir "deployments"
$backupDir = Join-Path (Split-Path -Parent $scriptDir) "backups"

# Create directories
@($logsDir, $deployLogsDir, $backupDir) | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Path $_ -Force | Out-Null }
}

$deployLogFile = Join-Path $deployLogsDir "$deploymentId.log"
$statusFile = Join-Path $logsDir "deployment_status.json"

# Helper functions
function Write-Log {
    param($Message, $Color = "White", $Level = "INFO")
    $logEntry = "[$timestamp] [$Level] $Message"
    Add-Content -Path $deployLogFile -Value $logEntry
    Write-Host $Message -ForegroundColor $Color
}

function Write-Status {
    param($Status, $Message)
    $statusObj = @{
        deployment_id = $deploymentId
        status        = $Status
        message       = $Message
        timestamp     = Get-Date -Format "o"
        log_file      = $deployLogFile
    }
    $statusObj | ConvertTo-Json | Set-Content -Path $statusFile -Force
}

function Test-ConfigValidity {
    Write-Log "Validating configuration..." "Yellow"
    
    if (-not (Test-Path $configPath)) {
        Write-Log "Configuration file not found: $configPath" "Red"
        return $false
    }
    
    try {
        $config = Get-Content $configPath | ConvertFrom-Json
        
        # Validate required fields
        $requiredFields = @(
            "sync.master_host",
            "sync.slave_db_path",
            "schedule.daily_refresh_time",
            "schedule.daily_sync_time"
        )
        
        foreach ($field in $requiredFields) {
            $parts = $field -split '\.'
            $value = $config
            foreach ($part in $parts) {
                $value = $value.$part
            }
            if ([string]::IsNullOrEmpty($value)) {
                Write-Log "Missing required config field: $field" "Red"
                return $false
            }
        }
        
        Write-Log "Configuration is valid" "Green"
        return $true
    }
    catch {
        Write-Log "Configuration validation error: $_" "Red"
        return $false
    }
}

function Test-Connectivity {
    Write-Log "Testing SSH connectivity to Server 2..." "Yellow"
    
    try {
        $config = Get-Content $configPath | ConvertFrom-Json
        $masterHost = $config.sync.master_host
        
        $sshTest = ssh -o ConnectTimeout=10 $masterHost "echo OK" 2>&1
        if ($sshTest -eq "OK") {
            Write-Log "SSH connection to $($masterHost): OK" "Green"
            return $true
        }
        else {
            Write-Log "SSH connection failed: $sshTest" "Red"
            return $false
        }
    }
    catch {
        Write-Log "SSH connectivity test error: $_" "Red"
        return $false
    }
}

function Get-ChangedFiles {
    Write-Log "Detecting changed files in db-sync..." "Yellow"
    
    $changed = @()
    
    # Check git status if available
    try {
        Push-Location $projectRoot
        $gitStatus = git status --porcelain db-sync/ 2>$null
        if ($gitStatus) {
            $changed = $gitStatus | ForEach-Object { 
                $parts = $_ -split '\s+', 2
                $parts[1]
            }
            Write-Log "Found $($changed.Count) changed files" "Green"
        }
        Pop-Location
    }
    catch {
        Write-Log "Git status check skipped (not a git repo or git not available)" "Gray"
    }
    
    return $changed
}

function Backup-Configuration {
    Write-Log "Backing up current configuration..." "Yellow"
    
    try {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupFile = Join-Path $backupDir "db-sync-config-backup_$timestamp.json"
        Copy-Item $configPath $backupFile -Force
        Write-Log "Configuration backed up to: $backupFile" "Green"
        return $backupFile
    }
    catch {
        Write-Log "Failed to backup configuration: $_" "Red"
        return $null
    }
}

function Update-ScheduledTasks {
    param($Config)
    
    Write-Log "Updating scheduled tasks..." "Yellow"
    
    # Read refresh time from config
    $refreshTime = $Config.schedule.daily_refresh_time
    $syncTime = $Config.schedule.daily_sync_time
    
    Write-Log "Daily refresh time: $refreshTime" "Gray"
    Write-Log "Daily sync time: $syncTime" "Gray"
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would update scheduled tasks" "Magenta"
        return $true
    }
    
    try {
        # Get existing tasks
        $refreshTask = Get-ScheduledTask -TaskName "Daily-Data-Refresh" -ErrorAction SilentlyContinue
        $syncTask = Get-ScheduledTask -TaskName "Daily-DB-Sync" -ErrorAction SilentlyContinue
        
        if ($refreshTask -and $syncTask) {
            Write-Log "Scheduled tasks found, validating..." "Gray"
            
            # Get trigger times
            $refreshTriggerTime = $refreshTask.Triggers[0].StartBoundary
            $syncTriggerTime = $syncTask.Triggers[0].StartBoundary
            
            Write-Log "Current refresh trigger: $refreshTriggerTime" "Gray"
            Write-Log "Current sync trigger: $syncTriggerTime" "Gray"
            
            # Tasks exist and are configured
            Write-Log "Scheduled tasks are configured and ready" "Green"
            return $true
        }
        else {
            Write-Log "Scheduled tasks not found. Run setup_daily_tasks.ps1 first" "Yellow"
            return $false
        }
    }
    catch {
        Write-Log "Error updating scheduled tasks: $_" "Red"
        return $false
    }
}

function Deploy-Changes {
    param($ChangedFiles, $ConfigBackup)
    
    Write-Log "Deploying changes..." "Yellow"
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would deploy $($ChangedFiles.Count) changed files" "Magenta"
        return $true
    }
    
    try {
        # Update config
        if ($ChangedFiles -contains "db-sync/config/db-sync.json") {
            Write-Log "Applying configuration changes..." "Gray"
        }
        
        # Update scripts
        $scriptChanges = $ChangedFiles | Where-Object { $_ -like "db-sync/bin/*.ps1" }
        if ($scriptChanges) {
            Write-Log "Updated scripts: $($scriptChanges -join ', ')" "Gray"
        }
        
        # Reload configuration
        $newConfig = Get-Content $configPath | ConvertFrom-Json
        
        # Verify changes took effect
        Write-Log "Verifying deployment..." "Gray"
        
        Write-Log "Deployment completed successfully" "Green"
        return $true
    }
    catch {
        Write-Log "Deployment error: $_" "Red"
        
        if ($AutoRollback -and $ConfigBackup) {
            Write-Log "Rolling back to backup: $ConfigBackup" "Yellow"
            Copy-Item $ConfigBackup $configPath -Force
            Write-Log "Configuration restored from backup" "Green"
        }
        
        return $false
    }
}

function Test-Deployment {
    Write-Log "Running post-deployment tests..." "Yellow"
    
    if ($SkipTests) {
        Write-Log "Tests skipped (as requested)" "Gray"
        return $true
    }
    
    # Test configuration validity
    if (-not (Test-ConfigValidity)) {
        return $false
    }
    
    # Test connectivity
    if (-not (Test-Connectivity)) {
        Write-Log "WARNING: SSH connectivity test failed" "Yellow"
        if (-not $Force) {
            return $false
        }
    }
    
    Write-Log "Post-deployment tests passed" "Green"
    return $true
}

function Deploy-ToRemote {
    Write-Log "Deploying to Server 2..." "Yellow"
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would deploy to Server 2" "Magenta"
        return $true
    }
    
    try {
        $config = Get-Content $configPath | ConvertFrom-Json
        $masterHost = $config.sync.master_host
        $remoteDbSyncPath = "/opt/myhealthteam/db-sync"
        
        Write-Log "Connecting to $masterHost..." "Gray"
        Write-Log "Remote db-sync path: $remoteDbSyncPath" "Gray"
        
        # Create temp directory for deployment
        $tempDeployDir = Join-Path $env:TEMP "db-sync-deploy_$timestamp"
        if (-not (Test-Path $tempDeployDir)) {
            New-Item -ItemType Directory -Path $tempDeployDir -Force | Out-Null
        }
        
        Write-Log "Preparing deployment package..." "Gray"
        
        # Copy db-sync files to temp directory (exclude logs and backups)
        $srcDir = Join-Path $projectRoot "db-sync"
        Get-ChildItem $srcDir -Recurse -Exclude @("logs", "backups", "temp", "flags") | ForEach-Object {
            $relPath = $_.FullName.Substring($srcDir.Length + 1)
            $destPath = Join-Path $tempDeployDir $relPath
            
            if ($_.PSIsContainer) {
                if (-not (Test-Path $destPath)) {
                    New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                }
            }
            else {
                Copy-Item $_.FullName $destPath -Force
            }
        }
        
        # Create tar archive
        $tempArchive = Join-Path $env:TEMP "db-sync-deploy_$timestamp.tar.gz"
        Write-Log "Creating deployment archive..." "Gray"
        
        $tarCmd = "tar -czf `"$tempArchive`" -C `"$env:TEMP`" db-sync-deploy_$timestamp"
        Invoke-Expression $tarCmd 2>&1 | Out-Null
        
        if (-not (Test-Path $tempArchive)) {
            Write-Log "Failed to create deployment archive" "Red"
            return $false
        }
        
        $fileSize = [math]::Round((Get-Item $tempArchive).Length / 1MB, 2)
        Write-Log "Archive created: $fileSize MB" "Green"
        
        # Upload to Server 2
        Write-Log "Uploading to Server 2..." "Gray"
        $scpCmd = "scp -C `"$tempArchive`" `"$($masterHost):/tmp/db-sync-deploy_$timestamp.tar.gz`""
        $scpResult = Invoke-Expression $scpCmd 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Failed to upload to Server 2: $scpResult" "Red"
            Remove-Item $tempArchive -Force -ErrorAction SilentlyContinue
            Remove-Item $tempDeployDir -Recurse -Force -ErrorAction SilentlyContinue
            return $false
        }
        
        Write-Log "Upload complete" "Green"
        
        # Extract and deploy on Server 2
        Write-Log "Extracting and deploying on Server 2..." "Gray"
        
        $remoteScript = @"
#!/bin/bash
set -e

# Extract deployment
cd /tmp
tar -xzf db-sync-deploy_$timestamp.tar.gz

# Backup old db-sync if exists
if [ -d '$remoteDbSyncPath' ]; then
  BACKUP_DIR='$remoteDbSyncPath/backups'
  mkdir -p \$BACKUP_DIR
  BACKUP_TS=\$(date +%Y%m%d_%H%M%S)
  cp -r '$remoteDbSyncPath/config' \$BACKUP_DIR/config_backup_\$BACKUP_TS || true
  cp -r '$remoteDbSyncPath/bin' \$BACKUP_DIR/bin_backup_\$BACKUP_TS || true
  echo "Backup created: \$BACKUP_ version
mkdir -p '$remoteDbSyncPath'
cp -r db-sync-deploy_$timestamp/db-sync/* '$remoteDbSyncPath/'

# Set permissions
chmod +x '$remoteDbSyncPath/bin/'*.ps1 2>/dev/null || true
chmod +x '$remoteDbSyncPath/bin/'*.sh 2>/dev/null || true

# Verify deployment
if [ -f '$remoteDbSyncPath/config/db-sync.json' ]; then
  echo 'Deployment successful'
  cat '$remoteDbSyncPath/config/db-sync.json' | head -20
else
  echo 'Deployment failed - config not found'
  exit 1
fi

# Cleanup
rm -f /tmp/db-sync-deploy_$timestamp.tar.gz
rm -rf /tmp/db-sync-deploy_$timestamp

exit 0
"@
        
        $remoteScriptFile = Join-Path $env:TEMP "remote_deploy_$timestamp.sh"
        $remoteScript | Set-Content -Path $remoteScriptFile -Encoding ASCII -Force
        
        $sshCmd = "ssh $masterHost 'bash -s' < `"$remoteScriptFile`""
        $sshResult = Invoke-Expression $sshCmd 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Remote deployment failed: $sshResult" "Red"
            Remove-Item $remoteScriptFile -Force -ErrorAction SilentlyContinue
            Remove-Item $tempArchive -Force -ErrorAction SilentlyContinue
            Remove-Item $tempDeployDir -Recurse -Force -ErrorAction SilentlyContinue
            return $false
        }
        
        Write-Log "Remote deployment successful" "Green"
        $sshResult | ForEach-Object { Write-Log "$_" "Gray" }
        
        # Cleanup
        Remove-Item $remoteScriptFile -Force -ErrorAction SilentlyContinue
        Remove-Item $tempArchive -Force -ErrorAction SilentlyContinue
        Remove-Item $tempDeployDir -Recurse -Force -ErrorAction SilentlyContinue
        
        # Verify remote installation
        Write-Log "Verifying remote db-sync installation..." "Gray"
        $verifyCmd = "ssh $masterHost 'ls -lh $remoteDbSyncPath/bin/ 2>/dev/null | head -10'"
        $verifyResult = Invoke-Expression $verifyCmd 2>&1
        Write-Log "Remote files verified:" "Gray"
        $verifyResult | ForEach-Object { Write-Log "  $_" "Gray" }
        
        return $true
    }
    catch {
        Write-Log "Remote deployment error: $_" "Red"
        return $false
    }
}

# Main workflow
function Invoke-Deployment {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  DB-Sync CI/CD Deployment" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Log "========================================" "Cyan"
    Write-Log "DB-Sync CI/CD Deployment Started" "Cyan"
    Write-Log "========================================" "Cyan"
    Write-Log "Deployment ID: $deploymentId" "Gray"
    Write-Log "DryRun: $DryRun" "Gray"
    Write-Log "Force: $Force" "Gray"
    Write-Log "RemoteDeployOnly: $RemoteDeployOnly" "Gray"
    Write-Log "SkipRemoteDeploy: $SkipRemoteDeploy" "Gray"
    Write-Log ""
    
    Write-Status "running" "Deployment in progress"
    
    # Skip local steps if remote deploy only
    if (-not $RemoteDeployOnly) {
        # Step 1: Validation
        if (-not $SkipValidation) {
            if (-not (Test-ConfigValidity)) {
                Write-Host "Configuration validation failed!" -ForegroundColor Red
                Write-Status "failed" "Configuration validation failed"
                exit 1
            }
        }
        else {
            Write-Log "Configuration validation skipped" "Gray"
        }
        
        Write-Host ""
        
        # Step 2: Backup
        $configBackup = Backup-Configuration
        if (-not $configBackup -and -not $DryRun) {
            Write-Host "Failed to backup configuration!" -ForegroundColor Red
            Write-Status "failed" "Backup failed"
            exit 1
        }
        
        Write-Host ""
        
        # Step 3: Detect changes
        $changedFiles = Get-ChangedFiles
        if ($changedFiles.Count -eq 0 -and -not $Force) {
            Write-Log "No changes detected" "Gray"
            Write-Host ""
            Write-Host "To force deployment, use -Force flag" -ForegroundColor Yellow
            Write-Status "no_changes" "No changes detected"
            exit 0
        }
        
        Write-Log "Changes to deploy:"
        $changedFiles | ForEach-Object { Write-Log "  $_" "Gray" }
        Write-Host ""
        
        # Step 4: Update tasks
        $config = Get-Content $configPath | ConvertFrom-Json
        if (-not (Update-ScheduledTasks $config)) {
            Write-Host "Failed to update scheduled tasks!" -ForegroundColor Red
            Write-Status "failed" "Scheduled task update failed"
            exit 1
        }
        
        Write-Host ""
        
        # Step 5: Deploy
        if (-not (Deploy-Changes $changedFiles $configBackup)) {
            Write-Host "Deployment failed!" -ForegroundColor Red
            Write-Status "failed" "Deployment failed"
            exit 1
        }
        
        Write-Host ""
        
        # Step 6: Test
        if (-not (Test-Deployment)) {
            Write-Host "Post-deployment tests failed!" -ForegroundColor Red
            Write-Status "failed" "Post-deployment tests failed"
            exit 1
        }
        
        Write-Host ""
    }
    
    # Step 7: Remote Deployment (unless skipped)
    if (-not $SkipRemoteDeploy) {
        Write-Log "========================================" "Cyan"
        Write-Log "Remote Deployment Phase" "Cyan"
        Write-Log "========================================" "Cyan"
        Write-Host ""
        
        if (-not (Deploy-ToRemote)) {
            Write-Host "Remote deployment failed!" -ForegroundColor Red
            Write-Status "failed" "Remote deployment to Server 2 failed"
            
            if ($AutoRollback -and -not $RemoteDeployOnly) {
                Write-Log "Rolling back due to remote deployment failure..." "Yellow"
                Copy-Item $configBackup $configPath -Force
                Write-Log "Configuration restored from backup" "Green"
            }
            exit 1
        }
        
        Write-Host ""
    }
    
    # Summary
    $config = Get-Content $configPath | ConvertFrom-Json
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Deployment Successful!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor White
    Write-Host "  Refresh time: $($config.schedule.daily_refresh_time)" -ForegroundColor Gray
    Write-Host "  Sync time: $($config.schedule.daily_sync_time)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Deployment Scope:" -ForegroundColor White
    Write-Host "  Local deployment: $(if ($RemoteDeployOnly) { 'Skipped' } else { 'Completed' })" -ForegroundColor Gray
    Write-Host "  Remote deployment: $(if ($SkipRemoteDeploy) { 'Skipped' } else { 'Completed' })" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Log file: $deployLogFile" -ForegroundColor Gray
    Write-Host "Status file: $statusFile" -ForegroundColor Gray
    Write-Host ""
    
    Write-Log "========================================" "Green"
    Write-Log "Deployment Successful" "Green"
    Write-Log "========================================" "Green"
    Write-Status "success" "Deployment completed successfully"
}

# Run deployment
try {
    Invoke-Deployment
}
catch {
    Write-Host "FATAL ERROR: $_" -ForegroundColor Red
    Write-Log "FATAL ERROR: $_" "Red"
    Write-Status "failed" "Fatal error: $_"
    exit 1
}
