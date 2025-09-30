# swap_database.ps1
# Script to safely swap the production database with the updated database

param(
    [string]$ProductionDB = "..\production.db",
    [string]$UpdateDB = "..\update_data.db",
    [string]$BackupSuffix = "_backup_$(Get-Date -Format 'yyyy-MM-dd_HH-mm-ss')"
)

# Function to check if a file is locked
function Test-FileLock {
    param(
        [string]$Path
    )
    
    if (-not (Test-Path $Path)) {
        return $false
    }
    
    try {
        $file = [System.IO.File]::Open($Path, 'Open', 'Write')
        $file.Close()
        return $false
    }
    catch {
        # File is locked
        return $true
    }
}

Write-Host "Database Swap Process Starting..." -ForegroundColor Yellow
Write-Host "Production DB: $ProductionDB" -ForegroundColor Yellow
Write-Host "Update DB: $UpdateDB" -ForegroundColor Yellow
Write-Host "Backup Suffix: $BackupSuffix" -ForegroundColor Yellow

# Check if update database exists
if (-not (Test-Path $UpdateDB)) {
    Write-Host "Error: Update database '$UpdateDB' not found." -ForegroundColor Red
    exit 1
}

# Check if production database exists
if (-not (Test-Path $ProductionDB)) {
    Write-Host "Error: Production database '$ProductionDB' not found." -ForegroundColor Red
    exit 1
}

# Check if production database is locked
if (Test-FileLock $ProductionDB) {
    Write-Host "Error: Production database '$ProductionDB' is currently locked. Please stop all applications using it." -ForegroundColor Red
    exit 1
}

# Create backup of production database
$backupDB = "$ProductionDB$BackupSuffix"
$backupDBWal = "$backupDB-WAL"
$backupDBShm = "$backupDB-SHM"

Write-Host "Creating backup of production database..." -ForegroundColor Green
try {
    Copy-Item $ProductionDB $backupDB -Force
    Write-Host "Backup created: $backupDB" -ForegroundColor Green
    
    # Also backup WAL and SHM files if they exist
    if (Test-Path "$ProductionDB-WAL") {
        Copy-Item "$ProductionDB-WAL" $backupDBWal -Force
        Write-Host "Backup created: $backupDBWal" -ForegroundColor Green
    }
    
    if (Test-Path "$ProductionDB-SHM") {
        Copy-Item "$ProductionDB-SHM" $backupDBShm -Force
        Write-Host "Backup created: $backupDBShm" -ForegroundColor Green
    }
}
catch {
    $errorMessage = "Error creating backup: " + $_.Exception.Message
    Write-Host $errorMessage -ForegroundColor Red
    exit 1
}

# Perform the swap
Write-Host "Swapping databases..." -ForegroundColor Green
try {
    # Remove existing production database files
    Remove-Item $ProductionDB -Force -ErrorAction SilentlyContinue
    Remove-Item "$ProductionDB-WAL" -Force -ErrorAction SilentlyContinue
    Remove-Item "$ProductionDB-SHM" -Force -ErrorAction SilentlyContinue
    
    # Rename update database to production database
    Move-Item $UpdateDB $ProductionDB -Force
    Write-Host "Database swap completed successfully!" -ForegroundColor Green
    
    # Also move WAL and SHM files if they exist
    if (Test-Path "$UpdateDB-WAL") {
        Move-Item "$UpdateDB-WAL" "$ProductionDB-WAL" -Force
        Write-Host "Moved WAL file" -ForegroundColor Green
    }
    
    if (Test-Path "$UpdateDB-SHM") {
        Move-Item "$UpdateDB-SHM" "$ProductionDB-SHM" -Force
        Write-Host "Moved SHM file" -ForegroundColor Green
    }
}
catch {
    $errorMessage = "Error swapping databases: " + $_.Exception.Message
    Write-Host $errorMessage -ForegroundColor Red
    
    # Try to restore from backup
    Write-Host "Attempting to restore from backup..." -ForegroundColor Yellow
    try {
        Move-Item $backupDB $ProductionDB -Force
        if (Test-Path $backupDBWal) {
            Move-Item $backupDBWal "$ProductionDB-WAL" -Force
        }
        if (Test-Path $backupDBShm) {
            Move-Item $backupDBShm "$ProductionDB-SHM" -Force
        }
        Write-Host "Restored from backup successfully" -ForegroundColor Green
    }
    catch {
        $restoreError = "Failed to restore from backup: " + $_.Exception.Message
        Write-Host $restoreError -ForegroundColor Red
    }
    
    exit 1
}

Write-Host "Database swap process completed successfully!" -ForegroundColor Green
Write-Host "Backup location: $backupDB" -ForegroundColor Green