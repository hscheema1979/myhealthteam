# setup_daily_tasks.ps1
# Creates Windows Scheduled Tasks for daily data refresh and sync
# Task 1: 5:00 AM - Download CSVs and import to production.db
# Task 2: 6:30 AM - Sync CSV data to Server 2

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setting up Daily Sync Schedule" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)
$refreshScript = Join-Path $projectRoot "refresh_production_data.ps1"
$syncScript = Join-Path $scriptDir "sync_csv_data.ps1"

# Verify scripts exist
if (-not (Test-Path $refreshScript)) {
    Write-Host "ERROR: refresh_production_data.ps1 not found at: $refreshScript" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $syncScript)) {
    Write-Host "ERROR: sync_csv_data.ps1 not found at: $syncScript" -ForegroundColor Red
    exit 1
}

# Task 1: Daily Refresh at 5:00 AM
$task1Name = "Daily-Data-Refresh"
$task1Desc = "Download latest CSVs and import to local production.db (5:00 AM daily)"

Write-Host "Creating Task 1: $task1Name" -ForegroundColor Yellow
Write-Host "  Script: $refreshScript" -ForegroundColor Gray
Write-Host "  Time: 5:00 AM daily" -ForegroundColor Gray
Write-Host "  Options: -SkipBackup -SyncToProduction" -ForegroundColor Gray
Write-Host ""

try {
    $existingTask1 = Get-ScheduledTask -TaskName $task1Name -ErrorAction SilentlyContinue
    if ($existingTask1) {
        Write-Host "  Task already exists, removing..." -ForegroundColor Gray
        Unregister-ScheduledTask -TaskName $task1Name -Confirm:$false | Out-Null
    }

    $action1 = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$refreshScript`" -SkipBackup -SyncToProduction"
    
    $trigger1 = New-ScheduledTaskTrigger -Daily -At "05:00"
    
    $settings1 = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -DontStopOnIdleEnd `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew
    
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    
    Register-ScheduledTask `
        -TaskName $task1Name `
        -Action $action1 `
        -Trigger $trigger1 `
        -Settings $settings1 `
        -Principal $principal `
        -Description $task1Desc | Out-Null
    
    Write-Host "  [OK] Task created successfully" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] Could not create task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Task 2: Daily Sync at 6:30 AM
$task2Name = "Daily-DB-Sync"
$task2Desc = "Sync CSV data from local production.db to Server 2 (6:30 AM daily)"

Write-Host "Creating Task 2: $task2Name" -ForegroundColor Yellow
Write-Host "  Script: $syncScript" -ForegroundColor Gray
Write-Host "  Time: 6:30 AM daily" -ForegroundColor Gray
Write-Host "  Purpose: Push refreshed data to production Server 2" -ForegroundColor Gray
Write-Host ""

try {
    $existingTask2 = Get-ScheduledTask -TaskName $task2Name -ErrorAction SilentlyContinue
    if ($existingTask2) {
        Write-Host "  Task already exists, removing..." -ForegroundColor Gray
        Unregister-ScheduledTask -TaskName $task2Name -Confirm:$false | Out-Null
    }

    $action2 = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$syncScript`""
    
    $trigger2 = New-ScheduledTaskTrigger -Daily -At "06:30"
    
    $settings2 = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -DontStopOnIdleEnd `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew
    
    Register-ScheduledTask `
        -TaskName $task2Name `
        -Action $action2 `
        -Trigger $trigger2 `
        -Settings $settings2 `
        -Principal $principal `
        -Description $task2Desc | Out-Null
    
    Write-Host "  [OK] Task created successfully" -ForegroundColor Green
}
catch {
    Write-Host "  [FAIL] Could not create task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Daily Sync Schedule Active" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Schedule:" -ForegroundColor White
Write-Host "  5:00 AM  - Download CSVs and import to production.db" -ForegroundColor Green
Write-Host "  6:30 AM  - Sync CSV data to Server 2" -ForegroundColor Green
Write-Host ""
Write-Host "To manage tasks:" -ForegroundColor White
Write-Host "  View:    Get-ScheduledTask -TaskName 'Daily-Data-Refresh'" -ForegroundColor Gray
Write-Host "  View:    Get-ScheduledTask -TaskName 'Daily-DB-Sync'" -ForegroundColor Gray
Write-Host "  Run now: Start-ScheduledTask -TaskName 'Daily-Data-Refresh'" -ForegroundColor Gray
Write-Host "  Disable: Disable-ScheduledTask -TaskName 'Daily-Data-Refresh'" -ForegroundColor Gray
Write-Host "  Remove:  Unregister-ScheduledTask -TaskName 'Daily-Data-Refresh' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
Write-Host "Logs will be saved to:" -ForegroundColor White
Write-Host "  Refresh: db-sync/logs/" -ForegroundColor Gray
Write-Host "  Sync:    db-sync/logs/" -ForegroundColor Gray
Write-Host ""
