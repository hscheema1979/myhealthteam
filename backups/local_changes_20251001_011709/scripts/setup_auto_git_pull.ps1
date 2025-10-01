# Setup Auto Git Pull for Production Environment
# This script sets up automated pulling from the remote repository
# Replaces the auto-commit/push system for production environments

param(
    [string]$TaskName = "MyHealthTeam-AutoGitPull",
    [string]$Branch = "main",
    [int]$IntervalMinutes = 60,
    [switch]$Remove = $false,
    [switch]$DryRun = $false
)

# Configuration
$ScriptPath = Join-Path $PSScriptRoot "auto_git_pull.ps1"
$RepoPath = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $RepoPath "logs\setup_auto_git_pull.log"

# Ensure logs directory exists
$LogDir = Split-Path -Parent $LogFile
if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"
    Write-Host $LogEntry
    Add-Content -Path $LogFile -Value $LogEntry
}

function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Remove-ExistingTask {
    param([string]$Name)
    
    try {
        $existingTask = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
        if ($existingTask) {
            Write-Log "Removing existing scheduled task: $Name" "INFO"
            Unregister-ScheduledTask -TaskName $Name -Confirm:$false
            Write-Log "Successfully removed existing task" "SUCCESS"
            return $true
        } else {
            Write-Log "No existing task found with name: $Name" "INFO"
            return $true
        }
    } catch {
        Write-Log "Error removing existing task: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Remove-AutoCommitTask {
    # Remove any existing auto-commit tasks
    $autoCommitTasks = @(
        "MyHealthTeam-AutoGitCommit",
        "AutoGitCommit",
        "Git-AutoCommit"
    )
    
    foreach ($taskName in $autoCommitTasks) {
        try {
            $existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            if ($existingTask) {
                Write-Log "Removing auto-commit task: $taskName" "INFO"
                Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
                Write-Log "Successfully removed auto-commit task: $taskName" "SUCCESS"
            }
        } catch {
            Write-Log "Error removing auto-commit task $taskName`: $($_.Exception.Message)" "WARNING"
        }
    }
}

function Create-AutoPullTask {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [int]$IntervalMinutes
    )
    
    try {
        Write-Log "Creating scheduled task: $Name" "INFO"
        Write-Log "Script path: $ScriptPath" "INFO"
        Write-Log "Interval: $IntervalMinutes minutes" "INFO"
        
        # Create the action
        $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`" -Branch $Branch"
        
        # Create the trigger (every X minutes)
        $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 365) -At (Get-Date).AddMinutes(5)
        
        # Create the settings
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RunOnlyIfNetworkAvailable
        
        # Create the principal (run as current user)
        $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive
        
        # Register the task
        if ($DryRun) {
            Write-Log "DRY RUN: Would create scheduled task with the following settings:" "WARNING"
            Write-Log "  Name: $Name" "WARNING"
            Write-Log "  Action: PowerShell.exe -ExecutionPolicy Bypass -File `"$ScriptPath`" -Branch $Branch" "WARNING"
            Write-Log "  Trigger: Every $IntervalMinutes minutes" "WARNING"
            Write-Log "  Principal: $env:USERNAME" "WARNING"
            return $true
        }
        
        Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
        
        Write-Log "Successfully created scheduled task: $Name" "SUCCESS"
        return $true
        
    } catch {
        Write-Log "Error creating scheduled task: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Test-AutoPullScript {
    if (!(Test-Path $ScriptPath)) {
        Write-Log "Auto pull script not found at: $ScriptPath" "ERROR"
        return $false
    }
    
    Write-Log "Testing auto pull script..." "INFO"
    try {
        $result = & PowerShell.exe -ExecutionPolicy Bypass -File $ScriptPath -DryRun
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Auto pull script test successful" "SUCCESS"
            return $true
        } else {
            Write-Log "Auto pull script test failed with exit code: $LASTEXITCODE" "ERROR"
            return $false
        }
    } catch {
        Write-Log "Error testing auto pull script: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-TaskStatus {
    param([string]$Name)
    
    try {
        $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
        if ($task) {
            Write-Log "Task Status for '$Name':" "INFO"
            Write-Log "  State: $($task.State)" "INFO"
            Write-Log "  Last Run Time: $($task.LastRunTime)" "INFO"
            Write-Log "  Next Run Time: $($task.NextRunTime)" "INFO"
            
            $taskInfo = Get-ScheduledTaskInfo -TaskName $Name -ErrorAction SilentlyContinue
            if ($taskInfo) {
                Write-Log "  Last Result: $($taskInfo.LastTaskResult)" "INFO"
            }
        } else {
            Write-Log "Task '$Name' not found" "WARNING"
        }
    } catch {
        Write-Log "Error getting task status: $($_.Exception.Message)" "ERROR"
    }
}

