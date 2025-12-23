# test_connection.ps1
# Quick test to verify SSH connection and database access on VPS2

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$configPath = Join-Path (Split-Path -Parent $scriptDir) "config\db-sync.json"
$config = Get-Content $configPath | ConvertFrom-Json

$masterHost = if ($config.sync.master_user) { "$($config.sync.master_user)@$($config.sync.master_host)" } else { $config.sync.master_host }
$masterDbPath = $config.sync.master_db_path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DB Sync Connection Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Target: $masterHost" -ForegroundColor White
Write-Host "DB Path: $masterDbPath" -ForegroundColor White
Write-Host ""

# Test 1: SSH Connection
Write-Host "[1/4] Testing SSH connection..." -ForegroundColor Yellow
try {
    $sshResult = ssh -o ConnectTimeout=10 -o BatchMode=yes $masterHost "echo 'OK'" 2>&1
    if ($sshResult -eq "OK") {
        Write-Host "  SSH connection: OK" -ForegroundColor Green
    } else {
        Write-Host "  SSH connection: FAILED" -ForegroundColor Red
        Write-Host "  Error: $sshResult" -ForegroundColor Red
        Write-Host ""
        Write-Host "  To fix, run:" -ForegroundColor Yellow
        Write-Host "    ssh-keygen -t ed25519 -C 'db-sync@srvr'" -ForegroundColor Gray
        Write-Host "    ssh-copy-id -i ~/.ssh/id_ed25519.pub $masterHost" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "  SSH connection: FAILED - $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Database exists
Write-Host "[2/4] Checking database exists..." -ForegroundColor Yellow
$dbExists = ssh $masterHost "test -f '$masterDbPath' && echo 'EXISTS' || echo 'MISSING'" 2>$null
if ($dbExists -eq "EXISTS") {
    Write-Host "  Database file: EXISTS" -ForegroundColor Green
} else {
    Write-Host "  Database file: MISSING" -ForegroundColor Red
    Write-Host "  Path: $masterDbPath" -ForegroundColor Gray
    exit 1
}

# Test 3: SQLite accessible
Write-Host "[3/4] Testing SQLite access..." -ForegroundColor Yellow
$sqliteTest = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM sqlite_master;'" 2>$null
if ($sqliteTest -match '^\d+$') {
    Write-Host "  SQLite access: OK ($sqliteTest tables)" -ForegroundColor Green
} else {
    Write-Host "  SQLite access: FAILED" -ForegroundColor Red
    Write-Host "  Make sure sqlite3 is installed on VPS2" -ForegroundColor Gray
    exit 1
}

# Test 4: Check task tables
Write-Host "[4/4] Checking task tables..." -ForegroundColor Yellow
$currentMonth = Get-Date -Format "yyyy_MM"
$providerTable = "provider_tasks_$currentMonth"
$coordTable = "coordinator_tasks_$currentMonth"

$providerCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $providerTable;'" 2>$null
$coordCount = ssh $masterHost "sqlite3 '$masterDbPath' 'SELECT COUNT(*) FROM $coordTable;'" 2>$null

if ($providerCount -match '^\d+$') {
    Write-Host "  $providerTable : $providerCount rows" -ForegroundColor Green
} else {
    Write-Host "  $providerTable : NOT FOUND (may not exist yet)" -ForegroundColor Yellow
}

if ($coordCount -match '^\d+$') {
    Write-Host "  $coordTable : $coordCount rows" -ForegroundColor Green
} else {
    Write-Host "  $coordTable : NOT FOUND (may not exist yet)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All tests passed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now run:" -ForegroundColor White
Write-Host "  .\sync_csv_data.ps1 -DryRun    # Test sync without changes" -ForegroundColor Gray
Write-Host "  .\sync_csv_data.ps1            # Run actual sync" -ForegroundColor Gray
