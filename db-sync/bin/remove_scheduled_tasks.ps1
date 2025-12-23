# remove_scheduled_tasks.ps1
# Remove old 15-minute sync task and prepare for new daily sync tasks

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Removing Old Scheduled Tasks" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Remove the old 15-minute sync task
$oldTaskName = "DB-Sync-Production"
$existingTask = Get-ScheduledTask -TaskName $oldTaskName -ErrorAction SilentlyContinue

if ($existingTask) {
    Write-Host "Removing task: $oldTaskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $oldTaskName -Confirm:$false -ErrorAction Stop
        Write-Host "  [OK] Task removed successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "  [FAIL] Could not remove task: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "Task '$oldTaskName' not found (already removed or never created)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Ready for new daily sync setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