# Main execution
try {
    Write-Log "========================================" "INFO"
    Write-Log "Auto Git Pull Setup Script Started" "INFO"
    Write-Log "========================================" "INFO"
    Write-Log "Mode: $(if ($Remove) { 'REMOVE' } else { 'SETUP' })" "INFO"
    Write-Log "Task Name: $TaskName" "INFO"
    Write-Log "Branch: $Branch" "INFO"
    Write-Log "Interval: $IntervalMinutes minutes" "INFO"
    Write-Log "Dry Run: $DryRun" "INFO"
    
    # Check admin privileges
    if (!(Test-AdminPrivileges)) {
        Write-Log "WARNING: Running without administrator privileges. Some operations may fail." "WARNING"
    }
    
    if ($Remove) {
        # Remove mode
        Write-Log "Removing auto pull task..." "INFO"
        if (Remove-ExistingTask -Name $TaskName) {
            Write-Log "Auto pull task removal completed successfully" "SUCCESS"
        } else {
            Write-Log "Auto pull task removal failed" "ERROR"
            exit 1
        }
    } else {
        # Setup mode
        Write-Log "Setting up auto pull for production environment..." "INFO"
        
        # Remove any existing auto-commit tasks
        Remove-AutoCommitTask
        
        # Remove existing auto-pull task if it exists
        Remove-ExistingTask -Name $TaskName
        
        # Test the auto pull script
        if (!(Test-AutoPullScript)) {
            Write-Log "Auto pull script test failed. Setup aborted." "ERROR"
            exit 1
        }
        
        # Create the new auto pull task
        if (Create-AutoPullTask -Name $TaskName -ScriptPath $ScriptPath -IntervalMinutes $IntervalMinutes) {
            Write-Log "Auto pull task setup completed successfully" "SUCCESS"
            
            # Show task status
            Show-TaskStatus -Name $TaskName
            
            Write-Log "" "INFO"
            Write-Log "PRODUCTION ENVIRONMENT CONFIGURED:" "SUCCESS"
            Write-Log "- Auto-commit/push system DISABLED" "SUCCESS"
            Write-Log "- Auto-pull system ENABLED (every $IntervalMinutes minutes)" "SUCCESS"
            Write-Log "- Local changes will be backed up before pulling" "SUCCESS"
            Write-Log "- Logs will be written to: $LogFile" "SUCCESS"
            Write-Log "" "INFO"
            Write-Log "To manually trigger a pull: PowerShell.exe -ExecutionPolicy Bypass -File `"$ScriptPath`"" "INFO"
            Write-Log "To remove this setup: PowerShell.exe -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Remove" "INFO"
            
        } else {
            Write-Log "Auto pull task setup failed" "ERROR"
            exit 1
        }
    }
    
    Write-Log "Script completed successfully" "SUCCESS"
    exit 0
    
} catch {
    Write-Log "Unexpected error: $($_.Exception.Message)" "ERROR"
    Write-Log "Stack trace: $($_.ScriptStackTrace)" "ERROR"
    exit 1
} finally {
    Write-Log "========================================" "INFO"
    Write-Log "Auto Git Pull Setup Script Finished" "INFO"
    Write-Log "========================================" "INFO"
}