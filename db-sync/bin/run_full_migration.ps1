# run_full_migration.ps1
# Orchestrates the complete VPS2 migration to the new architecture
# This is the MASTER script that runs all phases in order

param(
    [switch]$WhatIf,       # Show what would happen without doing it
    [switch]$SkipBackup,   # Skip backup (NOT RECOMMENDED)
    [switch]$Confirm       # Skip confirmation prompts
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
$backupFile = "$backupDir/production_pre_migration_$timestamp.db"

# Script paths
$phase1Script = Join-Path $scriptDir "migration_phase1_add_source_system.sql"
$phase2Script = Join-Path $scriptDir "migration_phase2_update_views.sql"
$phase3Script = Join-Path $scriptDir "migration_phase3_rebuild_summaries.sql"
$syncScript = Join-Path $scriptDir "sync_csv_billing_tables.ps1"
$cleanupScript = Join-Path $scriptDir "cleanup_vps2_operational_tables.sql"

function Write-Log {
    param($Message, $Color = "White")
    $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Write-Host $Message -ForegroundColor $Color
}

function Invoke-RemoteSql {
    param($SqlContent)
    $tempFile = "/tmp/migration_$([Guid]::NewGuid()).sql"
    $SqlContent | ssh $masterHost "cat > $tempFile"
    $result = ssh $masterHost "sqlite3 '$masterDbPath' < $tempFile 2>&1"
    ssh $masterHost "rm -f $tempFile"
    return $result
}

function Invoke-RemoteSqlFile {
    param($LocalPath)
    $fileName = Split-Path $LocalPath -Leaf
    $remotePath = "/tmp/$fileName"
    scp -C $LocalPath "${masterHost}:${remotePath}" 2>&1 | Out-Null
    $result = ssh $masterHost "sqlite3 '$masterDbPath' < $remotePath 2>&1"
    ssh $masterHost "rm -f $remotePath" 2>$null
    return $result
}

# =============================================================================
# HEADER
# =============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VPS2 Production Migration" -ForegroundColor Cyan
Write-Host "  New Architecture Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target: $masterHost" -ForegroundColor White
Write-Host "Database: $masterDbPath" -ForegroundColor White
Write-Host "Timestamp: $timestamp" -ForegroundColor Gray
Write-Host ""

if ($WhatIf) {
    Write-Host "MODE: WHAT-IF (no changes will be made)" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# PRE-MIGRATION CHECKS
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Pre-Migration Checks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking VPS2 connection..." -ForegroundColor Yellow
$testResult = ssh $masterHost "echo 'OK'" 2>&1
if ($testResult -ne "OK") {
    Write-Host "  FAILED: Cannot connect to VPS2" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: VPS2 is accessible" -ForegroundColor Green

Write-Host "Checking VPS2 database..." -ForegroundColor Yellow
$dbCheck = ssh $masterHost "test -f '$masterDbPath' && echo 'EXISTS' || echo 'MISSING'" 2>$null
if ($dbCheck -ne "EXISTS") {
    Write-Host "  FAILED: Database not found at $masterDbPath" -ForegroundColor Red
    exit 1
}
Write-Host "  OK: Database exists" -ForegroundColor Green

Write-Host "Checking current VPS2 state..." -ForegroundColor Yellow
$coordCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM coordinator_tasks_2026_01;' 2>/dev/null || echo '0'" 2>$null
$provCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM provider_tasks_2026_01;' 2>/dev/null || echo '0'" 2>$null
Write-Host "  coordinator_tasks_2026_01: $coordCount records (Laura's data)" -ForegroundColor Gray
Write-Host "  provider_tasks_2026_01: $provCount records (Laura's data)" -ForegroundColor Gray
Write-Host ""

# =============================================================================
# PHASE 0: BACKUP
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phase 0: Pre-Migration Backup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $SkipBackup) {
    Write-Host "Creating backup on VPS2..." -ForegroundColor Yellow
    Write-Host "  Location: ${masterHost}:${backupFile}" -ForegroundColor Gray

    if (-not $WhatIf) {
        $backupResult = ssh $masterHost "mkdir -p $backupDir && cp '$masterDbPath' '$backupFile' && echo 'OK' || echo 'FAILED'" 2>&1

        if ($backupResult -match 'OK') {
            $backupSize = ssh $masterHost "ls -lh '$backupFile' | awk '{print \$5}'" 2>$null
            Write-Host "  OK: Backup created ($backupSize)" -ForegroundColor Green
            Write-Host ""
            Write-Host "  If migration fails, restore with:" -ForegroundColor Yellow
            Write-Host "    ssh $masterHost 'cp $backupFile $masterDbPath'" -ForegroundColor Gray
            Write-Host "    OR: .\restore_vps2_backup.ps1" -ForegroundColor Gray
        } else {
            Write-Host "  FAILED: Could not create backup" -ForegroundColor Red
            Write-Host "  Error: $backupResult" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "  WHAT-IF: Would create backup at $backupFile" -ForegroundColor Yellow
    }
} else {
    Write-Host "WARNING: Skipping backup (-SkipBackup specified)" -ForegroundColor Red
    Write-Host "  You're on your own if something breaks!" -ForegroundColor Yellow
}

Write-Host ""

# =============================================================================
# PHASE 1: Add source_system Column
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phase 1: Add source_system Column" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will add source_system column to all operational tables:" -ForegroundColor White
Write-Host "  - 2026_01 tables: Mark existing records as 'DASHBOARD' (Laura's data)" -ForegroundColor Gray
Write-Host "  - Pre-2026 tables: Mark existing records as 'CSV_IMPORT' (to be deleted)" -ForegroundColor Gray
Write-Host ""

if (-not $WhatIf) {
    if (-not $Confirm) {
        $response = Read-Host "Proceed with Phase 1? (yes/no)"
        if ($response -ne 'yes') {
            Write-Host "Phase 1 skipped by user" -ForegroundColor Yellow
            exit 0
        }
    }

    Write-Host "Executing Phase 1..." -ForegroundColor Yellow
    $result = Invoke-RemoteSqlFile $phase1Script
    Write-Host $result

    # Verify
    $verifyResult = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT source_system, COUNT(*) FROM coordinator_tasks_2026_01 GROUP BY source_system;'" 2>$null
    Write-Host ""
    Write-Host "Verification (coordinator_tasks_2026_01 by source_system):" -ForegroundColor Yellow
    Write-Host $verifyResult
} else {
    Write-Host "WHAT-IF: Would execute Phase 1" -ForegroundColor Yellow
}

Write-Host ""

# =============================================================================
# PHASE 2: Sync csv_* Tables
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phase 2: Sync csv_* Billing Tables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will:" -ForegroundColor White
Write-Host "  - Create csv_* tables on VPS2 (billing source of truth)" -ForegroundColor Gray
Write-Host "  - Populate them with CSV data from Dev database" -ForegroundColor Gray
Write-Host "  - NOT touch operational tables (Laura's data safe)" -ForegroundColor Green
Write-Host ""

if (-not $WhatIf) {
    if (-not $Confirm) {
        $response = Read-Host "Proceed with Phase 2? (yes/no)"
        if ($response -ne 'yes') {
            Write-Host "Phase 2 skipped by user" -ForegroundColor Yellow
            exit 0
        }
    }

    Write-Host "Executing Phase 2 (syncing csv_* tables)..." -ForegroundColor Yellow
    & $syncScript -All

    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK: csv_* tables synced successfully" -ForegroundColor Green

        # Verify
        $csvCoordCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM csv_coordinator_tasks_2025_12;' 2>/dev/null || echo '0'" 2>$null
        $csvProvCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM csv_provider_tasks_2025_12;' 2>/dev/null || echo '0'" 2>$null
        Write-Host ""
        Write-Host "Verification:" -ForegroundColor Yellow
        Write-Host "  csv_coordinator_tasks_2025_12: $csvCoordCount records" -ForegroundColor Gray
        Write-Host "  csv_provider_tasks_2025_12: $csvProvCount records" -ForegroundColor Gray
    } else {
        Write-Host "FAILED: csv_* sync failed" -ForegroundColor Red
        Write-Host "Consider restoring from backup" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "WHAT-IF: Would sync csv_* tables to VPS2" -ForegroundColor Yellow
}

Write-Host ""

# =============================================================================
# PHASE 3: Update Views
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phase 3: Update Views" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will update coordinator_tasks and provider_tasks views to include 2026_01" -ForegroundColor White
Write-Host ""

if (-not $WhatIf) {
    if (-not $Confirm) {
        $response = Read-Host "Proceed with Phase 3? (yes/no)"
        if ($response -ne 'yes') {
            Write-Host "Phase 3 skipped by user" -ForegroundColor Yellow
            exit 0
        }
    }

    Write-Host "Executing Phase 3..." -ForegroundColor Yellow
    $result = Invoke-RemoteSqlFile $phase2Script
    Write-Host $result
} else {
    Write-Host "WHAT-IF: Would update views" -ForegroundColor Yellow
}

Write-Host ""

# =============================================================================
# PHASE 4: Cleanup Old Data
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phase 4: Cleanup Old Operational Tables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will DELETE all data from pre-2026 operational tables:" -ForegroundColor White
Write-Host "  - coordinator_tasks_2025_* (~28K records)" -ForegroundColor Gray
Write-Host "  - provider_tasks_2025_* (~3K records)" -ForegroundColor Gray
Write-Host "  - provider_tasks_2024_* (~5K records)" -ForegroundColor Gray
Write-Host "  - provider_tasks_2023_* (~800 records)" -ForegroundColor Gray
Write-Host ""
Write-Host "2026_01 tables (Laura's data) will NOT be touched" -ForegroundColor Green
Write-Host ""

if (-not $WhatIf) {
    if (-not $Confirm) {
        $response = Read-Host "Proceed with Phase 4? (yes/no)"
        if ($response -ne 'yes') {
            Write-Host "Phase 4 skipped by user" -ForegroundColor Yellow
            Write-Host "  You can run cleanup later with:" -ForegroundColor Gray
            Write-Host "    ssh $masterHost 'sqlite3 $masterDbPath < cleanup_script.sql'" -ForegroundColor Gray
            exit 0
        }
    }

    Write-Host "Executing Phase 4..." -ForegroundColor Yellow
    $result = Invoke-RemoteSqlFile $cleanupScript
    Write-Host $result
} else {
    Write-Host "WHAT-IF: Would clean up pre-2026 tables" -ForegroundColor Yellow
}

Write-Host ""

# =============================================================================
# PHASE 5: Rebuild Summaries
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Phase 5: Rebuild Billing/Payroll Summaries" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will rebuild billing and payroll summary tables using csv_* as source" -ForegroundColor White
Write-Host ""

if (-not $WhatIf) {
    if (-not $Confirm) {
        $response = Read-Host "Proceed with Phase 5? (yes/no)"
        if ($response -ne 'yes') {
            Write-Host "Phase 5 skipped by user" -ForegroundColor Yellow
            exit 0
        }
    }

    Write-Host "Executing Phase 5..." -ForegroundColor Yellow
    $result = Invoke-RemoteSqlFile $phase3Script
    Write-Host $result
} else {
    Write-Host "WHAT-IF: Would rebuild summaries" -ForegroundColor Yellow
}

Write-Host ""

# =============================================================================
# FINAL VERIFICATION
# =============================================================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Final Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not $WhatIf) {
    Write-Host "Verifying migration results..." -ForegroundColor Yellow
    Write-Host ""

    # Check csv_* tables
    $csvTables = ssh $masterHost "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'csv_%';" 2>$null
    Write-Host "  csv_* tables created: $csvTables" -ForegroundColor Gray

    # Check 2026 operational tables
    $coord2026 = ssh $masterHost "SELECT COUNT(*) FROM coordinator_tasks_2026_01;" 2>$null
    $prov2026 = ssh $masterHost "SELECT COUNT(*) FROM provider_tasks_2026_01;" 2>$null
    Write-Host "  coordinator_tasks_2026_01: $coord2026 records (preserved)" -ForegroundColor Green
    Write-Host "  provider_tasks_2026_01: $prov2026 records (preserved)" -ForegroundColor Green

    # Check summaries
    $summaryCount = ssh $masterHost "SELECT COUNT(*) FROM provider_weekly_summary_with_billing;" 2>$null
    Write-Host "  provider_weekly_summary_with_billing: $summaryCount records" -ForegroundColor Gray

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  Migration Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor White
    Write-Host "  1. Test coordinator dashboard" -ForegroundColor Gray
    Write-Host "  2. Test provider dashboard" -ForegroundColor Gray
    Write-Host "  3. Test billing reports" -ForegroundColor Gray
    Write-Host "  4. Test payroll calculations" -ForegroundColor Gray
    Write-Host ""
    Write-Host "If issues arise, restore backup:" -ForegroundColor Yellow
    Write-Host "  ssh $masterHost 'cp $backupFile $masterDbPath'" -ForegroundColor Gray
    Write-Host "  OR: .\restore_vps2_backup.ps1" -ForegroundColor Gray
    Write-Host ""

} else {
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  What-If Mode Complete" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To run the actual migration:" -ForegroundColor White
    Write-Host "  .\run_full_migration.ps1" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To skip confirmation prompts:" -ForegroundColor White
    Write-Host "  .\run_full_migration.ps1 -Confirm" -ForegroundColor Gray
    Write-Host ""
}
