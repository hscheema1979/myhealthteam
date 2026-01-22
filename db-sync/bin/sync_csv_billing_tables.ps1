# sync_csv_billing_tables.ps1
# Syncs ONLY csv_* billing tables to VPS2
# NEVER touches operational tables (coordinator_tasks_*, provider_tasks_*)
# This ensures live user data (like Laura's entries) on VPS2 is never affected
#
# Usage:
#   .\sync_csv_billing_tables.ps1          # Sync current month
#   .\sync_csv_billing_tables.ps1 -All     # Sync all csv_* tables
#   .\sync_csv_billing_tables.ps1 -DryRun  # Preview what would be synced

param(
    [switch]$DryRun,
    [switch]$All,     # Sync all csv_* tables, not just current month
    [string]$Month    # Specify month as "2025_12"
)

$ErrorActionPreference = "Stop"

# Configuration
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path (Split-Path -Parent $scriptDir) "config\db-sync.json"
$config = Get-Content $configPath | ConvertFrom-Json
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Ensure directories exist
if (-not (Test-Path $config.sync.slave_log_dir)) {
    New-Item -ItemType Directory -Path $config.sync.slave_log_dir -Force | Out-Null
}
if (-not (Test-Path $config.sync.slave_temp_dir)) {
    New-Item -ItemType Directory -Path $config.sync.slave_temp_dir -Force | Out-Null
}

$logFile = Join-Path $config.sync.slave_log_dir "csv_billing_sync_$timestamp.log"

# Logging function
function Write-Log {
    param($Message, $Color = "White")
    $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Add-Content -Path $logFile -Value $logEntry
    Write-Host $Message -ForegroundColor $Color
}

# Connection info
$masterHost = if ($config.sync.master_user) { "$($config.sync.master_user)@$($config.sync.master_host)" } else { $config.sync.master_host }
$masterDbPath = $config.sync.master_db_path
$slaveDbPath = $config.sync.slave_db_path
$tempDir = $config.sync.slave_temp_dir

Write-Log "========================================" "Cyan"
Write-Log "CSV Billing Tables Sync (Safe Mode)" "Cyan"
Write-Log "========================================" "Cyan"
Write-Log "Source: $slaveDbPath" "Gray"
Write-Log "Target: ${masterHost}:${masterDbPath}" "Gray"
Write-Log "Mode: $(if ($DryRun) { 'DRY RUN' } else { 'LIVE' })" "Yellow"
Write-Log "" "White"

Write-Log "SAFETY: Only syncing csv_* tables" "Green"
Write-Log "SAFETY: Operational tables (coordinator_tasks_*, provider_tasks_*) will NOT be touched" "Green"
Write-Log "SAFETY: Live user data on VPS2 is protected" "Green"
Write-Log "" "White"

# Test SSH connectivity first
Write-Log "Testing SSH connection..." "Yellow"
try {
    $sshTest = ssh -o ConnectTimeout=10 $masterHost "echo 'OK'" 2>&1
    if ($sshTest -ne "OK") {
        throw "SSH connection failed: $sshTest"
    }
    Write-Log "SSH connection: OK" "Green"
} catch {
    Write-Log "SSH connection FAILED: $($_.Exception.Message)" "Red"
    exit 1
}

# Get list of csv_* tables to sync
$csvTables = @()

if ($All) {
    # Get ALL csv_* tables
    Write-Log "Discovering all csv_* tables..." "Gray"
    $allTables = sqlite3 $slaveDbPath "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'csv_%' ORDER BY name;" 2>$null
    if ($allTables) {
        $csvTables = $allTables -split "`n" | Where-Object { $_ -match '^csv_' }
    }
} else {
    # Get tables for specified month or current month
    if (-not $Month) {
        $Month = Get-Date -Format "yyyy_MM"
    }
    Write-Log "Looking for csv_* tables for month: $Month" "Gray"

    # Check for csv_coordinator_tasks_YYYY_MM and csv_provider_tasks_YYYY_MM
    $coordinatorTable = "csv_coordinator_tasks_${Month}"
    $providerTable = "csv_provider_tasks_${Month}"

    $coordExists = sqlite3 $slaveDbPath "SELECT name FROM sqlite_master WHERE type='table' AND name='$coordinatorTable';" 2>$null
    $provExists = sqlite3 $slaveDbPath "SELECT name FROM sqlite_master WHERE type='table' AND name='$providerTable';" 2>$null

    if ($coordExists) { $csvTables += $coordinatorTable }
    if ($provExists) { $csvTables += $providerTable }
}

