# refresh_production_data.ps1
# One-step workflow to download and import fresh healthcare data

param(
    [switch]$SkipDownload,
    [switch]$SkipBackup,
    [switch]$SkipVerification,
    [switch]$SyncToProduction  # Sync CSV data to VPS2 after import
)

$ErrorActionPreference = "Stop"
$startTime = Get-Date

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Healthcare Data Refresh Workflow" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Step 1: Backup production.db
if (-not $SkipBackup) {
    Write-Host "[1/5] Creating backup..." -ForegroundColor Yellow
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
    Write-Host "[1/5] Skipping backup (as requested)`n" -ForegroundColor Gray
}

# Step 2: Backup old CSV files and download fresh data
if (-not $SkipDownload) {
    Write-Host "[2/5] Backing up old CSV files..." -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $csvBackupPath = "old_data/backup_$timestamp"

    if (-not (Test-Path "old_data")) {
        New-Item -ItemType Directory -Path "old_data" | Out-Null
    }

    if (Test-Path "downloads") {
        New-Item -ItemType Directory -Path $csvBackupPath | Out-Null
        Copy-Item "downloads/*" $csvBackupPath -Recurse -Force
        Write-Host "  [OK] CSV files backed up to $csvBackupPath`n" -ForegroundColor Green

        # Clear downloads folder to ensure fresh files with current timestamps
        Write-Host "  Clearing downloads folder for fresh data..." -ForegroundColor Gray
        Remove-Item "downloads\*" -Recurse -Force
        Write-Host "  [OK] Downloads folder cleared`n" -ForegroundColor Green
    }

    Write-Host "[2/5] Downloading fresh data from Google Sheets..." -ForegroundColor Yellow
    & scripts/1_download_files_complete.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [FAIL] Download failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] Downloaded to downloads/`n" -ForegroundColor Green

    Write-Host "[2/5] Consolidating CSV files..." -ForegroundColor Yellow
    & scripts/2_consolidate_files.ps1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [FAIL] Consolidation failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] Files consolidated in downloads/`n" -ForegroundColor Green
}
else {
    Write-Host "[2/5] Skipping download (using existing files)`n" -ForegroundColor Gray
}

# Step 3: Transform and import data
Write-Host "[3/5] Transforming and importing data..." -ForegroundColor Yellow
python transform_production_data_v3_fixed.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [FAIL] Import failed!" -ForegroundColor Red
    Write-Host "`nRollback command: Copy-Item '$backupPath' 'production.db' -Force" -ForegroundColor Yellow
    exit 1
}
Write-Host "  [OK] Import complete`n" -ForegroundColor Green

# Step 4: Post-import processing (views, patient updates, summaries)
Write-Host "[4/5] Running post-import processing..." -ForegroundColor Yellow
Get-Content "src/sql/post_import_processing.sql" | sqlite3 production.db
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Post-import processing had errors" -ForegroundColor Yellow
}
else {
    Write-Host "  [OK] Views created, patient data updated, summaries populated`n" -ForegroundColor Green
}

# Step 5: Sync to production (optional)
if ($SyncToProduction) {
    Write-Host "[5/5] Syncing CSV data to production (VPS2)..." -ForegroundColor Yellow
    Write-Host "  Using smart sync (preserves manual entries on VPS2)" -ForegroundColor Gray

    $syncScript = "db-sync\bin\sync_csv_data.ps1"
    if (Test-Path $syncScript) {
        & $syncScript
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] CSV data synced to production`n" -ForegroundColor Green
        }
        else {
            Write-Host "  [WARN] Sync had issues - check db-sync/logs/`n" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "  [WARN] Sync script not found: $syncScript" -ForegroundColor Yellow
        Write-Host "  Creating trigger file for manual sync...`n" -ForegroundColor Gray

        # Create trigger file for next sync cycle
        $triggerDir = "db-sync\flags"
        if (-not (Test-Path $triggerDir)) {
            New-Item -ItemType Directory -Path $triggerDir -Force | Out-Null
        }
        New-Item -ItemType File -Path "$triggerDir\bulk_import_complete.flag" -Force | Out-Null
        Write-Host "  [OK] Trigger file created - sync will run on next scheduled cycle`n" -ForegroundColor Green
    }
}
else {
    Write-Host "[5/5] Skipping production sync (use -SyncToProduction to enable)`n" -ForegroundColor Gray
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
Write-Host "  3. If issues, rollback: Copy-Item '$backupPath' 'production.db' -Force" -ForegroundColor Gray
if (-not $SyncToProduction) {
    Write-Host "  4. To sync to production: .\db-sync\bin\sync_csv_data.ps1" -ForegroundColor Gray
}
Write-Host "" -ForegroundColor White
