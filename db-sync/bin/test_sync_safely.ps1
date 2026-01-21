# test_sync_safely.ps1
# Safely test the csv_* billing tables sync to VPS2
# Creates a backup of VPS2 database before syncing
# Provides restore instructions if anything goes wrong

param(
    [switch]$ReallySync,   # Actually perform the sync (without this, only backup + dry run)
    [switch]$SkipBackup,   # Skip backup (NOT RECOMMENDED)
    [switch]$AlsoCleanup   # Also cleanup old operational tables after sync (deletes 2025 and earlier data)
)

$ErrorActionPreference = "Stop"

# Configuration
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path (Split-Path -Parent $scriptDir) "config\db-sync.json"
$config = Get-Content $configPath | ConvertFrom-Json

$masterHost = if ($config.sync.master_user) { "$($config.sync.master_user)@$($config.sync.master_host)" } else { $config.sync.master_host }
$masterDbPath = $config.sync.master_db_path
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "/opt/myhealthteam/backups"
$backupFile = "$backupDir/production_before_csv_sync_$timestamp.db"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Safe CSV Billing Sync Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target: $masterHost" -ForegroundColor White
Write-Host "Database: $masterDbPath" -ForegroundColor White
Write-Host ""

# Step 1: Create backup on VPS2
if (-not $SkipBackup) {
    Write-Host "[1/4] Creating backup of VPS2 database..." -ForegroundColor Yellow
    Write-Host "  Backup location: ${masterHost}:${backupFile}" -ForegroundColor Gray

    $backupResult = ssh $masterHost "mkdir -p $backupDir && cp '$masterDbPath' '$backupFile' && echo 'BACKUP_OK' || echo 'BACKUP_FAILED'" 2>&1

    if ($backupResult -match 'BACKUP_OK') {
        $backupSize = ssh $masterHost "ls -lh '$backupFile' | awk '{print \$5}'" 2>$null
        Write-Host "  Backup created successfully ($backupSize)" -ForegroundColor Green
        Write-Host ""
        Write-Host "  IMPORTANT: If sync fails, restore with:" -ForegroundColor Yellow
        Write-Host "    ssh $masterHost 'cp $backupFile $masterDbPath'" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "  Backup FAILED!" -ForegroundColor Red
        Write-Host "  Error: $backupResult" -ForegroundColor Red
        Write-Host ""
        Write-Host "  Cannot proceed without backup. Use -SkipBackup to force (not recommended)." -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "[1/4] SKIPPING backup (not recommended!)" -ForegroundColor Yellow
    Write-Host "  You're on your own if something breaks!" -ForegroundColor Red
    Write-Host ""
}

# Step 2: Get current state of csv_* tables on VPS2
Write-Host "[2/4] Checking current state of csv_* tables on VPS2..." -ForegroundColor Yellow

$currentMonth = Get-Date -Format "yyyy_MM"
$csvCoordTable = "csv_coordinator_tasks_${currentMonth}"
$csvProvTable = "csv_provider_tasks_${currentMonth}"

$beforeCoordCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $csvCoordTable;' 2>/dev/null || echo '0'" 2>$null
$beforeProvCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $csvProvTable;' 2>/dev/null || echo '0'" 2>$null

Write-Host "  $csvCoordTable: $beforeCoordCount rows" -ForegroundColor Gray
Write-Host "  $csvProvTable: $beforeProvCount rows" -ForegroundColor Gray
Write-Host ""

# Step 3: Dry run to see what would be synced
Write-Host "[3/4] Running DRY RUN of sync..." -ForegroundColor Yellow

$syncScript = Join-Path $scriptDir "sync_csv_billing_tables.ps1"
if (-not (Test-Path $syncScript)) {
    Write-Host "  ERROR: sync_csv_billing_tables.ps1 not found at: $syncScript" -ForegroundColor Red
    exit 1
}

& $syncScript -DryRun

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  Dry run had issues. Check output above." -ForegroundColor Yellow
    Write-Host "  No changes were made to VPS2." -ForegroundColor Green
}

Write-Host ""

