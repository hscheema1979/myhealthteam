# sync_tables.ps1
# Pull specific tables FROM production (VPS2) TO local instance for testing
# Usage: .\sync_tables.ps1 -Tables onboarding_tasks,onboarding_patients

param(
    [Parameter(Mandatory=$false)]
    [string[]]$Tables,  # Comma-separated list of table names

    [switch]$DryRun,
    [switch]$Force,     # Skip confirmation
    [switch]$ListRemote # List all tables on remote instead of syncing
)

$ErrorActionPreference = "Stop"

# Configuration
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path (Split-Path -Parent $scriptDir) "config\db-sync.json"
$config = Get-Content $configPath | ConvertFrom-Json
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Ensure directories exist
$logDir = $config.sync.slave_log_dir
$backupDir = $config.sync.slave_backup_dir
$tempDir = $config.sync.slave_temp_dir

foreach ($dir in @($logDir, $backupDir, $tempDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

$logFile = Join-Path $logDir "table_sync_$timestamp.log"

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

# List all tables on remote
function Get-RemoteTables {
    Write-Log "Fetching table list from production..." "Yellow"
    # Simple query - we'll filter out sqlite_* tables locally
    $tempSql = Join-Path $tempDir "remote_tables_query.sql"
    Set-Content -Path $tempSql -Value 'SELECT name FROM sqlite_master WHERE type="table" ORDER BY name;' -NoNewline

    $tables = Get-Content $tempSql -Raw | ssh $masterHost "sqlite3 $masterDbPath" 2>$null

    # Clean up temp file
    if (Test-Path $tempSql) {
        Remove-Item $tempSql -Force -ErrorAction SilentlyContinue
    }
    return $tables
}

# List all tables locally
function Get-LocalTables {
    # Get all tables and filter out sqlite_* in PowerShell
    $query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
    $tables = sqlite3 $slaveDbPath $query 2>$null
    if ($null -eq $tables) {
        return @()
    }
    # Filter out sqlite_* tables
    return $tables | Where-Object { -not $_.StartsWith('sqlite_') }
}

# Pull a single table from remote
function Sync-TableFromRemote {
    param($TableName)

    Write-Log "Processing: $TableName" "Cyan"

    # Check if table exists remotely - use temp file to avoid escaping issues
    $checkSql = Join-Path $tempDir "check_table.sql"
    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='$TableName';" | Out-File $checkSql -Encoding UTF8 -NoNewline
    $remoteCheck = Get-Content $checkSql -Raw | ssh $masterHost "sqlite3 $masterDbPath" 2>$null
    Remove-Item $checkSql -Force -ErrorAction SilentlyContinue

    if ($remoteCheck -ne "1") {
        Write-Log "  Table '$TableName' does not exist on remote - SKIPPING" "Yellow"
        return $false
    }

    # Check row counts
    $countSql = Join-Path $tempDir "count_rows.sql"
    "SELECT COUNT(*) FROM $TableName;" | Out-File $countSql -Encoding UTF8 -NoNewline
    $remoteCount = Get-Content $countSql -Raw | ssh $masterHost "sqlite3 $masterDbPath" 2>$null
    Remove-Item $countSql -Force -ErrorAction SilentlyContinue

    $localExists = sqlite3 $slaveDbPath "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='$TableName';" 2>$null

    if ($localExists -eq "1") {
        $localCount = sqlite3 $slaveDbPath "SELECT COUNT(*) FROM $TableName;" 2>$null
        Write-Log "  Remote: $remoteCount rows | Local: $localCount rows" "Gray"
    } else {
        Write-Log "  Remote: $remoteCount rows | Local: (table does not exist)" "Gray"
    }

    if ($remoteCount -eq "0") {
        Write-Log "  Remote table is empty - SKIPPING" "Gray"
        return $false
    }

    # Export table from remote using SQLite dump
    $exportFile = Join-Path $tempDir "${TableName}_remote.sql"

    Write-Log "  Exporting from remote..." "Gray"

    # Use sqlite3 dump for the specific table
    # Get the CREATE TABLE statement first (to handle new tables)
    $schemaSql = Join-Path $tempDir "schema.sql"
    ".schema $TableName" | Out-File $schemaSql -Encoding UTF8 -NoNewline
    $createTable = Get-Content $schemaSql -Raw | ssh $masterHost "sqlite3 $masterDbPath" 2>$null
    Remove-Item $schemaSql -Force -ErrorAction SilentlyContinue

    # Then dump the data
    $dataSql = Join-Path $tempDir "data.sql"
    ".mode insert $TableName" | Out-File $dataSql -Encoding UTF8 -NoNewline
    $dataSqlContent = Get-Content $dataSql -Raw
    $dataDump = ($dataSqlContent + "`nSELECT * FROM $TableName;") | ssh $masterHost "sqlite3 $masterDbPath" 2>$null
    Remove-Item $dataSql -Force -ErrorAction SilentlyContinue

    # Build the SQL file
    $sqlContent = @()
    $sqlContent += "-- Synced from production at $timestamp"
    $sqlContent += "-- Table: $TableName"
    $sqlContent += ""

    # If table doesn't exist locally, include CREATE TABLE
    if ($localExists -ne "1") {
        $sqlContent += $createTable
    }

    $sqlContent += ""
    $sqlContent += "BEGIN TRANSACTION;"
    $sqlContent += "-- Delete existing data (preserves table structure)"
    $sqlContent += "DELETE FROM $TableName;"
    $sqlContent += ""

    # Add the INSERT statements
    if ($dataDump) {
        $sqlContent += $dataDump
    }

    $sqlContent += ""
    $sqlContent += "COMMIT;"

    $sqlContent | Out-File -FilePath $exportFile -Encoding UTF8

    $fileSize = [math]::Round((Get-Item $exportFile).Length / 1KB, 1)
    Write-Log "  Export file: $fileSize KB" "Gray"

    if (-not $DryRun) {
        # Import to local database
        Write-Log "  Importing to local database..." "Gray"

        $result = Get-Content $exportFile -Raw | sqlite3 $slaveDbPath 2>&1

        if ($LASTEXITCODE -eq 0) {
            # Verify the import
            $newLocalCount = sqlite3 $slaveDbPath "SELECT COUNT(*) FROM $TableName;" 2>$null
            Write-Log "  SUCCESS: $TableName synced ($newLocalCount rows)" "Green"
            return $true
        } else {
            Write-Log "  FAILED: $result" "Red"
            return $false
        }
    } else {
        Write-Log "  DRY RUN - Would import $remoteCount rows" "Magenta"
        return $true
    }
}

# Main execution
try {
    Write-Log "========================================" "Cyan"
    Write-Log "Table Sync: Remote -> Local" "Cyan"
    Write-Log "========================================" "Cyan"
    Write-Log "Remote: ${masterHost}:${masterDbPath}" "Gray"
    Write-Log "Local:  $slaveDbPath" "Gray"
    Write-Log "" "White"

    # Test SSH connectivity
    Write-Log "Testing SSH connection..." "Yellow"
    $sshTest = ssh -o ConnectTimeout=10 $masterHost "echo 'OK'" 2>&1
    if ($sshTest -ne "OK") {
        throw "SSH connection failed: $sshTest"
    }
    Write-Log "SSH connection: OK" "Green"
    Write-Log "" "White"

    # List remote tables mode
    if ($ListRemote) {
        Write-Log "Tables on remote (production):" "Cyan"
        Write-Log "-----------------------------------" "Gray"

        $remoteTables = Get-RemoteTables
        $localTables = Get-LocalTables

        foreach ($table in $remoteTables) {
            # Skip empty or null entries
            if ([string]::IsNullOrWhiteSpace($table)) { continue }
            # Skip sqlite_* tables
            if ($table.StartsWith('sqlite_')) { continue }

            if ($localTables -contains $table) {
                $remoteCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $table;'" 2>$null
                $localCount = sqlite3 $slaveDbPath "SELECT COUNT(*) FROM $table;" 2>$null
                Write-Log ("  {0,-35} Remote: {1,6} | Local: {2,6}" -f $table, $remoteCount, $localCount) "White"
            } else {
                $remoteCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $table;'" 2>$null
                Write-Log ("  {0,-35} Remote: {1,6} | Local: (none)" -f $table, $remoteCount) "Yellow"
            }
        }

        Write-Log "========================================" "Cyan"
        exit 0
    }

    # Validate tables parameter
    if (-not $Tables) {
        Write-Log "ERROR: -Tables parameter is required (unless using -ListRemote)" "Red"
        Write-Log "Usage: .\sync_tables.ps1 -Tables <table1,table2,...>" "Yellow"
        exit 1
    }

    # Parse table names
    $tableList = $Tables -split ','
    $tableList = $tableList | ForEach-Object { $_.Trim() } | Where-Object { $_ }

    # Validate tables exist remotely before proceeding
    Write-Log "Validating tables on remote..." "Yellow"
    $validTables = @()
    foreach ($tbl in $tableList) {
        # Use temp file to avoid escaping issues
        $checkSql = Join-Path $tempDir "validate_$tbl.sql"
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='$tbl';" | Out-File $checkSql -Encoding UTF8 -NoNewline
        $exists = Get-Content $checkSql -Raw | ssh $masterHost "sqlite3 $masterDbPath" 2>$null
        Remove-Item $checkSql -Force -ErrorAction SilentlyContinue

        if ($exists -eq "1") {
            $validTables += $tbl
        } else {
            Write-Log "  WARNING: Table '$tbl' not found on remote" "Yellow"
        }
    }

    if ($validTables.Count -eq 0) {
        Write-Log "No valid tables to sync!" "Red"
        exit 1
    }

    Write-Log "Found $($validTables.Count) valid table(s) to sync" "Green"
    $validTables | ForEach-Object { Write-Log "  $_" "Gray" }
    Write-Log "" "White"

    # Confirmation prompt
    if (-not $Force -and -not $DryRun) {
        $response = Read-Host "Proceed with sync? (y/N)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            Write-Log "Sync cancelled" "Yellow"
            exit 0
        }
    }

    # Backup local database before sync
    if (-not $DryRun) {
        Write-Log "Creating local backup..." "Yellow"
        $backupName = "production_backup_before_table_sync_$timestamp.db"
        $backupPath = Join-Path $backupDir $backupName
        Copy-Item $slaveDbPath $backupPath -Force
        Write-Log "Backup created: $backupPath" "Green"
        Write-Log "" "White"
    }

    # Sync each table
    $syncedCount = 0
    foreach ($table in $validTables) {
        if (Sync-TableFromRemote -TableName $table) {
            $syncedCount++
        }
        Write-Log "" "White"
    }

    # Summary
    Write-Log "========================================" "Cyan"
    if ($DryRun) {
        Write-Log "DRY RUN Complete" "Magenta"
        Write-Log "Would sync $syncedCount of $($validTables.Count) table(s)" "Magenta"
    } else {
        Write-Log "Sync Complete" "Green"
        Write-Log "Synced $syncedCount of $($validTables.Count) table(s)" "Green"
    }
    Write-Log "Log file: $logFile" "Gray"
    Write-Log "========================================" "Cyan"

} catch {
    Write-Log "========================================" "Red"
    Write-Log "Sync FAILED: $($_.Exception.Message)" "Red"
    Write-Log "========================================" "Red"
    Write-Log "Check log file: $logFile" "Yellow"
    exit 1
}
