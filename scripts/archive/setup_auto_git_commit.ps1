# Setup Auto Git Commit Scheduled Task
# This script creates a Windows Task Scheduler job to automatically commit and push changes every hour

param(
    [string]$TaskName = "MHT Auto Git Commit",
    [string]$Branch = "main",
    [switch]$Remove = $false,
    [switch]$Force = $false
)

# Configuration
$ScriptPath = Join-Path $PSScriptRoot "auto_git_commit.ps1"
$LogFile = Join-Path (Split-Path -Parent $PSScriptRoot) "logs\auto_git_commit.log"

function Write-Status {
    param(
        [string]$Message,
        [string]$Status = "INFO"
    )
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $StatusIcon = switch ($Status) {
        "SUCCESS" { "✅" }
        "ERROR" { "❌" }
        "WARNING" { "⚠️" }
        default { "ℹ️" }
    }
    Write-Host "[$Timestamp] $StatusIcon $Message"
}

function Test-AdminRights {
    try {
        $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
        return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    } catch {
        return $false
    }
}

function Remove-ExistingTask {
    param([string]$TaskName)
    
    try {
        $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($existingTask) {
            Write-Status "Found existing task: $TaskName" "WARNING"
            
            if ($Force -or (Read-Host "Remove existing task? (y/N)").ToLower() -eq 'y') {
                Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
                Write-Status "Removed existing task: $TaskName" "SUCCESS"
                return $true
            } else {
                Write-Status "Task removal cancelled" "WARNING"
                return $false
            }
        }
        return $true
    } catch {
        Write-Status "Error removing existing task: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Create-AutoGitCommitTask {
    param(
        [string]$TaskName,
        [string]$ScriptPath,
        [string]$Branch
    )
    
    try {
        # Verify script exists
        if (!(Test-Path $ScriptPath)) {
            Write-Status "Script not found: $ScriptPath" "ERROR"
            return $false
        }
        
        # Create the scheduled task action
        $Action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
            -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`" -Branch `"$Branch`"" `
            -WorkingDirectory (Split-Path -Parent $ScriptPath)
        
        # Create trigger - run every hour
        $Trigger = New-ScheduledTaskTrigger -Hourly -At 0
        
        # Create task settings
        $Settings = New-ScheduledTaskSettingsSet `
            -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries `
            -StartWhenAvailable `
            -RunOnlyIfNetworkAvailable `
            -MultipleInstances Parallel `
            -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
            -RestartCount 3 `
            -RestartInterval (New-TimeSpan -Minutes 5)
        
        # Create task principal (run as current user)
        $Principal = New-ScheduledTaskPrincipal `
            -UserId $env:USERNAME `
            -LogonType Interactive `
            -RunLevel Highest
        
        # Register the scheduled task
        Register-ScheduledTask `
            -TaskName $TaskName `
            -Action $Action `
            -Trigger $Trigger `
            -Settings $Settings `
            -Principal $Principal `
            -Description "Automatically commits and pushes git changes every hour for MHT Healthcare System"
        
        Write-Status "Created scheduled task: $TaskName" "SUCCESS"
        return $true
        
    } catch {
        Write-Status "Error creating scheduled task: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-TaskInfo {
    param([string]$TaskName)
    
    try {
        $Task = Get-ScheduledTask -TaskName $TaskName
        $TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
        
        Write-Status "Task Information:" "INFO"
        Write-Status "  Name: $($Task.TaskName)" "INFO"
        Write-Status "  State: $($Task.State)" "INFO"
        Write-Status "  Description: $($Task.Description)" "INFO"
        Write-Status "  Last Run Time: $($TaskInfo.LastRunTime)" "INFO"
        Write-Status "  Next Run Time: $($TaskInfo.NextRunTime)" "INFO"
        Write-Status "  Last Task Result: $($TaskInfo.LastTaskResult)" "INFO"
        
        if ($TaskInfo.LastTaskResult -ne 0) {
            Write-Status "  ⚠️  Check logs for errors: $LogFile" "WARNING"
        }
        
    } catch {
        Write-Status "Error getting task information: $($_.Exception.Message)" "ERROR"
    }
}

# Main execution
try {
    Write-Status "========================================" "INFO"
    Write-Status "Auto Git Commit Task Setup Started" "INFO"
    Write-Status "========================================" "INFO"
    
    # Check for admin rights
    if (!(Test-AdminRights)) {
        Write-Status "This script requires administrator privileges" "ERROR"
        Write-Status "Please run PowerShell as Administrator" "WARNING"
        exit 1
    }
    
    if ($Remove) {
        Write-Status "Removing scheduled task: $TaskName" "WARNING"
        Remove-ExistingTask -TaskName $TaskName
        Write-Status "Task removal completed" "SUCCESS"
        exit 0
    }
    
    # Check if task already exists
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        if (!(Remove-ExistingTask -TaskName $TaskName)) {
            exit 1
        }
    }
    
    # Create the scheduled task
    Write-Status "Creating scheduled task..." "INFO"
    if (Create-AutoGitCommitTask -TaskName $TaskName -ScriptPath $ScriptPath -Branch $Branch) {
        Write-Status "Scheduled task created successfully!" "SUCCESS"
        
        # Show task information
        Show-TaskInfo -TaskName $TaskName
        
        Write-Status "" "INFO"
        Write-Status "Next steps:" "INFO"
        Write-Status "1. Monitor the log file: $LogFile" "INFO"
        Write-Status "2. Check Task Scheduler for task status" "INFO"
        Write-Status "3. The task will run every hour automatically" "INFO"
        Write-Status "4. Manual test: Right-click task → Run" "INFO"
        
    } else {
        Write-Status "Failed to create scheduled task" "ERROR"
        exit 1
    }
    
} catch {
    Write-Status "Unexpected error: $($_.Exception.Message)" "ERROR"
    Write-Status "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
} finally {
    Write-Status "========================================" "INFO"
    Write-Status "Auto Git Commit Task Setup Finished" "INFO"
    Write-Status "========================================" "INFO"
}