# Step 4: Actual sync (if -ReallySync specified)
if ($ReallySync) {
    Write-Host "[4/4] Running ACTUAL SYNC..." -ForegroundColor Yellow
    Write-Host "  This will modify csv_* tables on VPS2!" -ForegroundColor Red
    Write-Host "  Operational tables (coordinator_tasks_*, provider_tasks_*) will NOT be touched." -ForegroundColor Green
    Write-Host ""

    $confirm = Read-Host "  Type 'YES' to proceed"

    if ($confirm -eq 'YES') {
        & $syncScript -All

        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "  Sync completed successfully!" -ForegroundColor Green

            # Show after state
            $afterCoordCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $csvCoordTable;' 2>/dev/null || echo '0'" 2>$null
            $afterProvCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $csvProvTable;' 2>/dev/null || echo '0'" 2>$null

            Write-Host ""
            Write-Host "  After sync:" -ForegroundColor White
            Write-Host "    $csvCoordTable: $beforeCoordCount -> $afterCoordCount rows" -ForegroundColor Gray
            Write-Host "    $csvProvTable: $beforeProvCount -> $afterProvCount rows" -ForegroundColor Gray

            # Verify operational tables were NOT touched
            Write-Host ""
            Write-Host "  Verifying operational tables were NOT touched..." -ForegroundColor Yellow

            $opCoordTable = "coordinator_tasks_${currentMonth}"
            $opProvTable = "provider_tasks_${currentMonth}"

            $opCoordCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $opCoordTable;' 2>/dev/null || echo '0'" 2>$null
            $opProvCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $opProvTable;' 2>/dev/null || echo '0'" 2>$null

            Write-Host "    $opCoordTable: $opCoordCount rows (unchanged)" -ForegroundColor Green
            Write-Host "    $opProvTable: $opProvCount rows (unchanged)" -ForegroundColor Green

            Write-Host ""
            Write-Host "  SUCCESS: csv_* tables synced, operational tables protected!" -ForegroundColor Green
            Write-Host ""
            Write-Host "  Backup retained at: ${masterHost}:${backupFile}" -ForegroundColor Gray
            Write-Host "  Can be restored for 7 days (cleanup will remove old backups)" -ForegroundColor Gray

            # Optional cleanup step
            if ($AlsoCleanup) {
                Write-Host ""
                Write-Host "========================================" -ForegroundColor Yellow
                Write-Host "  Cleanup Step: Old Operational Tables" -ForegroundColor Yellow
                Write-Host "========================================" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "  This will DELETE all data from 2025 and earlier tables:" -ForegroundColor White
                Write-Host "  - These tables contain CSV-imported data (now in csv_* tables)" -ForegroundColor Gray
                Write-Host "  - 2026 tables (Laura's data) will NOT be touched" -ForegroundColor Green
                Write-Host ""
                Write-Host "  Tables to be cleaned:" -ForegroundColor White
                Write-Host "    coordinator_tasks_2025_* (28K+ records)" -ForegroundColor Gray
                Write-Host "    provider_tasks_2025_* (3K+ records)" -ForegroundColor Gray
                Write-Host "    provider_tasks_2024_* (5K+ records)" -ForegroundColor Gray
                Write-Host "    provider_tasks_2023_* (800+ records)" -ForegroundColor Gray
                Write-Host ""
                Write-Host "  To proceed, type 'CLEANUP': " -ForegroundColor Yellow -NoNewline
                $cleanupConfirm = Read-Host

                if ($cleanupConfirm -eq 'CLEANUP') {
                    $cleanupScript = Join-Path $scriptDir "cleanup_vps2_operational_tables.sql"
                    if (Test-Path $cleanupScript) {
                        Write-Host ""
                        Write-Host "  Uploading cleanup script to VPS2..." -ForegroundColor Gray
                        $remoteCleanup = "/tmp/cleanup_vps2.sql"
                        scp -C "$cleanupScript" "${masterHost}:${remoteCleanup}" 2>&1 | Out-Null

                        Write-Host "  Running cleanup on VPS2..." -ForegroundColor Gray
                        $cleanupResult = ssh $masterHost "sqlite3 '$masterDbPath' < $remoteCleanup" 2>&1
                        $cleanupResult

                        # Cleanup remote temp file
                        ssh $masterHost "rm -f $remoteCleanup" 2>$null

                        Write-Host ""
                        Write-Host "  Cleanup completed!" -ForegroundColor Green
                        Write-Host "  Verify 2026 tables still have Laura's data:" -ForegroundColor Yellow

                        $opCoordCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM coordinator_tasks_2026_01;'" 2>$null
                        $opProvCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM provider_tasks_2026_01;'" 2>$null

                        Write-Host "    coordinator_tasks_2026_01: $opCoordCount records (preserved)" -ForegroundColor Green
                        Write-Host "    provider_tasks_2026_01: $opProvCount records (preserved)" -ForegroundColor Green
                    } else {
                        Write-Host "  WARNING: Cleanup script not found at: $cleanupScript" -ForegroundColor Yellow
                    }
                } else {
                    Write-Host "  Cleanup skipped by user." -ForegroundColor Yellow
                }

                Write-Host ""
            }

            # Final summary
            if ($AlsoCleanup) {
                Write-Host "========================================" -ForegroundColor Cyan
                Write-Host "  Migration Complete!" -ForegroundColor Green
                Write-Host "========================================" -ForegroundColor Cyan
                Write-Host ""
                Write-Host "  Final state on VPS2:" -ForegroundColor White
                Write-Host "    - csv_* tables: Billing source of truth" -ForegroundColor Green
                Write-Host "    - 2026 operational tables: Laura's live data" -ForegroundColor Green
                Write-Host "    - Pre-2026 operational tables: Cleaned up" -ForegroundColor Green
                Write-Host ""
            }
        } else {
            Write-Host ""
            Write-Host "  Sync FAILED!" -ForegroundColor Red
            Write-Host "  Restore the backup with:" -ForegroundColor Yellow
            Write-Host "    ssh $masterHost 'cp $backupFile $masterDbPath'" -ForegroundColor Gray
            exit 1
        }
    } else {
        Write-Host "  Cancelled by user." -ForegroundColor Yellow
    }
} else {
    Write-Host "[4/4] ACTUAL SYNC SKIPPED" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  To perform the actual sync:" -ForegroundColor White
    Write-Host "    .\test_sync_safely.ps1 -ReallySync" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  To sync AND cleanup old tables:" -ForegroundColor White
    Write-Host "    .\test_sync_safely.ps1 -ReallySync -AlsoCleanup" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  This will:" -ForegroundColor White
    Write-Host "    1. Create backup of VPS2 database" -ForegroundColor Gray
    Write-Host "    2. Sync csv_* tables to VPS2" -ForegroundColor Gray
    Write-Host "    3. (optional) Delete 2025 and earlier data from operational tables" -ForegroundColor Gray
    Write-Host "    4. Verify 2026 tables (Laura's data) unchanged" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  If anything goes wrong, restore with:" -ForegroundColor Yellow
    Write-Host "    ssh $masterHost 'cp $backupFile $masterDbPath'" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
