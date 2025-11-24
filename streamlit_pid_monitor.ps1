<#
.SYNOPSIS
  Monitors the Streamlit app process by PID every N seconds and restarts it if it exits.

.DESCRIPTION
  Launches the Streamlit app in a visible PowerShell window and tracks the child python.exe
  process running `python -m streamlit run <app.py>`. Every CheckInterval seconds, it verifies
  that the tracked PID is still alive; if not, it restarts the app and updates the tracked PID.

.PARAMETER CheckInterval
  Number of seconds between checks (default: 30).

.PARAMETER MaxConsecutiveFailures
  Number of consecutive restart failures before pausing (default: 5).

.PARAMETER AppPath
  Path to your Streamlit app.py (defaults to Streamlit\app.py next to this script).

.PARAMETER LogPath
  Path to the monitor log file (defaults to Streamlit\streamlit_pid_monitor.log).

.NOTES
  - This script is intended to be run by a user (visible window). It will open the app in a
    new visible PowerShell window and keep monitoring from the current window.
  - You can register this monitor to run at logon using a Scheduled Task (Interactive), or place
    a shortcut in the Startup folder.
#>

param(
  [int]$CheckInterval = 30,
  [int]$MaxConsecutiveFailures = 5,
  [string]$AppPath,
  [string]$LogPath
)

# Resolve default paths relative to this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $AppPath) { $AppPath = Join-Path $scriptDir 'app.py' }
if (-not $LogPath) { $LogPath = Join-Path $scriptDir 'streamlit_pid_monitor.log' }

$TrackedPid = $null
$ConsecutiveFailures = 0

function Write-Log {
  param([string]$Message)
  $ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
  $line = "[$ts] $Message"
  Write-Host $line
  try { Add-Content -Path $LogPath -Value $line } catch {}
}

function Find-StreamlitProcess {
  param([string]$AppPath)
  # Find python.exe or streamlit process whose CommandLine contains 'streamlit' and our app path
  try {
    $processes = Get-CimInstance Win32_Process |
      Where-Object { $_.CommandLine -match 'streamlit' -and $_.CommandLine -match [Regex]::Escape($AppPath) }
    if ($processes) {
      # Return the most recent by CreationDate
      $p = $processes | Sort-Object CreationDate -Descending | Select-Object -First 1
      return $p
    }
  } catch {}
  return $null
}

function Start-StreamlitVisible {
  param([string]$AppPath)
  Write-Log "Starting Streamlit app in visible PowerShell window..."
  try {
    # Launch a new visible PowerShell window that runs the app and stays open
    Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoExit', '-Command', "python -m streamlit run `"$AppPath`"" -WindowStyle Normal | Out-Null
    Start-Sleep -Seconds 3
    $p = Find-StreamlitProcess -AppPath $AppPath
    if ($p) {
      Write-Log "Located streamlit process: PID=$($p.ProcessId) CommandLine=$($p.CommandLine)"
      return $p.ProcessId
    } else {
      Write-Log "Failed to locate streamlit process after start."
      return $null
    }
  } catch {
    Write-Log "Exception while starting Streamlit: $($_.Exception.Message)"
    return $null
  }
}

function Is-ProcessAlive {
  param([int]$Pid)
  try {
    $proc = Get-Process -Id $Pid -ErrorAction SilentlyContinue
    return [bool]$proc
  } catch { return $false }
}

Write-Log "Streamlit PID monitor started. AppPath=$AppPath CheckInterval=${CheckInterval}s LogPath=$LogPath"

# Initial start (if not already running)
$existing = Find-StreamlitProcess -AppPath $AppPath
if ($existing) {
  $TrackedPid = $existing.ProcessId
  Write-Log "Detected existing app process. Tracking PID=$TrackedPid"
} else {
  $TrackedPid = Start-StreamlitVisible -AppPath $AppPath
}

while ($true) {
  if (-not $TrackedPid -or -not (Is-ProcessAlive -Pid $TrackedPid)) {
    Write-Log "Tracked process missing. Restarting..."
    $TrackedPid = Start-StreamlitVisible -AppPath $AppPath
    if ($TrackedPid) {
      $ConsecutiveFailures = 0
    } else {
      $ConsecutiveFailures += 1
      Write-Log "Restart attempt failed (count=$ConsecutiveFailures)."
      if ($ConsecutiveFailures -ge $MaxConsecutiveFailures) {
        Write-Log "Max consecutive failures reached ($MaxConsecutiveFailures). Pausing for 2 minutes before retrying."
        $ConsecutiveFailures = 0
        Start-Sleep -Seconds 120
      }
    }
  }
  else {
    # Optional: write a heartbeat every N cycles instead of every cycle to reduce noise
    Write-Log "Process PID=$TrackedPid is alive."
  }
  Start-Sleep -Seconds $CheckInterval
}