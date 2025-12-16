# refresh_production_data.ps1
# One-step workflow to download and import fresh healthcare data

param(
    [switch]$SkipDownload,
    [switch]$SkipBackup,
    [switch]$SkipVerification
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Healthcare Data Refresh Workflow" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Backup production.db
if (-not $SkipBackup) {
    Write-Host "[1/4] Creating backup..." -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupPath = "backups/production_backup_$timestamp.db"

    if (-not (Test-Path "backups")) {
        New-Item -ItemType Directory -Path "backups" | Out-Null
    }

    Copy-Item "production.db" $backupPath -Force
    $backupSize = (Get-Item $backupPath).Length / 1MB
    Write-Host ("  [OK] Backup created: $backupPath ($([math]::Round($backupSize, 2)) MB)`n") -ForegroundColor Green
}
else {
    Write-Host "[1/4] Skipping backup (as requested)`n" -ForegroundColor Gray
}

# Step 2: Backup old CSV files and download fresh data
if (-not $SkipDownload) {
    Write-Host "[2/4] Backing up old CSV files..." -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $csvBackupPath = "old_data/backup_$timestamp"

    if (-not (Test-Path "old_data")) {
        New-Item -ItemType Directory -Path "old_data" | Out-Null
    }

    if (Test-Path "downloads") {
        New-Item -ItemType Directory -Path $csvBackupPath | Out-Null
        Copy-Item "downloads/*" $csvBackupPath -Recurse -Force
        Write-Host "  [OK] CSV files backed up to $csvBackupPath`n" -ForegroundColor Green
    }

    Write-Host "[2/4] Downloading fresh data from Google Sheets..." -ForegroundColor Yellow
    & scripts/1_download_files_complete.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [FAIL] Download failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] Downloaded to downloads/`n" -ForegroundColor Green
}
else {
    Write-Host "[2/4] Skipping download (using existing files)`n" -ForegroundColor Gray
}

# Step 3: Transform and import data
Write-Host "[3/4] Transforming and importing data..." -ForegroundColor Yellow
python transform_production_data_v3_fixed.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [FAIL] Import failed!" -ForegroundColor Red
    Write-Host "`nRollback command: Copy-Item '$backupPath' 'production.db' -Force" -ForegroundColor Yellow
    exit 1
}
Write-Host "  [OK] Import complete`n" -ForegroundColor Green

# Step 4: Post-import processing (views, patient updates, summaries)
Write-Host "[4/4] Running post-import processing..." -ForegroundColor Yellow
Get-Content "src/sql/post_import_processing.sql" | sqlite3 production.db
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Post-import processing had errors" -ForegroundColor Yellow
}
else {
    Write-Host "  [OK] Views created, patient data updated, summaries populated`n" -ForegroundColor Green
}

# Summary
$duration = (Get-Date) - $startTime
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Workflow Complete!" -ForegroundColor Cyan
Write-Host "  Duration: $($duration.ToString('mm\:ss'))" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Launch Streamlit: .\run_and_monitor.ps1" -ForegroundColor Gray
Write-Host "  2. Check dashboards for fresh data" -ForegroundColor Gray
Write-Host "  3. If issues, rollback: Copy-Item '$backupPath' 'production.db' -Force`n" -ForegroundColor Gray
