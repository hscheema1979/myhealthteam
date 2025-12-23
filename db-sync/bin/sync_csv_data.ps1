# sync_csv_data.ps1
# Smart CSV sync script - syncs only CSV_IMPORT rows, preserves MANUAL/DASHBOARD entries
# This is the recommended script to run after refresh_production_data.ps1

param(
    [switch]$DryRun,
    [string]$Month  # Optional: specify month as "2025_12", defaults to current month
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

$logFile = Join-Path $config.sync.slave_log_dir "csv_sync_$timestamp.log"

# Logging function
function Write-Log {
    param($Message, $Color = "White")
    $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Add-Content -Path $logFile -Value $logEntry
    Write-Host $Message -ForegroundColor $Color
}

# Connection info - use SSH alias directly if no user specified
$masterHost = if ($config.sync.master_user) { "$($config.sync.master_user)@$($config.sync.master_host)" } else { $config.sync.master_host }
$masterDbPath = $config.sync.master_db_path
$slaveDbPath = $config.sync.slave_db_path
$tempDir = $config.sync.slave_temp_dir

# Determine which month to sync
if (-not $Month) {
    $Month = Get-Date -Format "yyyy_MM"
}

Write-Log "========================================" "Cyan"
Write-Log "Smart CSV Sync - $Month" "Cyan"
Write-Log "========================================" "Cyan"
Write-Log "Source: $slaveDbPath" "Gray"
Write-Log "Target: ${masterHost}:${masterDbPath}" "Gray"
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
    Write-Log "Make sure SSH keys are configured. Run:" "Yellow"
    Write-Log "  ssh-keygen -t ed25519 -C 'db-sync@srvr'" "Gray"
    Write-Log "  ssh-copy-id -i ~/.ssh/id_ed25519.pub $masterHost" "Gray"
    exit 1
}

# Get list of task tables for the specified month
$taskTables = @()
foreach ($prefix in $config.tables.task_tables_prefix) {
    $tableName = "${prefix}${Month}"
    # Check if table exists locally
    $exists = sqlite3 $slaveDbPath "SELECT name FROM sqlite_master WHERE type='table' AND name='$tableName';" 2>$null
    if ($exists) {
        $taskTables += $tableName
    }
}

if ($taskTables.Count -eq 0) {
    Write-Log "No task tables found for $Month" "Yellow"
    Write-Log "Available months:" "Gray"
    $available = sqlite3 $slaveDbPath "SELECT DISTINCT name FROM sqlite_master WHERE type='table' AND (name LIKE 'provider_tasks_%' OR name LIKE 'coordinator_tasks_%') ORDER BY name;" 2>$null
    $available | ForEach-Object { Write-Log "  $_" "Gray" }
    exit 0
}

Write-Log "Found $($taskTables.Count) task table(s) to sync:" "Green"
$taskTables | ForEach-Object { Write-Log "  $_" "Gray" }
Write-Log "" "White"

$totalRows = 0
$syncedTables = 0

foreach ($table in $taskTables) {
    Write-Log "Processing: $table" "Yellow"

    # Count rows to sync
    $localCsvCount = sqlite3 $slaveDbPath "SELECT COUNT(*) FROM $table WHERE source_system = 'CSV_IMPORT';" 2>$null
    $localManualCount = sqlite3 $slaveDbPath "SELECT COUNT(*) FROM $table WHERE source_system != 'CSV_IMPORT';" 2>$null

    Write-Log "  Local: $localCsvCount CSV_IMPORT rows, $localManualCount manual rows" "Gray"

    if ([int]$localCsvCount -eq 0) {
        Write-Log "  Skipping - no CSV_IMPORT rows" "Gray"
        continue
    }

    # Export CSV_IMPORT rows
    $exportFile = Join-Path $tempDir "${table}_export.sql"

    Write-Log "  Exporting $localCsvCount rows..." "Gray"

    # Use SQLite's .mode insert for proper escaping of special characters
    # This handles embedded quotes, newlines, and other special chars correctly
    $headerFile = Join-Path $tempDir "${table}_header.sql"
    $dataFile = Join-Path $tempDir "${table}_data.sql"

    # Write header with DELETE statement
    $header = @"
-- Smart CSV Sync Export
-- Table: $table
-- Exported: $timestamp
-- Source: SRVR (Windows)

BEGIN TRANSACTION;

-- Delete old CSV_IMPORT rows (preserves MANUAL/DASHBOARD entries)
DELETE FROM $table WHERE source_system = 'CSV_IMPORT';

-- Insert fresh CSV data
"@
    $header | Out-File -FilePath $headerFile -Encoding UTF8 -NoNewline

    # Use SQLite .mode insert to generate proper INSERT statements with escaping
    $sqliteCmd = @"
.mode insert $table
SELECT * FROM $table WHERE source_system = 'CSV_IMPORT';
"@
    $sqliteCmd | sqlite3 $slaveDbPath 2>$null | Out-File -FilePath $dataFile -Encoding UTF8

    # Combine header + data + footer
    $footer = "`n`nCOMMIT;`n"
    Get-Content $headerFile | Out-File -FilePath $exportFile -Encoding UTF8
    Get-Content $dataFile | Add-Content -Path $exportFile -Encoding UTF8
    $footer | Add-Content -Path $exportFile -Encoding UTF8

    # Cleanup temp files
    Remove-Item $headerFile -Force -ErrorAction SilentlyContinue
    Remove-Item $dataFile -Force -ErrorAction SilentlyContinue

    $fileSize = [math]::Round((Get-Item $exportFile).Length / 1KB, 1)
    Write-Log "  Export file: $fileSize KB" "Gray"

    if (-not $DryRun) {
        # Upload to master
        Write-Log "  Uploading to master..." "Gray"
        scp -C "$exportFile" "${masterHost}:/tmp/${table}_import.sql" 2>&1 | Out-Null

        if ($LASTEXITCODE -ne 0) {
            Write-Log "  FAILED to upload!" "Red"
            continue
        }

        # Execute on master
        Write-Log "  Executing on master..." "Gray"
        $result = ssh $masterHost "sqlite3 '$masterDbPath' < /tmp/${table}_import.sql" 2>&1

        # Check SSH exit code
        if ($LASTEXITCODE -eq 0) {
            # Import succeeded
            Write-Log "  SUCCESS: $localCsvCount rows synced to master" "Green"
            $totalRows += [int]$localCsvCount
            $syncedTables++
        } else {
            Write-Log "  FAILED (exit code $LASTEXITCODE): $result" "Red"
        }

        # Cleanup remote temp file
        ssh $masterHost "rm -f /tmp/${table}_import.sql" 2>$null
    } else {
        Write-Log "  DRY RUN - Would sync $localCsvCount rows" "Magenta"
        $totalRows += [int]$localCsvCount
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
    Write-Log "Sync Complete" "Green"
    Write-Log "Synced $totalRows rows across $syncedTables table(s)" "Green"
}
Write-Log "Log file: $logFile" "Gray"
Write-Log "========================================" "Cyan"

# Remove trigger file if it exists
$triggerFile = $config.sync.bulk_import_trigger_file
if (Test-Path $triggerFile) {
    Remove-Item $triggerFile -Force
    Write-Log "Trigger file removed" "Gray"
}
