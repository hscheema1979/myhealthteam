#!/usr/bin/env powershell
# Daily Import Scheduler
# Sets up automated daily import process using Windows Task Scheduler

param(
    [string]$TaskName = "HealthcareDashboard_DailyImport",
    [string]$ImportTime = "02:00",
    [switch]$Remove = $false,
    [switch]$TestRun = $false
)

# Function to write colored output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-Host "Healthcare Dashboard - Daily Import Scheduler" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

if ($Remove) {
    Write-Host "Removing scheduled task: $TaskName" -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-ColorOutput Green "✅ Task removed successfully"
        exit 0
    }
    catch {
        Write-ColorOutput Red "❌ Failed to remove task: $($_.Exception.Message)"
        exit 1
    }
}

if ($TestRun) {
    Write-Host "Running test import..." -ForegroundColor Yellow
    try {
        # Test the unified import script
        $testResult = & python scripts/unified_import.py --start-date 2025-12-01 --no-backup
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput Green "✅ Test import completed successfully"
            Write-ColorOutput Green $testResult
        } else {
            Write-ColorOutput Red "❌ Test import failed"
            Write-ColorOutput Red $testResult
        }
        exit $LASTEXITCODE
    }
    catch {
        Write-ColorOutput Red "❌ Test import failed: $($_.Exception.Message)"
        exit 1
    }
}

# Check if Python is available
Write-Host "Checking Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = & python --version 2>&1
    Write-ColorOutput Green "✅ Python found: $pythonVersion"
}
catch {
    Write-ColorOutput Red "❌ Python not found. Please install Python first."
    exit 1
}

# Check if unified import script exists
$importScript = "scripts\unified_import.py"
if (-not (Test-Path $importScript)) {
    Write-ColorOutput Red "❌ Unified import script not found: $importScript"
    exit 1
}
Write-ColorOutput Green "✅ Unified import script found"

# Check if wrapper script exists
$wrapperScript = "scripts\run_unified_import.bat"
if (-not (Test-Path $wrapperScript)) {
    Write-ColorOutput Yellow "⚠️ Wrapper script not found: $wrapperScript"
}

# Get current working directory
$currentDir = Get-Location
$scriptPath = Join-Path $currentDir $importScript

Write-Host "Setting up scheduled task..." -ForegroundColor Cyan
Write-Host "Task Name: $TaskName" -ForegroundColor White
Write-Host "Import Time: $ImportTime" -ForegroundColor White
Write-Host "Script Path: $scriptPath" -ForegroundColor White

# Create the PowerShell script content for the scheduled task
$taskScript = @"
# Daily Import Script for Healthcare Dashboard
`$ErrorActionPreference = "Stop"

try {
    Set-Location "$currentDir"
    
    Write-Output "Starting daily import at $(Get-Date)"
    
    # Run the unified import script with incremental mode
    `$result = & python "$scriptPath" --no-backup
    
    if (`$LASTEXITCODE -eq 0) {
        Write-Output "Daily import completed successfully at $(Get-Date)"
        exit 0
    } else {
        Write-Output "Daily import failed with exit code `$LASTEXITCODE"
        exit `$LASTEXITCODE
    }
}
catch {
    Write-Output "Daily import failed with error: `$(`$_.Exception.Message)"
    exit 1
}
"@

# Write the task script to a temporary file
$taskScriptPath = Join-Path $currentDir "scripts\daily_import_task.ps1"
$taskScript | Out-File -FilePath $taskScriptPath -Encoding UTF8

# Create the scheduled task
try {
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$taskScriptPath`""
    $trigger = New-ScheduledTaskTrigger -Daily -At $ImportTime
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    # Create the task
    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Description "Daily Healthcare Dashboard Data Import" -Force | Out-Null
    
    Write-ColorOutput Green "✅ Scheduled task created successfully"
    
    # Display task information
    Write-Host ""
    Write-ColorOutput Green "📋 Task Details:"
    Write-ColorOutput White "   Task Name: $TaskName"
    Write-ColorOutput White "   Schedule: Daily at $ImportTime"
    Write-ColorOutput White "   Script: $taskScriptPath"
    Write-ColorOutput White "   Status: Enabled"
    
    Write-Host ""
    Write-ColorOutput Green "🎯 Management Commands:"
    Write-ColorOutput White "   View task: schtasks /query /tn `"$TaskName`""
    Write-ColorOutput White "   Run task: schtasks /run /tn `"$TaskName`""
    Write-ColorOutput White "   Disable task: schtasks /change /tn `"$TaskName`" /disable"
    Write-ColorOutput White "   Remove task: powershell -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Remove"
    
    Write-Host ""
    Write-ColorOutput Green "📁 Log Files:"
    Write-ColorOutput White "   Check logs in: logs\unified_import_*.log"
    
    # Test the task (optional)
    Write-Host ""
    $testNow = Read-Host "Would you like to test run the task now? (y/N)"
    if ($testNow -eq "y" -or $testNow -eq "Y") {
        Write-ColorOutput Yellow "Testing scheduled task..."
        try {
            Start-ScheduledTask -TaskName $TaskName
            Write-ColorOutput Green "✅ Task started successfully"
            Write-ColorOutput White "   Check logs for results: logs\unified_import_*.log"
        }
        catch {
            Write-ColorOutput Red "❌ Failed to start task: $($_.Exception.Message)"
        }
    }
    
}
catch {
    Write-ColorOutput Red "❌ Failed to create scheduled task: $($_.Exception.Message)"
    exit 1
}

Write-Host ""
Write-ColorOutput Green "🎉 Daily import scheduler setup complete!"
