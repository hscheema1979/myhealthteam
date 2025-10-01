<#
.SYNOPSIS
    Enhanced Auto Git Commit Script with Database Packaging

.DESCRIPTION
    This script automatically commits and pushes changes every hour, with optional database packaging.
    It integrates database backup and packaging into the automated workflow.

.PARAMETER CommitMessage
    Custom commit message

.PARAMETER Branch
    Git branch to push to (default: main)

.PARAMETER Force
    Force commit even with no changes

.PARAMETER DryRun
    Perform dry run without actual operations

.PARAMETER IncludeDatabase
    Include database packaging in the workflow

.PARAMETER DatabaseName
    Name of the database file to package

.PARAMETER IncludeBackups
    Include backup files in the package

.EXAMPLE
    .\auto_git_commit_with_db.ps1
    .\auto_git_commit_with_db.ps1 -IncludeDatabase $true -DatabaseName "production.db"
    .\auto_git_commit_with_db.ps1 -DryRun $true
#>

param(
    [string]$CommitMessage = "Automated hourly commit - $(Get-Date -Format 'yyyy-MM-dd HH:mm')",
    [string]$Branch = "main",
    [switch]$Force = $false,
    [switch]$DryRun = $false,
    [bool]$IncludeDatabase = $true,
    [string]$DatabaseName = "production.db",
    [bool]$IncludeBackups = $true
)

# Configuration
$RepoPath = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $RepoPath "logs\auto_git_commit_with_db.log"
$MaxRetries = 3
$RetryDelay = 30  # seconds
$DatabasePackageInterval = 6  # hours - package database every 6 hours

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

function Test-DatabaseExists {
    param([string]$DbPath)
    return Test-Path $DbPath
}

function New-DatabasePackage {
    param(
        [string]$MainDbFile,
        [bool]$IncludeBackups,
        [string]$OutputZip
    )
    
    Write-Log "Creating database package..."
    
    # Create temporary directory for packaging
    $TempDir = "temp_db_package_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    
    try {
        # Copy main database file
        if (Test-DatabaseExists $MainDbFile) {
            Write-Log "Adding main database file: $MainDbFile"
            Copy-Item $MainDbFile "$TempDir\$MainDbFile" -Force
        } else {
            Write-Log "Main database file not found: $MainDbFile" "WARNING"
            return $false
        }
        
        # Copy backup files if requested
        if ($IncludeBackups) {
            Write-Log "Including backup files..."
            $BackupFiles = Get-ChildItem -Path "." -Name "$MainDbFile*" -Exclude "$MainDbFile"
            
            if ($BackupFiles.Count -gt 0) {
                New-Item -ItemType Directory -Path "$TempDir\backups" -Force | Out-Null
                foreach ($Backup in $BackupFiles) {
                    Write-Log "Adding backup file: $Backup"
                    Copy-Item $Backup "$TempDir\backups\$Backup" -Force
                }
            } else {
                Write-Log "No backup files found for $MainDbFile"
            }
        }
        
        # Create package info file
        $PackageInfo = @"
Database Package Information
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Main Database: $MainDbFile
Include Backups: $IncludeBackups
Files Included:
$(Get-ChildItem $TempDir -Recurse | Select-Object -ExpandProperty Name | Out-String)
"@
        Set-Content -Path "$TempDir\package_info.txt" -Value $PackageInfo
        
        # Create zip file
        Write-Log "Creating zip file: $OutputZip"
        Compress-Archive -Path "$TempDir\*" -DestinationPath $OutputZip -Force
        
        Write-Log "Package created successfully: $OutputZip"
        return $true
        
    } finally {
        # Clean up temporary directory
        if (Test-Path $TempDir) {
            Remove-Item $TempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Should-CreateDatabasePackage {
    # Check if it's time to create a database package (every 6 hours)
    $LastPackageFile = "logs\last_db_package_timestamp.txt"
    
    if (!(Test-Path $LastPackageFile)) {
        return $true  # First run
    }
    
    try {
        $LastPackageTime = Get-Content $LastPackageFile | Get-Date
        $CurrentTime = Get-Date
        $TimeDiff = $CurrentTime - $LastPackageTime
        
        return $TimeDiff.TotalHours -ge $DatabasePackageInterval
    } catch {
        Write-Log "Error reading last package timestamp, creating new package" "WARNING"
        return $true
    }
}

function Update-LastPackageTimestamp {
    $LastPackageFile = "logs\last_db_package_timestamp.txt"
    Get-Date -Format "yyyy-MM-dd HH:mm:ss" | Set-Content $LastPackageFile
}

function Invoke-DatabasePackaging {
    if (!$IncludeDatabase) {
        Write-Log "Database packaging disabled" "INFO"
        return $true
    }
    
    if (!(Should-CreateDatabasePackage)) {
        Write-Log "Not time for database packaging yet (interval: $DatabasePackageInterval hours)" "INFO"
        return $true
    }
    
    Write-Log "Starting database packaging process..." "INFO"
    
    # Check if database exists
    if (!(Test-DatabaseExists $DatabaseName)) {
        Write-Log "Database file not found: $DatabaseName" "WARNING"
        return $true  # Continue with regular commit even if DB packaging fails
    }
    
    # Generate zip filename
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $ZipFileName = "database_package_$Timestamp.zip"
    
    Write-Log "Creating database package: $ZipFileName"
    
    # Create database package
    $PackageSuccess = New-DatabasePackage -MainDbFile $DatabaseName -IncludeBackups $IncludeBackups -OutputZip $ZipFileName
    
    if (!$PackageSuccess) {
        Write-Log "Database packaging failed, continuing with regular commit" "WARNING"
        return $true
    }
    
    # Stage the package file
    if (!(Invoke-GitCommand "add $ZipFileName" "Staging database package")) {
        Write-Log "Failed to stage database package" "ERROR"
        return $false
    }
    
    # Update timestamp for next package
    Update-LastPackageTimestamp
    
    Write-Log "Database packaging completed successfully" "SUCCESS"
    return $true
}

function Invoke-AutoGitCommitWithDB {
    Write-Log "Starting automated git commit and push process with database packaging" "INFO"
    Write-Log "Repository: $RepoPath" "INFO"
    Write-Log "Branch: $Branch" "INFO"
    Write-Log "Dry Run: $DryRun" "INFO"
    Write-Log "Include Database: $IncludeDatabase" "INFO"
    Write-Log "Database Name: $DatabaseName" "INFO"
    
    # Verify this is a git repository
    if (!(Test-GitRepository)) {
        Write-Log "Exiting: Not a valid git repository" "ERROR"
        return $false
    }
    
    # Perform database packaging first (if enabled)
    if (!(Invoke-DatabasePackaging)) {
        Write-Log "Database packaging failed, but continuing with regular commit" "WARNING"
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
    
    Write-Log "Automated git commit and push with database packaging completed successfully!" "SUCCESS"
    return $true
}

# Execute main function
$ExitCode = 0
try {
    $Success = Invoke-AutoGitCommitWithDB
    if (!$Success) {
        $ExitCode = 1
    }
} catch {
    Write-Log "Unexpected error: $($_.Exception.Message)" "ERROR"
    $ExitCode = 1
}

exit $ExitCode