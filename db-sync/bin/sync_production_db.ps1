# sync_production_db.ps1
# Database synchronization script for SRVR (Windows) <-> VPS2 (Linux)
# Supports full DB sync and smart CSV-only sync

param(
    [switch]$Force,
    [switch]$Reverse,
    [switch]$DryRun,
    [switch]$CsvOnly  # Use smart CSV sync instead of full DB sync
)

$ErrorActionPreference = "Stop"

# Configuration
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path (Split-Path -Parent $scriptDir) "config\db-sync.json"
$config = Get-Content $configPath | ConvertFrom-Json
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Ensure log directory exists
if (-not (Test-Path $config.sync.slave_log_dir)) {
    New-Item -ItemType Directory -Path $config.sync.slave_log_dir -Force | Out-Null
}
$logFile = Join-Path $config.sync.slave_log_dir "sync_$timestamp.log"

# Logging function
function Write-Log {
    param($Message, $Color = "White")
    $logEntry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - $Message"
    Add-Content -Path $logFile -Value $logEntry
    Write-Host $Message -ForegroundColor $Color
}

# Pre-sync validation
function Test-DatabaseIntegrity {
    param($dbPath, [switch]$Remote)
    try {
        if ($Remote) {
            $sshHost = if ($config.sync.master_user) { "$($config.sync.master_user)@$($config.sync.master_host)" } else { $config.sync.master_host }
            $result = ssh $sshHost "sqlite3 '$dbPath' 'PRAGMA integrity_check;'" 2>$null
        } else {
            $result = sqlite3 $dbPath "PRAGMA integrity_check;" 2>$null
        }
        return $result -eq "ok"
    } catch {
        return $false
    }
}

# Backup database locally
function Backup-Database {
    param($sourcePath, $backupDir)
    if (-not (Test-Path $backupDir)) {
        New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    }
    $backupName = "production_backup_$timestamp.db"
    $backupPath = Join-Path $backupDir $backupName
    Copy-Item $sourcePath $backupPath -Force
    return $backupPath
}

# SSH/SCP Transfer functions - use SSH alias directly if no user specified
$masterHost = if ($config.sync.master_user) { "$($config.sync.master_user)@$($config.sync.master_host)" } else { $config.sync.master_host }
$masterDbPath = $config.sync.master_db_path
$slaveDbPath = $config.sync.slave_db_path

function Sync-MasterToSlave {
    # Pull from master (Linux) to slave (Windows) - FULL DB
    Write-Log "Downloading full database from master..." "Yellow"
    $incomingPath = "${slaveDbPath}.incoming"

    # Use SCP with compression for faster transfer
    scp -C -o ConnectTimeout=30 -o ServerAliveInterval=60 "${masterHost}:${masterDbPath}" $incomingPath

    if ($LASTEXITCODE -ne 0) { throw "SCP download failed" }

    # Validate incoming file
    if (-not (Test-DatabaseIntegrity $incomingPath)) {
        Remove-Item $incomingPath -Force
        throw "Downloaded database failed integrity check"
    }

    # Atomic replace
    Move-Item $incomingPath $slaveDbPath -Force
    Write-Log "Full database synced from master successfully" "Green"
}

function Sync-SlaveToMaster {
    # Push from slave (Windows) to master (Linux) - FULL DB
    Write-Log "Uploading full database to master..." "Yellow"
    $remoteIncoming = "${masterDbPath}.incoming"

    # Upload with compression
    scp -C -o ConnectTimeout=30 -o ServerAliveInterval=60 $slaveDbPath "${masterHost}:${remoteIncoming}"

    if ($LASTEXITCODE -ne 0) { throw "SCP upload failed" }

    # Atomic replace on master
    ssh $masterHost "mv '$remoteIncoming' '$masterDbPath'"

    if ($LASTEXITCODE -ne 0) { throw "Remote file replacement failed" }

    Write-Log "Full database pushed to master successfully" "Green"
}

