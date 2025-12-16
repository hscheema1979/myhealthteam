# Create Scheduled Task for Database Backup
# This script sets up a Windows Task Scheduler job to backup the database
# Runs every weekday at 7:00 PM

$TaskName = "MHT_Database_Backup"
$ScriptPath = "D:\Git\myhealthteam2\Streamlit\backup_database.ps1"
$WorkingDirectory = "D:\Git\myhealthteam2\Streamlit"

# Remove existing task if it exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "🗑️ Removing existing task: $TaskName"
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task action
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`"" `
    -WorkingDirectory $WorkingDirectory

# Create the trigger for weekdays at 7:00 PM
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 7:00PM

# Create task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create the principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Register the scheduled task
try {
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Automated daily backup of MHT production database"
    
    Write-Host "✅ Scheduled task created successfully!"
    Write-Host "   Task Name: $TaskName"
    Write-Host "   Schedule: Monday-Friday at 7:00 PM"
    Write-Host "   Script: $ScriptPath"
    Write-Host ""
    
    # Show the created task
    $Task = Get-ScheduledTask -TaskName $TaskName
    Write-Host "📋 Task Details:"
    Write-Host "   State: $($Task.State)"
    Write-Host "   Next Run: $((Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo).NextRunTime)"
    
} catch {
    Write-Error "❌ Failed to create scheduled task: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "🛠️ Manual Setup Instructions:"
    Write-Host "1. Open Task Scheduler (taskschd.msc)"
    Write-Host "2. Create Basic Task..."
    Write-Host "3. Name: $TaskName"
    Write-Host "4. Trigger: Daily, Monday-Friday, 7:00 PM"
    Write-Host "5. Action: Start a program"
    Write-Host "6. Program: PowerShell.exe"
    Write-Host "7. Arguments: -ExecutionPolicy Bypass -File `"$ScriptPath`""
    Write-Host "8. Start in: $WorkingDirectory"
}

Write-Host ""
Write-Host "🧪 To test the backup manually, run:"
Write-Host "   .\backup_database.ps1"
Write-Host ""
Write-Host "📊 To view task status:"
Write-Host "   Get-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "📅 To view task history:"
Write-Host "   Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; ID=200,201} | Where-Object {`$_.Message -like '*$TaskName*'} | Select-Object TimeCreated,Message"