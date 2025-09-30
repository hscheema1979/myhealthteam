<#
.SYNOPSIS
    Package and upload database files to GitHub repository

.DESCRIPTION
    This script compresses database files (production.db and related backups) into a zip file
    and uploads them to the GitHub repository with proper commit and push.

.PARAMETER DatabaseName
    Name of the main database file (default: production.db)

.PARAMETER IncludeBackups
    Include backup files in the package (default: $true)

.PARAMETER ZipFileName
    Name of the output zip file (default: database_package_YYYYMMDD_HHMMSS.zip)

.PARAMETER CommitMessage
    Commit message for the upload (default: "Upload database package")

.PARAMETER DryRun
    Perform a dry run without actual commit/push

.EXAMPLE
    .\package_and_upload_db.ps1
    .\package_and_upload_db.ps1 -DatabaseName "staging.db" -IncludeBackups $false
    .\package_and_upload_db.ps1 -DryRun $true
#>

param(
    [string]$DatabaseName = "production.db",
    [bool]$IncludeBackups = $true,
    [string]$ZipFileName = "",
    [string]$CommitMessage = "Upload database package",
    [bool]$DryRun = $false
)

# Set error handling
$ErrorActionPreference = "Stop"

# Configuration
$LogDir = "logs"
$LogFile = "$LogDir\package_and_upload_db.log"
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Create logs directory if it doesn't exist
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Logging function
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

# Function to test if git is available
function Test-GitAvailable {
    try {
        git --version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to check if database file exists
function Test-DatabaseExists {
    param([string]$DbPath)
    return Test-Path $DbPath
}

# Function to create zip package
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
            throw "Main database file not found: $MainDbFile"
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

# Function to commit and push to repository
function Invoke-GitUpload {
    param(
        [string]$ZipFile,
        [string]$Message,
        [bool]$DryRun
    )
    
    Write-Log "Preparing to upload $ZipFile to repository..."
    
    if ($DryRun) {
        Write-Log "DRY RUN: Would execute the following git commands:"
        Write-Log "  git add $ZipFile"
        Write-Log "  git commit -m '$Message'"
        Write-Log "  git push"
        return $true
    }
    
    try {
        # Add file to git
        Write-Log "Adding $ZipFile to git..."
        git add $ZipFile
        if ($LASTEXITCODE -ne 0) { throw "Git add failed" }
        
        # Commit changes
        Write-Log "Committing changes..."
        git commit -m $Message
        if ($LASTEXITCODE -ne 0) { throw "Git commit failed" }
        
        # Push to remote
        Write-Log "Pushing to remote repository..."
        git push
        if ($LASTEXITCODE -ne 0) { throw "Git push failed" }
        
        Write-Log "Upload completed successfully!"
        return $true
        
    } catch {
        Write-Log "Git operation failed: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Main execution
function Main {
    Write-Log "=== Database Package and Upload Script Started ==="
    Write-Log "Parameters: DatabaseName=$DatabaseName, IncludeBackups=$IncludeBackups, DryRun=$DryRun"
    
    # Validate git availability
    if (!(Test-GitAvailable)) {
        Write-Log "Git is not available. Please ensure git is installed and accessible." "ERROR"
        return 1
    }
    
    # Check if main database exists
    if (!(Test-DatabaseExists $DatabaseName)) {
        Write-Log "Database file not found: $DatabaseName" "ERROR"
        Write-Log "Available database files in current directory:"
        Get-ChildItem -Name "*.db*" | ForEach-Object { Write-Log "  $_" }
        return 1
    }
    
    # Generate zip filename if not provided
    if ([string]::IsNullOrEmpty($ZipFileName)) {
        $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $ZipFileName = "database_package_$Timestamp.zip"
    }
    
    # Ensure zip file has .zip extension
    if (!$ZipFileName.EndsWith(".zip")) {
        $ZipFileName += ".zip"
    }
    
    Write-Log "Package will be created as: $ZipFileName"
    
    # Create database package
    $PackageSuccess = New-DatabasePackage -MainDbFile $DatabaseName -IncludeBackups $IncludeBackups -OutputZip $ZipFileName
    
    if (!$PackageSuccess) {
        Write-Log "Failed to create database package" "ERROR"
        return 1
    }
    
    # Upload to repository
    $UploadSuccess = Invoke-GitUpload -ZipFile $ZipFileName -Message $CommitMessage -DryRun $DryRun
    
    if (!$UploadSuccess) {
        Write-Log "Failed to upload package to repository" "ERROR"
        return 1
    }
    
    Write-Log "=== Database Package and Upload Script Completed Successfully ==="
    Write-Log "Package created: $ZipFileName"
    Write-Log "Size: $([math]::Round((Get-Item $ZipFileName).Length / 1MB, 2)) MB"
    
    return 0
}

# Execute main function
$ExitCode = Main
exit $ExitCode