if ($csvTables.Count -eq 0) {
    Write-Log "No csv_* tables found to sync" "Yellow"
    Write-Log "Available csv_* tables:" "Gray"
    $available = sqlite3 $slaveDbPath "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'csv_%' ORDER BY name;" 2>$null
    if ($available) {
        $available -split "`n" | Where-Object { $_ } | ForEach-Object { Write-Log "  $_" "Gray" }
    }
    exit 0
}

Write-Log "Found $($csvTables.Count) csv_* table(s) to sync:" "Green"
$csvTables | ForEach-Object { Write-Log "  $_" "Gray" }
Write-Log "" "White"

$totalRows = 0
$syncedTables = 0
$errors = 0

foreach ($table in $csvTables) {
    Write-Log "Processing: $table" "Yellow"

    # Count rows in this csv table
    $rowCount = sqlite3 $slaveDbPath "SELECT COUNT(*) FROM $table;" 2>$null
    if (-not $rowCount) { $rowCount = 0 }

    Write-Log "  Table has $rowCount rows" "Gray"

    if ([int]$rowCount -eq 0) {
        Write-Log "  Skipping - empty table" "Gray"
        continue
    }

    $exportFile = Join-Path $tempDir "${table}_export.sql"

    Write-Log "  Exporting data..." "Gray"

    # Use sqlite3 .dump which generates CREATE TABLE + INSERT statements
    # We need to prepend DROP TABLE IF EXISTS for clean import
    $dumpOutput = & sqlite3 $slaveDbPath ".dump $table" 2>$null

    if (-not $dumpOutput) {
        Write-Log "  ERROR: Failed to dump $table" "Red"
        $errors++
        continue
    }

    # Prepend DROP TABLE to handle existing tables on target
    $dropStatement = "DROP TABLE IF EXISTS $table;"
    $exportSql = "$dropStatement`n$dumpOutput"

    # Write export file (use UTF8NoBOM to avoid BOM issues)
    [System.IO.File]::WriteAllText($exportFile, $exportSql, [System.Text.Encoding]::UTF8)

    $fileSize = [math]::Round((Get-Item $exportFile).Length / 1KB, 1)
    Write-Log "  Export file: $fileSize KB" "Gray"

    if (-not $DryRun) {
        # Upload to master
        Write-Log "  Uploading to master..." "Gray"
        $remotePath = "/tmp/${table}_import.sql"
        scp -C "$exportFile" "${masterHost}:${remotePath}" 2>&1 | Out-Null

        if ($LASTEXITCODE -ne 0) {
            Write-Log "  FAILED to upload!" "Red"
            $errors++
            Remove-Item $exportFile -Force -ErrorAction SilentlyContinue
            continue
        }

        # Execute on master
        Write-Log "  Executing on master..." "Gray"
        $result = ssh $masterHost "sqlite3 '$masterDbPath' < $remotePath 2>&1" 2>&1

        if ($LASTEXITCODE -eq 0) {
            Write-Log "  SUCCESS: $rowCount rows synced" "Green"
            $totalRows += [int]$rowCount
            $syncedTables++
        } else {
            Write-Log "  FAILED (exit code $LASTEXITCODE)" "Red"
            Write-Log "  Error: $result" "Red"
            $errors++
        }

        # Cleanup remote temp file
        ssh $masterHost "rm -f $remotePath" 2>$null
    } else {
        Write-Log "  DRY RUN - Would sync $rowCount rows" "Magenta"
        $totalRows += [int]$rowCount
        $syncedTables++
    }

    # Cleanup local temp file
    Remove-Item $exportFile -Force -ErrorAction SilentlyContinue
}

Write-Log "" "White"
Write-Log "========================================" "Cyan"
if ($DryRun) {
    Write-Log "DRY RUN Complete" "Magenta"
    Write-Log "Would sync $totalRows rows across $syncedTables table(s)" "Magenta"
} else {
    if ($errors -eq 0) {
        Write-Log "Sync Complete - SUCCESS" "Green"
        Write-Log "Synced $totalRows rows across $syncedTables table(s)" "Green"
    } else {
        Write-Log "Sync Complete with $errors error(s)" "Yellow"
        Write-Log "Synced $totalRows rows across $syncedTables table(s)" "Yellow"
    }
}
Write-Log "Log file: $logFile" "Gray"
Write-Log "========================================" "Cyan"

# Remove trigger file if it exists
$triggerFile = $config.sync.bulk_import_trigger_file
if (Test-Path $triggerFile) {
    Remove-Item $triggerFile -Force
    Write-Log "Trigger file removed" "Gray"
}

exit $(if ($errors -gt 0) { 1 } else { 0 })
