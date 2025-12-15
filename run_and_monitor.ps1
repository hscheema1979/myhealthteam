<#
.SYNOPSIS
  Monitors the Streamlit app process by PID every N seconds and restarts it if it exits.

.DESCRIPTION
  Launches the Streamlit app in a visible PowerShell window from the script's directory.
  Tracks the child python.exe process running `python -m streamlit run <app.py>`.
  Every CheckInterval seconds, it verifies that the tracked PID is still alive;
  if not, it restarts the app and updates the tracked PID.

.PARAMETER CheckInterval
  Number of seconds between checks (default: 30).

.PARAMETER MaxConsecutiveFailures
  Number of consecutive restart failures before pausing (default: 5).

.PARAMETER AppPath
  Path to your Streamlit app.py (defaults to Streamlit\app.py next to this script).

.PARAMETER LogPath
  Path to the monitor log file (defaults to Streamlit\run_and_monitor.log).

.PARAMETER UsePrototype
  Switch to enable Prototype Mode (sets USE_PROTOTYPE=1 environment variable).

.NOTES
  - This script is intended to be run by a user (visible window). It will open the app in a
    new visible PowerShell window and keep monitoring from the current window.
  - YOU MUST RUN THIS SCRIPT FROM ITS DIRECTORY OR PROVIDE ABSOLUTE PATHS.
#>

param(
  [int]$CheckInterval = 30,
  [int]$MaxConsecutiveFailures = 5,
  [string]$AppPath,
  [string]$LogPath,
  [int]$Port = 8502,  # Dev environment default
  [switch]$UsePrototype # Logic to use prototype.db
)

# Resolve default paths relative to this script
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $AppPath) { $AppPath = Join-Path $scriptDir 'app.py' }
if (-not $LogPath) { $LogPath = Join-Path $scriptDir 'run_and_monitor.log' }

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
  param([string]$AppPath, [int]$Port = 8502, [switch]$UsePrototype)
  
  $dbMsg = if ($UsePrototype) { "PROTOTYPE DB" } else { "Production DB" }
  Write-Log "Starting Streamlit app ($dbMsg) in visible PowerShell window on port $Port..."
  
  # IMPORTANT: Propagate the environment variable to the current process so the child inherits it.
  if ($UsePrototype) {
    $env:USE_PROTOTYPE = "1"
    Write-Log "Set env:USE_PROTOTYPE = 1"
  } else {
    $env:USE_PROTOTYPE = $null
  }

  try {
    # Use simple command string, relying on environment inheritance
    $cmd = "python -m streamlit run `"$AppPath`" --server.port $Port"
    
    # Launch new visible PowerShell window that runs the app and stays open.
    # CRITICAL: Set WorkingDirectory to $scriptDir to ensure relative DB paths work.
    Start-Process -FilePath 'powershell.exe' `
                  -ArgumentList '-NoExit', '-Command', $cmd `
                  -WorkingDirectory $scriptDir `
                  -WindowStyle Normal | Out-Null
    
    Start-Sleep -Seconds 5 # Give it a moment to spin up
    
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
  param([int]$ProcessId)
  try {
    $proc = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    return [bool]$proc
  } catch { return $false }
}

Write-Log "Streamlit monitor started." 
Write-Log "  AppPath: $AppPath"
Write-Log "  WorkingDir: $scriptDir"
Write-Log "  PrototypeMode: $UsePrototype"

# Initial start (if not already running)
$existing = Find-StreamlitProcess -AppPath $AppPath
if ($existing) {
  $TrackedPid = $existing.ProcessId
  Write-Log "Detected existing app process. Tracking PID=$TrackedPid"
} else {
  $TrackedPid = Start-StreamlitVisible -AppPath $AppPath -Port $Port -UsePrototype:$UsePrototype
}


function Find-CaddyProcess {
  try {
    $processes = Get-CimInstance Win32_Process |
      Where-Object { $_.Name -eq 'caddy.exe' }
    if ($processes) {
      $p = $processes | Sort-Object CreationDate -Descending | Select-Object -First 1
      return $p
    }
  } catch {}
  return $null
}

function Start-CaddyVisible {
  param([string]$CaddyPath, [string]$ConfigPath)
  Write-Log "Starting Caddy in visible PowerShell window..."
  try {
    Start-Process -FilePath 'powershell.exe' `
                  -ArgumentList '-NoExit', '-Command', "& `"$CaddyPath`" run --config `"$ConfigPath`"" `
                  -WorkingDirectory $scriptDir `
                  -WindowStyle Normal | Out-Null
    Start-Sleep -Seconds 3
    $p = Find-CaddyProcess
    if ($p) {
      Write-Log "Located Caddy process: PID=$($p.ProcessId) CommandLine=$($p.CommandLine)"
      return $p.ProcessId
    } else {
      Write-Log "Failed to locate Caddy process after start."
      return $null
    }
  } catch {
    Write-Log "Exception while starting Caddy: $($_.Exception.Message)"
    return $null
  }
}

$CaddyPath = Join-Path $scriptDir 'scripts\tools\caddy.exe'
$CaddyConfigPath = Join-Path $scriptDir 'scripts\tools\Caddyfile'
$TrackedCaddyPid = $null

$existingCaddy = Find-CaddyProcess
if ($existingCaddy) {
  $TrackedCaddyPid = $existingCaddy.ProcessId
  Write-Log "Detected existing Caddy process. Tracking PID=$TrackedCaddyPid"
} else {
  if (Test-Path $CaddyPath) {
    $TrackedCaddyPid = Start-CaddyVisible -CaddyPath $CaddyPath -ConfigPath $CaddyConfigPath
  } else {
    Write-Log "Caddy executable not found at $CaddyPath. Skipping Caddy start."
  }
}

while ($true) {
  # Monitor Streamlit
  if (-not $TrackedPid -or -not (Is-ProcessAlive -ProcessId $TrackedPid)) {
    Write-Log "Tracked Streamlit process missing. Restarting..."
    $TrackedPid = Start-StreamlitVisible -AppPath $AppPath -Port $Port -UsePrototype:$UsePrototype
    if ($TrackedPid) {
      $ConsecutiveFailures = 0
    } else {
      $ConsecutiveFailures += 1
      Write-Log "Streamlit restart attempt failed (count=$ConsecutiveFailures)."
      if ($MaxConsecutiveFailures -le 0) {
        Write-Log "Unlimited retries enabled. Continuing without pause."
      } elseif ($ConsecutiveFailures -ge $MaxConsecutiveFailures) {
        Write-Log "Max consecutive failures reached ($MaxConsecutiveFailures). Pausing for 2 minutes before retrying."
        $ConsecutiveFailures = 0
        Start-Sleep -Seconds 120
      }
    }
  }
  else {
    # Keep output clean, check periodically
  }

  # Monitor Caddy
  if ($TrackedCaddyPid -and -not (Is-ProcessAlive -ProcessId $TrackedCaddyPid)) {
    Write-Log "Tracked Caddy process missing. Restarting..."
    $TrackedCaddyPid = Start-CaddyVisible -CaddyPath $CaddyPath -ConfigPath $CaddyConfigPath
  } elseif (-not $TrackedCaddyPid -and (Test-Path $CaddyPath)) {
      $TrackedCaddyPid = Start-CaddyVisible -CaddyPath $CaddyPath -ConfigPath $CaddyConfigPath
  }

  Start-Sleep -Seconds $CheckInterval
}
