# Simple Hourly Backup Schedule Setup
# Creates a Windows Task Scheduler job for hourly database backups
# Uses a simplified approach for maximum compatibility

param(
    [string]$TaskName = "MHT_Hourly_Database_Backup",
    [string]$ScriptPath = "D:\Git\myhealthteam2\Streamlit\scripts\hourly_backup_system.ps1",
    [string]$WorkingDirectory = "D:\Git\myhealthteam2\Streamlit"
)

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "WARNING: This script requires Administrator privileges to create scheduled tasks." -ForegroundColor Yellow
    Write-Host "Please right-click and 'Run as Administrator' or run from an elevated PowerShell." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "MANUAL SETUP ALTERNATIVE:" -ForegroundColor Cyan
    Write-Host "If you cannot run as admin, use Task Scheduler GUI:" -ForegroundColor White
    Write-Host "1. Press Win+R, type 'taskschd.msc' and press Enter" -ForegroundColor White  
    Write-Host "2. Click 'Create Basic Task...'" -ForegroundColor White
    Write-Host "3. Name: $TaskName" -ForegroundColor White
    Write-Host "4. Trigger: Daily, repeat every 1 hour" -ForegroundColor White
    Write-Host "5. Action: Start a program" -ForegroundColor White
    Write-Host "   Program: PowerShell.exe" -ForegroundColor White
    Write-Host "   Arguments: -ExecutionPolicy Bypass -File `"$ScriptPath`"" -ForegroundColor White
    Write-Host "6. Check 'Open the Properties dialog' and click Finish" -ForegroundColor White
    Write-Host "7. In Properties -> Settings -> Check 'Run task as soon as possible after a missed run'" -ForegroundColor White
    exit 1
}

Write-Host "=== Setting up Hourly Database Backup Schedule ===" -ForegroundColor Cyan
Write-Host "Task Name: $TaskName" -ForegroundColor White
Write-Host "Script: $ScriptPath" -ForegroundColor White
Write-Host ""

# Remove existing task if it exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Removing existing task: $TaskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed existing task" -ForegroundColor Green
    } catch {
        Write-Host "Could not remove existing task: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host ""
}

try {
    # Create the action
    $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`"" -WorkingDirectory $WorkingDirectory
    
    # Create the trigger (every hour starting at midnight)
    $Trigger = New-ScheduledTaskTrigger -Daily -At 12:00AM
    
    # Create simple settings
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -StartWhenAvailable
    
    # Create the principal (run as SYSTEM)
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
    
    # Create the task
    $Description = "Automated hourly backup of MHT production database with GitHub auto-commit"
    
    Write-Host "Creating scheduled task..." -ForegroundColor Cyan
    
    # Register the task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description $Description
    
    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Now set up the hourly repetition using schtasks command
    Write-Host "Setting up hourly repetition..." -ForegroundColor Cyan
    
    # Use schtasks to add the hourly repetition (more reliable)
    $schtasksCommand = "schtasks /Change /TN `"$TaskName`" /RI 60"  # 60 = 60 minutes
    
    Write-Host "Executing: $schtasksCommand" -ForegroundColor White
    
    $schtasksResult = Invoke-Expression $schtasksCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Hourly repetition configured successfully!" -ForegroundColor Green
    } else {
        Write-Host "Could not set hourly repetition. Task will run daily at midnight." -ForegroundColor Yellow
        Write-Host "You can manually modify the task to repeat every hour if needed." -ForegroundColor White
    }
    
    Write-Host ""
    
    # Show task details
    $Task = Get-ScheduledTask -TaskName $TaskName
    $TaskInfo = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
    
    Write-Host "Task Configuration:" -ForegroundColor Cyan
    Write-Host "   Task Name: $($Task.TaskName)" -ForegroundColor White
    Write-Host "   State: $($Task.State)" -ForegroundColor White
    Write-Host "   Next Run: $($TaskInfo.NextRunTime)" -ForegroundColor White
    Write-Host "   Last Run: $($TaskInfo.LastRunTime)" -ForegroundColor White
    Write-Host "   Author: $($Task.Author)" -ForegroundColor White
    Write-Host "   Description: $($Task.Description)" -ForegroundColor White
    Write-Host ""
    
    # Test the script
    Write-Host "Testing the backup script..." -ForegroundColor Cyan
    
    try {
        Write-Host "Running backup test..." -ForegroundColor White
        $testResult = & $ScriptPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Backup script test completed successfully!" -ForegroundColor Green
        } else {
            Write-Host "Backup script test completed with exit code: $LASTEXITCODE" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Backup script test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your system will now backup the database:" -ForegroundColor White
    Write-Host "• Automatically every hour" -ForegroundColor White  
    Write-Host "• With GitHub code versioning" -ForegroundColor White
    Write-Host "• With automatic cleanup of old backups" -ForegroundColor White
    Write-Host ""
    Write-Host "Monitor the backup log: backups\hourly_backup_log.txt" -ForegroundColor Cyan
    Write-Host ""
    
} catch {
    Write-Error "Failed to create scheduled task: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "MANUAL ALTERNATIVE:" -ForegroundColor Yellow
    Write-Host "Use Task Scheduler GUI to create the task manually:" -ForegroundColor White
    Write-Host "1. Open Task Scheduler (taskschd.msc)" -ForegroundColor White
    Write-Host "2. Create Basic Task..." -ForegroundColor White
    Write-Host "3. Name: $TaskName" -ForegroundColor White
    Write-Host "4. Trigger: Daily, repeat every 1 hour" -ForegroundColor White
    Write-Host "5. Action: Start a program" -ForegroundColor White
    Write-Host "   Program: PowerShell.exe" -ForegroundColor White
    Write-Host "   Arguments: -ExecutionPolicy Bypass -File `"$ScriptPath`"" -ForegroundColor White
}