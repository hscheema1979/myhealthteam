# Production Auto-Pull Deployment Script
# Automatically pulls latest changes from GitHub and deploys to production
# Version: 1.0
# Last Updated: $(Get-Date -Format "yyyy-MM-dd")

param(
    [string]$Branch = "main",
    [switch]$SkipBackup = $false,
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

# Configuration
$RepoPath = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$LogFile = Join-Path $RepoPath "logs\production_auto_pull.log"
$ConfigFile = Join-Path $PSScriptRoot "auto_pull_config.json"
$ProductionPort = 8501

# Ensure logs directory exists
$LogDir = Split-Path -Parent $LogFile
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry -ForegroundColor $(
        switch ($Level) {
            "ERROR" { "Red" }
            "WARNING" { "Yellow" }
            "SUCCESS" { "Green" }
            "INFO" { "Cyan" }
            default { "White" }
        }
    )
    Add-Content -Path $LogFile -Value $LogEntry
}

function Test-GitRepository {
    try {
        $gitStatus = git status 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Not a valid git repository" "ERROR"
            return $false
        }
        return $true
    }
    catch {
        Write-Log "Git not available or repository invalid: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Backup-ProductionState {
    if ($SkipBackup) {
        Write-Log "Skipping backup as requested" "WARNING"
        return $true
    }

    try {
        Write-Log "Creating production backup..." "INFO"
        
        # Backup database
        if (Test-Path "production.db") {
            $BackupName = "production_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').db"
            Copy-Item "production.db" "backups\$BackupName"
            Write-Log "Database backed up to: backups\$BackupName" "SUCCESS"
        }

        # Run existing backup script if available
        $BackupScript = "scripts\backup_production_db.py"
        if (Test-Path $BackupScript) {
            python $BackupScript
            Write-Log "Executed backup script: $BackupScript" "SUCCESS"
        }

        return $true
    }
    catch {
        Write-Log "Backup failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Update-FromGitHub {
    try {
        Write-Log "Fetching latest changes from GitHub..." "INFO"
        
        # Fetch latest changes
        git fetch origin 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Git fetch failed" "ERROR"
            return $false
        }

        # Check if there are updates
        $LocalCommit = git rev-parse HEAD
        $RemoteCommit = git rev-parse "origin/$Branch"
        
        if ($LocalCommit -eq $RemoteCommit) {
            Write-Log "Already up to date with origin/$Branch" "INFO"
            return $true
        }

        Write-Log "Updates available. Local: $($LocalCommit.Substring(0,8)), Remote: $($RemoteCommit.Substring(0,8))" "INFO"

        if ($DryRun) {
            Write-Log "DRY RUN: Would update from $($LocalCommit.Substring(0,8)) to $($RemoteCommit.Substring(0,8))" "INFO"
            return $true
        }

        # Reset to remote branch (hard reset)
        Write-Log "Updating to latest version..." "INFO"
        git reset --hard "origin/$Branch" 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Git reset failed" "ERROR"
            return $false
        }

        Write-Log "Successfully updated to commit: $($RemoteCommit.Substring(0,8))" "SUCCESS"
        return $true
    }
    catch {
        Write-Log "GitHub update failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Update-Dependencies {
    try {
        if (Test-Path "requirements.txt") {
            Write-Log "Updating Python dependencies..." "INFO"
            
            if ($DryRun) {
                Write-Log "DRY RUN: Would update dependencies from requirements.txt" "INFO"
                return $true
            }

            pip install -r requirements.txt --upgrade --quiet
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Dependencies updated successfully" "SUCCESS"
            } else {
                Write-Log "Some dependencies may have failed to update" "WARNING"
            }
        } else {
            Write-Log "No requirements.txt found, skipping dependency update" "INFO"
        }
        return $true
    }
    catch {
        Write-Log "Dependency update failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Restart-ProductionApp {
    try {
        Write-Log "Restarting production Streamlit application..." "INFO"
        
        if ($DryRun) {
            Write-Log "DRY RUN: Would restart Streamlit on port $ProductionPort" "INFO"
            return $true
        }

        # Stop existing Streamlit processes
        $StreamlitProcesses = Get-Process -Name "streamlit" -ErrorAction SilentlyContinue
        if ($StreamlitProcesses) {
            Write-Log "Stopping existing Streamlit processes..." "INFO"
            Stop-Process -Name "streamlit" -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 5
        }

        # Start new Streamlit process
        Write-Log "Starting Streamlit on port $ProductionPort..." "INFO"
        $Process = Start-Process -FilePath "streamlit" -ArgumentList "run", "app.py", "--server.port", $ProductionPort -WindowStyle Hidden -PassThru
        
        if ($Process) {
            Write-Log "Streamlit started successfully (PID: $($Process.Id))" "SUCCESS"
            return $true
        } else {
            Write-Log "Failed to start Streamlit process" "ERROR"
            return $false
        }
    }
    catch {
        Write-Log "Application restart failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-ProductionHealth {
    try {
        Write-Log "Performing production health check..." "INFO"
        
        # Wait for application to start
        Start-Sleep -Seconds 10
        
        # Check if Streamlit process is running
        $StreamlitProcess = Get-Process -Name "streamlit" -ErrorAction SilentlyContinue
        if (-not $StreamlitProcess) {
            Write-Log "Streamlit process not running" "ERROR"
            return $false
        }

        # Run health check script if available
        $HealthCheckScript = Join-Path $PSScriptRoot "production_health_check.ps1"
        if (Test-Path $HealthCheckScript) {
            & $HealthCheckScript
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Health check passed" "SUCCESS"
                return $true
            } else {
                Write-Log "Health check failed" "ERROR"
                return $false
            }
        } else {
            Write-Log "Basic health check passed - Streamlit process running" "SUCCESS"
            return $true
        }
    }
    catch {
        Write-Log "Health check failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Main execution
function Invoke-ProductionAutoPull {
    Write-Log "=== Production Auto-Pull Deployment Started ===" "INFO"
    Write-Log "Branch: $Branch, DryRun: $DryRun, SkipBackup: $SkipBackup" "INFO"

    # Change to repository directory
    Set-Location $RepoPath

    # Validate git repository
    if (-not (Test-GitRepository)) {
        Write-Log "Invalid git repository, aborting deployment" "ERROR"
        return $false
    }

    # Step 1: Backup current state
    if (-not (Backup-ProductionState)) {
        Write-Log "Backup failed, aborting deployment" "ERROR"
        return $false
    }

    # Step 2: Update from GitHub
    if (-not (Update-FromGitHub)) {
        Write-Log "GitHub update failed, aborting deployment" "ERROR"
        return $false
    }

    # Step 3: Update dependencies
    if (-not (Update-Dependencies)) {
        Write-Log "Dependency update failed, continuing with deployment" "WARNING"
    }

    # Step 4: Restart application
    if (-not (Restart-ProductionApp)) {
        Write-Log "Application restart failed, deployment may be incomplete" "ERROR"
        return $false
    }

    # Step 5: Health check
    if (-not (Test-ProductionHealth)) {
        Write-Log "Health check failed, deployment may have issues" "WARNING"
    }

    Write-Log "=== Production Auto-Pull Deployment Completed ===" "SUCCESS"
    return $true
}

# Execute main function
try {
    $Success = Invoke-ProductionAutoPull
    if ($Success) {
        Write-Log "Production deployment completed successfully!" "SUCCESS"
        exit 0
    } else {
        Write-Log "Production deployment failed!" "ERROR"
        exit 1
    }
}
catch {
    Write-Log "Unexpected error during deployment: $($_.Exception.Message)" "ERROR"
    exit 1
}