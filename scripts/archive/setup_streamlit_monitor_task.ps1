<#
.SYNOPSIS
  Sets up a Windows Scheduled Task to launch the Streamlit app and monitor on user logon, with a visible PowerShell session.

.DESCRIPTION
  Creates a scheduled task (default: MyHealthTeam-StreamlitMonitor) that runs:
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<repo>\Streamlit\run_and_monitor.ps1"

  The run_and_monitor.ps1 script starts the Streamlit app in a visible PowerShell window and the monitor minimized.

  This script requires Administrator privileges to register the scheduled task.

.PARAMETER TaskName
  Name of the task to create. Defaults to MyHealthTeam-StreamlitMonitor.

.PARAMETER Unregister
  Removes the scheduled task if it exists.

.PARAMETER StartNow
  Immediately starts the app and monitor after creating the task.

.PARAMETER StartupTrigger
  Also create a second scheduled task to start on system startup (requires admin). The suffix "-Startup" will be appended to TaskName.

.PARAMETER LogonTrigger
  Create a task that starts at user logon (default).

.EXAMPLE
  Run PowerShell as Administrator:
    PS> .\scripts\setup_streamlit_monitor_task.ps1 -StartNow

.EXAMPLE
  Create both logon and startup tasks:
    PS> .\scripts\setup_streamlit_monitor_task.ps1 -StartNow -StartupTrigger

.EXAMPLE
  Remove tasks:
    PS> .\scripts\setup_streamlit_monitor_task.ps1 -Unregister
#>

param(
  [string]$TaskName = "MyHealthTeam-StreamlitMonitor",
  [switch]$Unregister,
  [switch]$StartNow,
  [switch]$StartupTrigger,
  [switch]$LogonTrigger
)

function Test-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $p = New-Object Security.Principal.WindowsPrincipal($id)
  return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn($msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err($msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red }

# Determine paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$streamlitDir = Join-Path $repoRoot 'Streamlit'
$runScript = Join-Path $streamlitDir 'run_and_monitor.ps1'

if (-not (Test-Path $runScript)) {
  Write-Err "Could not find run_and_monitor.ps1 at: $runScript"
  Write-Err "Please ensure you run this from the repository root with the Streamlit folder present."
  exit 1
}

if ($Unregister) {
  Write-Info "Removing scheduled tasks..."
  schtasks /Delete /TN $TaskName /F | Out-Null
  schtasks /Delete /TN "$TaskName-Startup" /F | Out-Null
  Write-Info "Done."
  exit 0
}

$isAdmin = Test-Admin
if (-not $isAdmin) {
  Write-Err "This script must be run as Administrator to register scheduled tasks."
  Write-Info "Right-click PowerShell and choose 'Run as administrator', then re-run this script."
  exit 1
}

# Default: create logon task if no explicit trigger provided
$createLogon = $true
if ($PSBoundParameters.ContainsKey('LogonTrigger')) { $createLogon = $LogonTrigger.IsPresent }

# Build task command
$escapedRunScript = '"' + $runScript + '"'
$taskCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File $escapedRunScript"

if ($createLogon) {
  Write-Info "Creating logon task: $TaskName"
  $result = schtasks /Create /TN $TaskName /TR $taskCommand /SC ONLOGON /RL LIMITED /F /RU $env:USERNAME /IT 2>&1
  if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create logon task: $result"; exit 1 }
}

if ($StartupTrigger.IsPresent) {
  $startupName = "$TaskName-Startup"
  Write-Info "Creating startup task: $startupName"
  $result2 = schtasks /Create /TN $startupName /TR $taskCommand /SC ONSTART /RL LIMITED /F /RU $env:USERNAME /IT 2>&1
  if ($LASTEXITCODE -ne 0) { Write-Err "Failed to create startup task: $result2"; exit 1 }
}

Write-Info "Scheduled task(s) created successfully."
Write-Info "Task(s):"
try {
  Get-ScheduledTask | Where-Object { $_.TaskName -eq $TaskName -or $_.TaskName -eq "$TaskName-Startup" } | Format-Table TaskName, State, LastRunTime, NextRunTime
} catch {
  Write-Warn "Unable to query tasks via Get-ScheduledTask; continuing."
}

if ($StartNow) {
  Write-Info "Starting app and monitor now via run_and_monitor.ps1..."
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runScript
}

Write-Info "Setup complete. On next logon, the app will start in a visible PowerShell window and the monitor in a minimized window."