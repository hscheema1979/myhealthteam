#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Schedules the autocommit script to run every hour
.DESCRIPTION
    Creates a Windows Task Scheduler task that runs the autocommit.py script every hour
#>

param(
    [string]$TaskName = "AutoCommit-Hourly",
    [string]$ScriptPath = "D:\Git\myhealthteam2\Streamlit\scripts\autocommit.py",
    [string]$LogPath = "D:\Git\myhealthteam2\Streamlit\scripts\autocommit.log"
)

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: This script must be run as Administrator to create scheduled tasks." -ForegroundColor Red
    exit 1
}

# Create the scheduled task action
$action = New-ScheduledTaskAction -Execute "python" -Argument "-u $ScriptPath" -WorkingDirectory "D:\Git\myhealthteam2\Streamlit"

# Create the trigger (every hour)
$trigger = New-ScheduledTaskTrigger -Once -At 12:00AM -RepetitionInterval (New-TimeSpan -Hours 1)

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable:$false

# Create principal (run with highest privileges)
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

# Register the task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Auto-commit git changes every hour"
    
    Write-Host "SUCCESS: Scheduled task '$TaskName' created successfully!" -ForegroundColor Green
    Write-Host "Task will run every hour at the top of the hour." -ForegroundColor Cyan
    Write-Host "Logs will be written to: $LogPath" -ForegroundColor Yellow
    
    # Show current status
    Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State, LastRunTime, NextRunTime
    
} catch {
    Write-Host "ERROR: Failed to create scheduled task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Optional: Start the task immediately for testing
Write-Host "`nWould you like to run the task immediately for testing? (y/n)" -ForegroundColor Yellow
$response = Read-Host
if ($response -eq "y" -or $response -eq "Y") {
    try {
        Start-ScheduledTask -TaskName $TaskName
        Write-Host "Task started successfully for testing." -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not start task immediately: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}