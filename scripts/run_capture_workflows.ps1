param(
  [string]$StreamlitUrl = "http://localhost:8501",
  [string]$AdminEmail = "",
  [string]$AdminPassword = "",
  [string]$CoordinatorEmail = "",
  [string]$ProviderEmail = "",
  [bool]$Headless = $true
)

$ErrorActionPreference = "Stop"

function Test-AppUp {
  param([string]$Url)
  try {
    $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
    return $resp.StatusCode -eq 200
  } catch { return $false }
}

function Start-StreamlitIfNeeded {
  param([string]$Url)
  if (Test-AppUp -Url $Url) {
    Write-Host "✅ Streamlit is up at $Url" -ForegroundColor Green
    return
  }
  Write-Host "⏳ Starting Streamlit app..." -ForegroundColor Yellow
  $appPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'app.py'
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "python"
  $psi.Arguments = "-m streamlit run `"$appPath`""
  $psi.WorkingDirectory = (Split-Path $PSScriptRoot -Parent)
  $psi.UseShellExecute = $true
  $proc = [System.Diagnostics.Process]::Start($psi)
  Start-Sleep -Seconds 3
  # Poll until app responds
  $maxWait = 30
  $i = 0
  while (-not (Test-AppUp -Url $Url) -and $i -lt $maxWait) {
    Start-Sleep -Seconds 2
    $i++
  }
  if (Test-AppUp -Url $Url) {
    Write-Host "✅ Streamlit started at $Url" -ForegroundColor Green
  } else {
    Write-Host "❌ Streamlit did not start in time" -ForegroundColor Red
  }
}

# Ensure app is up
Start-StreamlitIfNeeded -Url $StreamlitUrl

# Set environment for Node script
$env:STREAMLIT_URL = $StreamlitUrl
if ($AdminEmail) { $env:ADMIN_EMAIL = $AdminEmail }
if ($AdminPassword) { $env:ADMIN_PASSWORD = $AdminPassword }
if ($CoordinatorEmail) { $env:COORDINATOR_EMAIL = $CoordinatorEmail }
if ($ProviderEmail) { $env:PROVIDER_EMAIL = $ProviderEmail }
$env:HEADLESS = if ($Headless) { "true" } else { "false" }

# Run capture script
Write-Host "📸 Running workflow capture..." -ForegroundColor Cyan
$nodeScript = Join-Path $PSScriptRoot 'automation\capture_workflows.js'
node $nodeScript

if ($LASTEXITCODE -eq 0) {
  Write-Host "✅ Capture complete" -ForegroundColor Green
} else {
  Write-Host "❌ Capture failed (exit $LASTEXITCODE)" -ForegroundColor Red
}