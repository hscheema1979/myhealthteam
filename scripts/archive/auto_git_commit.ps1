# Auto Git Commit and Push Script
# This script automatically commits and pushes changes every hour
# Designed to run via Windows Task Scheduler

param(
    [string]$CommitMessage = "Automated hourly commit - $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
    [string]$Branch = "main",
    [switch]$Force = $false,
    [switch]$DryRun = $false
)

# Configuration
$RepoPath = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $RepoPath "logs\auto_git_commit.log"
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

function Get-GitChanges {
    try {
        Push-Location $RepoPath
        $status = git status --porcelain
        $changedFiles = @()
        $untrackedFiles = @()
        $modifiedFiles = @()
        
        foreach ($line in $status) {
            if ($line) {
                $statusCode = $line.Substring(0, 2)
                $filePath = $line.Substring(3)
                
                switch ($statusCode) {
                    "??" { $untrackedFiles += $filePath }
                    "M " { $modifiedFiles += $filePath }
                    " M" { $modifiedFiles += $filePath }
                    "MM" { $modifiedFiles += $filePath }
                    "A " { $modifiedFiles += $filePath }
                    " D" { $modifiedFiles += $filePath }
                    "D " { $modifiedFiles += $filePath }
                }
                $changedFiles += $filePath
            }
        }
        
        return @{
            HasChanges = $changedFiles.Count -gt 0
            ChangedFiles = $changedFiles
            UntrackedFiles = $untrackedFiles
            ModifiedFiles = $modifiedFiles
            Count = $changedFiles.Count
        }
    } catch {
        Write-Log "Error getting git changes: $($_.Exception.Message)" "ERROR"
        return @{ HasChanges = $false; ChangedFiles = @(); Count = 0 }
    } finally {
        Pop-Location
    }
}

function Invoke-GitCommand {
    param(
        [string]$Command,
        [string]$Description,
        [int]$MaxRetries = $MaxRetries
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

function Invoke-AutoGitCommit {
    Write-Log "Starting automated git commit and push process" "INFO"
    Write-Log "Repository: $RepoPath" "INFO"
    Write-Log "Branch: $Branch" "INFO"
    Write-Log "Dry Run: $DryRun" "INFO"
    
    # Verify this is a git repository
    if (!(Test-GitRepository)) {
        Write-Log "Exiting: Not a valid git repository" "ERROR"
        return $false
    }
    
    # Check for changes
    $changes = Get-GitChanges
    
    if (!$changes.HasChanges) {
        Write-Log "No changes detected in repository" "INFO"
        return $true
    }
    
    Write-Log "Found $($changes.Count) changed files:" "INFO"
    foreach ($file in $changes.ChangedFiles) {
        Write-Log "  - $file" "INFO"
    }
    
    # Stage all changes
    if (!(Invoke-GitCommand "add ." "Staging changes")) {
        Write-Log "Failed to stage changes" "ERROR"
        return $false
    }
    
    # Commit changes
    $commitCommand = "commit -m `"$CommitMessage`""
    if ($Force) {
        $commitCommand += " --allow-empty"
    }
    
    if (!(Invoke-GitCommand $commitCommand "Committing changes")) {
        Write-Log "Failed to commit changes" "ERROR"
        return $false
    }
    
    # Push changes
    $pushCommand = "push origin $Branch"
    if (!(Invoke-GitCommand $pushCommand "Pushing to remote")) {
        Write-Log "Failed to push changes" "ERROR"
        return $false
    }
    
    Write-Log "Automated git commit and push completed successfully!" "SUCCESS"
    return $true
}

# Main execution
try {
    Write-Log "========================================" "INFO"
    Write-Log "Auto Git Commit Script Started" "INFO"
    Write-Log "========================================" "INFO"
    
    $success = Invoke-AutoGitCommit
    
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
    Write-Log "Auto Git Commit Script Finished" "INFO"
    Write-Log "========================================" "INFO"
}