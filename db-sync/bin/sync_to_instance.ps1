# sync_to_instance.ps1
# Simple database file copy - creates DB locally, copies to remote
# Usage:
#   .\sync_to_instance.ps1 -Target test

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("test", "production")]
    [string]$Target
)

$ErrorActionPreference = "Stop"

# Paths
$localDb = "D:\Git\myhealthteam2\Dev\production.db"

# Remote paths
$remotePaths = @{
    test = @{
        host = "server2"
        dbPath = "/opt/test_myhealthteam/production.db"
        service = "myhealthteam-test"
    }
    production = @{
        host = "server2"
        dbPath = "/opt/myhealthteam/production.db"
        service = "myhealthteam"
    }
}

$targetConfig = $remotePaths[$Target]

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Sync to $Target" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check local DB exists
if (-not (Test-Path $localDb)) {
    Write-Host "ERROR: Local database not found: $localDb" -ForegroundColor Red
    exit 1
}

$localSize = [math]::Round((Get-Item $localDb).Length / 1MB, 2)
Write-Host "Local DB: $localDb ($localSize MB)" -ForegroundColor Gray
Write-Host "Target: $($targetConfig.host):$($targetConfig.dbPath)" -ForegroundColor Gray
Write-Host ""

# Confirm
Write-Host "This will:" -ForegroundColor Yellow
Write-Host "  1. Stop remote service" -ForegroundColor Gray
Write-Host "  2. Backup remote DB" -ForegroundColor Gray
Write-Host "  3. Copy local DB to remote" -ForegroundColor Gray
Write-Host "  4. Restart remote service" -ForegroundColor Gray
Write-Host ""

$response = Read-Host "Continue? (y/N)"
if ($response -ne "y") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# Timestamp for backup
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "$($targetConfig.dbPath).backup_$timestamp"

Write-Host "`n[1/4] Stopping service..." -ForegroundColor Yellow
ssh $targetConfig.host "sudo systemctl stop $($targetConfig.service)"

Write-Host "[2/4] Backing up remote DB..." -ForegroundColor Yellow
ssh $targetConfig.host "cp '$($targetConfig.dbPath)' '$backupPath'"

Write-Host "[3/4] Copying local DB to remote..." -ForegroundColor Yellow
scp -C "$localDb" "$($targetConfig.host):$($targetConfig.dbPath)"

Write-Host "[4/4] Restarting service..." -ForegroundColor Yellow
ssh $targetConfig.host "sudo systemctl start $($targetConfig.service)"

# Verify
Write-Host "`nVerifying..." -ForegroundColor Yellow
$status = ssh $targetConfig.host "sudo systemctl is-active $($targetConfig.service)" 2>$null
if ($status -eq "active") {
    Write-Host "Service is running" -ForegroundColor Green
} else {
    Write-Host "WARNING: Service may not be running properly" -ForegroundColor Yellow
    Write-Host "Check with: ssh $($targetConfig.host) 'sudo systemctl status $($targetConfig.service)'" -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backup saved: $backupPath" -ForegroundColor Gray
if ($Target -eq "test") {
    Write-Host "Test instance: https://test.myhealthteam.org" -ForegroundColor Cyan
} else {
    Write-Host "Production: https://care.myhealthteam.org" -ForegroundColor Cyan
}
Write-Host ""
