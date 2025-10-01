<#
.SYNOPSIS
    Setup Windows Task Scheduler for automated Git commits with database packaging

.DESCRIPTION
    This script configures Windows Task Scheduler to run the enhanced auto-commit script
    that includes database packaging functionality.

.PARAMETER Action
    Action to perform: 'create', 'remove', 'status'

.PARAMETER IntervalHours
    Interval in hours for the task (default: 1)

.PARAMETER IncludeDatabase
    Whether to include database packaging in the automated workflow

.PARAMETER DatabaseName
    Name of the database file to package

.EXAMPLE
    .\setup_auto_git_commit_with_db.ps1 -Action create
    .\setup_auto_git_commit_with_db.ps1 -Action create -IncludeDatabase $true
    .\setup_auto_git_commit_with_db.ps1 -Action remove
    .\setup_auto_git_commit_with_db.ps1 -Action status
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('create', 'remove', 'status')]
    [string]$Action,
    
    [int]$IntervalHours = 1,
    [bool]$IncludeDatabase = $true,
    [string]$DatabaseName = "production.db"
)

# Configuration
$TaskName = "MyHealthTeam Auto Git Commit with DB"
$ScriptPath = Split-Path -Parent $PSScriptRoot
$ScriptFile = "scripts\auto_git_commit_with_db.ps1"
$FullScriptPath = Join-Path $ScriptPath $ScriptFile

function Write-Status {
    param([string]$Message, [string]$Type = "INFO")
    $Colors = @{
        "INFO" = "White"
        "SUCCESS" = "Green"
        "WARNING" = "Yellow"
        "ERROR" = "Red"
    }
    Write-Host $Message -ForegroundColor $Colors[$Type]
}

function Test-AdminRights {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-TaskStatus {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        return @{
            Exists = $true
            State = $task.State
            LastRunTime = $taskInfo.LastRunTime
            NextRunTime = $taskInfo.NextRunTime
            LastTaskResult = $taskInfo.LastTaskResult
        }
    }
    return @{ Exists = $false }
}

function New-AutoCommitTask {
    # Build the PowerShell command with parameters
    $Arguments = "-ExecutionPolicy Bypass -File `"$FullScriptPath`""
    
    if ($IncludeDatabase) {
        $Arguments += " -IncludeDatabase `$true -DatabaseName `"$DatabaseName`""
    } else {
        $Arguments += " -IncludeDatabase `$false"
    }
    
    Write-Status "Creating scheduled task with arguments: $Arguments" "INFO"
    
    # Create the scheduled task
    $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument $Arguments
    
    # Set trigger to run every hour
    $Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours $IntervalHours)
    
    # Set conditions - run whether user is logged on or not, wake computer if needed
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun
    
    # Register the task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -RunLevel Highest -Force | Out-Null
    
    Write-Status "Task '$TaskName' created successfully!" "SUCCESS"
    Write-Status "The task will run every $IntervalHours hour(s)" "INFO"
    Write-Status "Database packaging: $(if($IncludeDatabase){'ENABLED'}else{'DISABLED'})" "INFO"
}

function Remove-AutoCommitTask {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Status "Task '$TaskName' removed successfully!" "SUCCESS"
    } else {
        Write-Status "Task '$TaskName' not found!" "WARNING"
    }
}

function Show-TaskStatus {
    $status = Get-TaskStatus
    if ($status.Exists) {
        Write-Status "Task Status for '$TaskName':" "INFO"
        Write-Status "  State: $($status.State)" "INFO"
        Write-Status "  Last Run: $($status.LastRunTime)" "INFO"
        Write-Status "  Next Run: $($status.NextRunTime)" "INFO"
        Write-Status "  Last Result: $($status.LastTaskResult)" "INFO"
    } else {
        Write-Status "Task '$TaskName' does not exist" "WARNING"
    }
}

# Main execution
Write-Status "=== MyHealthTeam Auto Git Commit with DB Setup ===" "INFO"

# Check for admin rights
if (!(Test-AdminRights)) {
    Write-Status "This script requires administrator privileges!" "ERROR"
    Write-Status "Please run PowerShell as Administrator and try again." "WARNING"
    exit 1
}

# Verify script file exists
if (!(Test-Path $FullScriptPath)) {
    Write-Status "Script file not found: $FullScriptPath" "ERROR"
    Write-Status "Please ensure the enhanced auto-commit script exists." "WARNING"
    exit 1
}

# Execute requested action
switch ($Action.ToLower()) {
    'create' {
        Write-Status "Creating automated git commit task with database packaging..." "INFO"
        New-AutoCommitTask
        Show-TaskStatus
        
        Write-Status "`nNext steps:" "INFO"
        Write-Status "1. Monitor the logs at: $ScriptPath\logs\" "INFO"
        Write-Status "2. Check Task Scheduler for task status" "INFO"
        Write-Status "3. Database packages will be created every 6 hours" "INFO"
        if ($IncludeDatabase) {
            Write-Status "4. Database '$DatabaseName' will be packaged and included in commits" "INFO"
        }
    }
    
    'remove' {
        Write-Status "Removing automated git commit task..." "INFO"
        Remove-AutoCommitTask
    }
    
    'status' {
        Write-Status "Checking task status..." "INFO"
        Show-TaskStatus
    }
}

Write-Status "`n=== Setup Completed ===" "INFO"