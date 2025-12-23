# setup_scheduled_task.ps1
# Creates Windows Scheduled Task for automatic database sync every 15 minutes

param(
    [switch]$Remove,  # Remove the scheduled task instead of creating it
    [int]$IntervalMinutes = 15  # Sync interval in minutes
)

$taskName = "DB-Sync-Production"
$scriptPath = Join-Path $PSScriptRoot "sync_production_db.ps1"

if ($Remove) {
    Write-Host "Removing scheduled task: $taskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction Stop
        Write-Host "Task removed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Task not found or already removed" -ForegroundColor Gray
    }
    exit 0
}

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task '$taskName' already exists. Use -Remove to delete it first." -ForegroundColor Yellow
    Write-Host "Current status: $($existingTask.State)" -ForegroundColor Gray
    exit 0
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setting up DB Sync Scheduled Task" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Task Name:    $taskName" -ForegroundColor White
Write-Host "Script:       $scriptPath" -ForegroundColor White
Write-Host "Interval:     Every $IntervalMinutes minutes" -ForegroundColor White
Write-Host ""

# Verify script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: Sync script not found: $scriptPath" -ForegroundColor Red
    exit 1
}

# Create the scheduled task
try {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`""

    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
        -RepetitionDuration (New-TimeSpan -Days 365)

    $settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -DontStopOnIdleEnd `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances IgnoreNew

    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Syncs production.db with VPS2 master every $IntervalMinutes minutes. Pulls from master normally, pushes after CSV imports." | Out-Null

    Write-Host "Scheduled task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The task will:" -ForegroundColor White
    Write-Host "  - Run every $IntervalMinutes minutes" -ForegroundColor Gray
    Write-Host "  - Pull database from VPS2 (master) to SRVR (slave)" -ForegroundColor Gray
    Write-Host "  - Push to VPS2 when bulk_import_complete.flag is detected" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To manage the task:" -ForegroundColor White
    Write-Host "  View:    Get-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "  Run now: Start-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "  Disable: Disable-ScheduledTask -TaskName '$taskName'" -ForegroundColor Gray
    Write-Host "  Remove:  .\setup_scheduled_task.ps1 -Remove" -ForegroundColor Gray

} catch {
    Write-Host "ERROR: Failed to create scheduled task" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