function Sync-CsvDataToMaster {
    # Smart sync: Only sync CSV_IMPORT rows, preserve MANUAL/DASHBOARD entries
    Write-Log "Starting smart CSV sync (preserves manual entries on master)..." "Cyan"

    $currentMonth = Get-Date -Format "yyyy_MM"
    $tempDir = $config.sync.slave_temp_dir

    if (-not (Test-Path $tempDir)) {
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    }

    # Get list of current month task tables
    $taskTables = @()
    foreach ($prefix in $config.tables.task_tables_prefix) {
        $tableName = "${prefix}${currentMonth}"
        # Check if table exists locally
        $exists = sqlite3 $slaveDbPath "SELECT name FROM sqlite_master WHERE type='table' AND name='$tableName';" 2>$null
        if ($exists) {
            $taskTables += $tableName
        }
    }

    if ($taskTables.Count -eq 0) {
        Write-Log "  No current month task tables found to sync" "Yellow"
        return
    }

    Write-Log "  Found $($taskTables.Count) task tables for $currentMonth" "Gray"

    foreach ($table in $taskTables) {
        Write-Log "  Processing $table..." "Gray"

        # Export CSV_IMPORT rows from local DB
        $exportFile = Join-Path $tempDir "${table}_csv_export.sql"

        # Get column names (excluding auto-increment ID)
        $columns = sqlite3 $slaveDbPath "PRAGMA table_info($table);" 2>$null | ForEach-Object {
            $parts = $_ -split '\|'
            if ($parts[1] -ne "provider_task_id" -and $parts[1] -ne "coordinator_task_id") {
                $parts[1]
            }
        } | Where-Object { $_ }
        $columnList = $columns -join ", "

        # Export as INSERT statements
        $exportQuery = "SELECT '$columnList' AS cols; SELECT $columnList FROM $table WHERE source_system = 'CSV_IMPORT';"
        $rows = sqlite3 $slaveDbPath $exportQuery 2>$null

        if ($rows.Count -le 1) {
            Write-Log "    No CSV_IMPORT rows to sync in $table" "Gray"
            continue
        }

        $rowCount = $rows.Count - 1  # Subtract header row
        Write-Log "    Exporting $rowCount CSV_IMPORT rows..." "Gray"

        # Create SQL file with INSERT statements
        $sqlContent = @()
        $sqlContent += "-- Exported from SRVR at $timestamp"
        $sqlContent += "BEGIN TRANSACTION;"
        $sqlContent += "DELETE FROM $table WHERE source_system = 'CSV_IMPORT';"

        # Skip header row, process data rows
        for ($i = 1; $i -lt $rows.Count; $i++) {
            $values = $rows[$i] -split '\|' | ForEach-Object {
                if ($_ -eq "") { "NULL" }
                else { "'" + ($_ -replace "'", "''") + "'" }
            }
            $sqlContent += "INSERT INTO $table ($columnList) VALUES ($($values -join ', '));"
        }

        $sqlContent += "COMMIT;"
        $sqlContent | Out-File -FilePath $exportFile -Encoding UTF8

        if (-not $DryRun) {
            # Upload SQL file to master
            Write-Log "    Uploading to master..." "Gray"
            scp -C "$exportFile" "${masterHost}:/tmp/${table}_import.sql"

            if ($LASTEXITCODE -ne 0) { throw "Failed to upload $table export" }

            # Execute on master
            Write-Log "    Executing on master (delete CSV_IMPORT, insert fresh)..." "Gray"
            ssh $masterHost "sqlite3 '$masterDbPath' < /tmp/${table}_import.sql && rm /tmp/${table}_import.sql"

            if ($LASTEXITCODE -ne 0) { throw "Failed to import $table on master" }

            Write-Log "    $table synced successfully ($rowCount rows)" "Green"
        } else {
            Write-Log "    DRY RUN - Would sync $rowCount rows" "Magenta"
        }

        # Cleanup temp file
        Remove-Item $exportFile -Force -ErrorAction SilentlyContinue
    }

    Write-Log "Smart CSV sync completed" "Green"
}

# Main sync logic
try {
    Write-Log "========================================" "Cyan"
    Write-Log "Starting database sync at $timestamp" "Cyan"
    Write-Log "========================================" "Cyan"

    # Check for bulk import trigger (reverse sync needed)
    $bulkImportTrigger = $false
    if ($Reverse -or (Test-Path $config.sync.bulk_import_trigger_file)) {
        $bulkImportTrigger = $true
        Write-Log "Bulk import detected - performing reverse sync (Slave -> Master)" "Yellow"
    }

    if ($bulkImportTrigger) {
        # Reverse sync: Slave (dev) -> Master (production)

        # Validate slave database first
        if (-not (Test-DatabaseIntegrity $slaveDbPath)) {
            throw "Slave database integrity check failed"
        }
        Write-Log "Local database integrity: OK" "Green"

        # Backup slave before pushing (in case we need to rollback)
        $localBackup = Backup-Database $slaveDbPath $config.sync.slave_backup_dir
        Write-Log "Local backup created: $localBackup" "Green"

        if (-not $DryRun) {
            if ($CsvOnly) {
                # Smart sync - only CSV data, preserve manual entries
                Sync-CsvDataToMaster
            } else {
                # Full database push (overwrites everything on master)
                Write-Log "WARNING: Full DB push will overwrite all data on master!" "Red"
                Sync-SlaveToMaster
            }

            # Remove trigger file after successful sync
            if (Test-Path $config.sync.bulk_import_trigger_file) {
                Remove-Item $config.sync.bulk_import_trigger_file
                Write-Log "Trigger file removed" "Gray"
            }
        } else {
            Write-Log "DRY RUN - Would push to master" "Magenta"
        }

    } else {
        # Normal sync: Master (production) -> Slave (dev)
        Write-Log "Performing normal sync (Master -> Slave)" "Yellow"

        # Backup slave before sync
        $localBackup = Backup-Database $slaveDbPath $config.sync.slave_backup_dir
        Write-Log "Local backup created: $localBackup" "Green"

        if (-not $DryRun) {
            # Perform normal sync (always full DB pull)
            Sync-MasterToSlave
        } else {
            Write-Log "DRY RUN - Would pull from master" "Magenta"
        }
    }

    # Post-sync validation
    if (Test-DatabaseIntegrity $slaveDbPath) {
        Write-Log "Post-sync integrity check: OK" "Green"
    } else {
        throw "Post-sync integrity check failed"
    }

    Write-Log "========================================" "Cyan"
    Write-Log "Sync completed successfully" "Green"
    Write-Log "========================================" "Cyan"

} catch {
    Write-Log "========================================" "Red"
    Write-Log "Sync FAILED: $($_.Exception.Message)" "Red"
    Write-Log "========================================" "Red"
    Write-Log "Check log file: $logFile" "Yellow"
    exit 1
}
