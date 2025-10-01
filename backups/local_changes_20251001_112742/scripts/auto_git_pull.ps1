# Auto Git Pull Script for Production Environment
# This script automatically pulls changes from the remote repository
# Designed to run via Windows Task Scheduler

param(
    [string]$Branch = "main",
    [switch]$DryRun = $false,
    [switch]$Force = $false
)

# Configuration
$RepoPath = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $RepoPath "logs\auto_git_pull.log"
$MaxRetries = 3
$RetryDelay = 30  # seconds

# Ensure logs directory exists
$LogDir = Split-Path -Parent $LogFile
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

function Test-GitRepository {
    try {
        Push-Location $RepoPath
        $gitStatus = git status 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            Write-Log "Not a valid git repository or git not available" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Error testing git repository: $($_.Exception.Message)" "ERROR"
        return $false
    } finally {
        Pop-Location
    }
}

function Invoke-GitCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    $attempt = 1
    while ($attempt -le $MaxRetries) {
        try {
            Write-Log "Executing: git $Command (Attempt $attempt of $MaxRetries)"
            
            if ($DryRun) {
                Write-Log "DRY RUN: Would execute: git $Command" "WARNING"
                return $true
            }
            
            Push-Location $RepoPath
            
            # Split command into arguments for proper execution
            $arguments = $Command -split ' '
            $output = & git @arguments 2>&1
            $exitCode = $LASTEXITCODE
            
            if ($exitCode -eq 0) {
                Write-Log "$Description successful" "SUCCESS"
                if ($output) {
                    Write-Log "Output: $output" "INFO"
                }
                return $true
            } else {
                Write-Log "$Description failed with exit code $exitCode" "ERROR"
                if ($output) {
                    Write-Log "Output: $output" "ERROR"
                }
                
                if ($attempt -lt $MaxRetries) {
                    Write-Log "Retrying in $RetryDelay seconds..." "WARNING"
                    Start-Sleep -Seconds $RetryDelay
                }
            }
        } catch {
            Write-Log "Error during $Description`: $($_.Exception.Message)" "ERROR"
            if ($attempt -lt $MaxRetries) {
                Write-Log "Retrying in $RetryDelay seconds..." "WARNING"
                Start-Sleep -Seconds $RetryDelay
            }
        } finally {
            Pop-Location
        }
        
        $attempt++
    }
    
    Write-Log "$Description failed after $MaxRetries attempts" "ERROR"
    return $false
}

function Get-LocalChanges {
    try {
        Push-Location $RepoPath
        $status = git status --porcelain 2>&1
        if ($LASTEXITCODE -eq 0) {
            $changes = $status | Where-Object { $_ -ne "" }
            return @{
                HasChanges = ($changes.Count -gt 0)
                Count = $changes.Count
                ChangedFiles = $changes
            }
        } else {
            Write-Log "Failed to get git status" "ERROR"
            return @{ HasChanges = $false; Count = 0; ChangedFiles = @() }
        }
    } catch {
        Write-Log "Error getting git status: $($_.Exception.Message)" "ERROR"
        return @{ HasChanges = $false; Count = 0; ChangedFiles = @() }
    } finally {
        Pop-Location
    }
}

function Backup-LocalChanges {
    param([array]$ChangedFiles)
    
    $backupDir = Join-Path $RepoPath "backups\local_changes_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    
    try {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
        Write-Log "Created backup directory: $backupDir" "INFO"
        
        foreach ($file in $ChangedFiles) {
            $fileName = $file -replace '^..\s*', ''  # Remove git status prefix
            $sourcePath = Join-Path $RepoPath $fileName
            $destPath = Join-Path $backupDir $fileName
            
            if (Test-Path $sourcePath) {
                $destDir = Split-Path -Parent $destPath
                if (!(Test-Path $destDir)) {
                    New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                }
                Copy-Item -Path $sourcePath -Destination $destPath -Force
                Write-Log "Backed up: $fileName" "INFO"
            }
        }
        
        return $backupDir
    } catch {
        Write-Log "Error creating backup: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

function Invoke-AutoGitPull {
    Write-Log "Starting automated git pull process" "INFO"
    Write-Log "Repository: $RepoPath" "INFO"
    Write-Log "Branch: $Branch" "INFO"
    Write-Log "Dry Run: $DryRun" "INFO"
    
    # Verify this is a git repository
    if (!(Test-GitRepository)) {
        Write-Log "Exiting: Not a valid git repository" "ERROR"
        return $false
    }
    
    # Check for local changes
    $localChanges = Get-LocalChanges
    
    if ($localChanges.HasChanges) {
        Write-Log "Found $($localChanges.Count) local changes:" "WARNING"
        foreach ($file in $localChanges.ChangedFiles) {
            Write-Log "  - $file" "WARNING"
        }
        
        # Backup local changes
        $backupPath = Backup-LocalChanges -ChangedFiles $localChanges.ChangedFiles
        if ($backupPath) {
            Write-Log "Local changes backed up to: $backupPath" "INFO"
        }
        
        # Stash local changes
        if (!(Invoke-GitCommand "stash push -m `"Auto-stash before pull $(Get-Date -Format 'yyyy-MM-dd HH:mm')`"" "Stashing local changes")) {
            Write-Log "Failed to stash local changes" "ERROR"
            return $false
        }
    } else {
        Write-Log "No local changes detected" "INFO"
    }
    
    # Fetch latest changes
    if (!(Invoke-GitCommand "fetch origin" "Fetching from remote")) {
        Write-Log "Failed to fetch from remote" "ERROR"
        return $false
    }
    
    # Check if there are updates available
    try {
        Push-Location $RepoPath
        $behind = git rev-list --count HEAD..origin/$Branch 2>&1
        if ($LASTEXITCODE -eq 0 -and $behind -gt 0) {
            Write-Log "Repository is $behind commits behind origin/$Branch" "INFO"
        } elseif ($LASTEXITCODE -eq 0 -and $behind -eq 0) {
            Write-Log "Repository is up to date with origin/$Branch" "INFO"
            return $true
        } else {
            Write-Log "Could not determine if updates are available" "WARNING"
        }
    } catch {
        Write-Log "Error checking for updates: $($_.Exception.Message)" "WARNING"
    } finally {
        Pop-Location
    }
    
    # Pull changes
    $pullCommand = "pull origin $Branch"
    if ($Force) {
        $pullCommand = "reset --hard origin/$Branch"
        Write-Log "Using force reset instead of pull" "WARNING"
    }
    
    if (!(Invoke-GitCommand $pullCommand "Pulling from remote")) {
        Write-Log "Failed to pull changes" "ERROR"
        return $false
    }
    
    Write-Log "Automated git pull completed successfully!" "SUCCESS"
    return $true
}

# Main execution
try {
    Write-Log "========================================" "INFO"
    Write-Log "Auto Git Pull Script Started" "INFO"
    Write-Log "========================================" "INFO"
    
    $success = Invoke-AutoGitPull
    
    if ($success) {
        Write-Log "Script completed successfully" "SUCCESS"
        exit 0
    } else {
        Write-Log "Script completed with errors" "ERROR"
        exit 1
    }
} catch {
    Write-Log "Unexpected error: $($_.Exception.Message)" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
} finally {
    Write-Log "========================================" "INFO"
    Write-Log "Auto Git Pull Script Finished" "INFO"
    Write-Log "========================================" "INFO"
}