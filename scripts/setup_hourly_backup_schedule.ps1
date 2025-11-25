# Setup Hourly Database Backup Schedule
# Creates Windows Task Scheduler job for hourly database backups
# Replaces the existing daily backup with hourly backups

param(
    [string]$TaskName = "MHT_Hourly_Database_Backup",
    [string]$ScriptPath = "D:\Git\myhealthteam2\Streamlit\scripts\hourly_backup_system.ps1",
    [string]$WorkingDirectory = "D:\Git\myhealthteam2\Streamlit"
)

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "⚠️  This script requires Administrator privileges to create scheduled tasks." -ForegroundColor Yellow
    Write-Host "Please right-click and 'Run as Administrator' or run from an elevated PowerShell." -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Setting up Hourly Database Backup Schedule ===" -ForegroundColor Cyan

# Remove existing daily backup task if it exists
$existingDailyTask = "MHT_Database_Backup"
if (Get-ScheduledTask -TaskName $existingDailyTask -ErrorAction SilentlyContinue) {
    Write-Host "🗑️ Removing existing daily backup task: $existingDailyTask" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $existingDailyTask -Confirm:$false
        Write-Host "✅ Removed existing daily backup task" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to remove existing daily backup task: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Remove existing hourly backup task if it exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "🗑️ Removing existing hourly backup task: $TaskName" -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task action
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`" -EnableGitCommit" `
    -WorkingDirectory $WorkingDirectory

# Create the trigger - every hour
$Trigger = New-ScheduledTaskTrigger -Once -At 12:00AM -RepetitionInterval (New-TimeSpan -Hours 1) -RepeatIndefinitely

# Create task settings for reliability
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -RestartOnFailure `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Create the principal (run as current user with highest privileges)
$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Create task description
$Description = "Automated hourly backup of MHT production database with GitHub auto-commit. 
Runs every hour to provide frequent backup coverage for production data.
Includes automatic cleanup of old backups based on retention policies."

try {
    # Register the scheduled task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $Description
    
    Write-Host "✅ Hourly backup task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Task Configuration:" -ForegroundColor Cyan
    Write-Host "   Task Name: $TaskName" -ForegroundColor White
    Write-Host "   Schedule: Every hour starting at 12:00 AM" -ForegroundColor White
    Write-Host "   Script: $ScriptPath" -ForegroundColor White
    Write-Host "   Working Directory: $WorkingDirectory" -ForegroundColor White
    Write-Host "   GitHub Auto-Commit: Enabled" -ForegroundColor White
    Write-Host ""
    
    # Show the created task
    $Task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "📊 Task Status:" -ForegroundColor Cyan
    Write-Host "   State: $($Task.State)" -ForegroundColor White
    
    $TaskInfo = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
    Write-Host "   Next Run: $($TaskInfo.NextRunTime)" -ForegroundColor White
    Write-Host "   Last Run: $($TaskInfo.LastRunTime)" -ForegroundColor White
    Write-Host "   Last Result: $($TaskInfo.LastTaskResult)" -ForegroundColor White
    Write-Host ""
    
    # Test the task immediately
    Write-Host "🧪 Testing the backup script..." -ForegroundColor Cyan
    
    try {
        & $ScriptPath -EnableGitCommit
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Backup script test completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Backup script test failed with exit code: $LASTEXITCODE" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Backup script test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🎯 Hourly Backup Schedule Setup Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your database will now be backed up every hour with:" -ForegroundColor White
    Write-Host "• Hourly backups (kept for 7 days)" -ForegroundColor White
    Write-Host "• Daily backup references (kept for 90 days)" -ForegroundColor White
    Write-Host "• Automatic cleanup of old backups" -ForegroundColor White
    Write-Host "• GitHub auto-commit for code versioning" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Error "❌ Failed to create scheduled task: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "🛠️ Manual Setup Instructions:" -ForegroundColor Yellow
    Write-Host "1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
    Write-Host "2. Create Basic Task..." -ForegroundColor White
    Write-Host "3. Name: $TaskName" -ForegroundColor White
    Write-Host "4. Trigger: Daily, Repeat task every: 1 hour" -ForegroundColor White
    Write-Host "5. Action: Start a program" -ForegroundColor White
    Write-Host "   Program: PowerShell.exe" -ForegroundColor White
    Write-Host "   Arguments: -ExecutionPolicy Bypass -File `"$ScriptPath`"" -ForegroundColor White
    Write-Host "6. Finish and test the task" -ForegroundColor White
}