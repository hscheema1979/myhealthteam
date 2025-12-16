param(
  [string]$StreamlitUrl = "http://localhost:8501",
  [string]$CoordinatorEmail = "hector@myhealthteam.org",
  [string]$CoordinatorPassword = "pass123",
  [string]$OnboardingEmail = "onboarding@myhealthteam.org",
  [string]$OnboardingPassword = "pass123",
  [string]$ProviderEmail = "angela@myhealthteam.org",
  [string]$ProviderPassword = "pass123",
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
    Write-Host "Streamlit is up at $Url"
    return
  }
  Write-Host "Starting Streamlit app..."
  $appPath = Join-Path (Split-Path $PSScriptRoot -Parent) 'app.py'
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = "python"
  $psi.Arguments = "-m streamlit run `"$appPath`""
  $psi.WorkingDirectory = (Split-Path $PSScriptRoot -Parent)
  $psi.UseShellExecute = $true
  $proc = [System.Diagnostics.Process]::Start($psi)
  Start-Sleep -Seconds 3
  $maxWait = 30
  $i = 0
  while (-not (Test-AppUp -Url $Url) -and $i -lt $maxWait) {
    Start-Sleep -Seconds 2
    $i++
  }
  if (Test-AppUp -Url $Url) {
    Write-Host "Streamlit started at $Url"
  } else {
    Write-Host "Streamlit did not start in time"
  }
}

Start-StreamlitIfNeeded -Url $StreamlitUrl

$env:STREAMLIT_URL = $StreamlitUrl
$env:COORDINATOR_EMAIL = $CoordinatorEmail
$env:COORDINATOR_PASSWORD = $CoordinatorPassword
if ($OnboardingEmail) { $env:ONBOARDING_EMAIL = $OnboardingEmail }
if ($OnboardingPassword) { $env:ONBOARDING_PASSWORD = $OnboardingPassword }
$env:PROVIDER_EMAIL = $ProviderEmail
$env:PROVIDER_PASSWORD = $ProviderPassword
$env:HEADLESS = if ($Headless) { "true" } else { "false" }

Write-Host "Running workflow capture (direct login)..."
$nodeScript = Join-Path $PSScriptRoot 'automation\capture_workflows_direct.js'
node $nodeScript

if ($LASTEXITCODE -eq 0) {
  Write-Host "Capture complete"
} else {
  Write-Host "Capture failed (exit $LASTEXITCODE)"
}