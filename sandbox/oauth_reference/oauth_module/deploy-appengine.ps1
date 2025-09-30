# Deploy OAuth Streamlit App to Google App Engine
param(
    [string]$ProjectId = "PCOPs",
    [string]$Version = "v1",
    [switch]$Promote = $true
)

Write-Host "Deploying OAuth Streamlit App to App Engine..." -ForegroundColor Green
Write-Host "Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Version: $Version" -ForegroundColor Yellow

# Set project
gcloud config set project $ProjectId

# Copy production requirements
Write-Host "Preparing production files..." -ForegroundColor Cyan
Copy-Item "requirements-production.txt" "requirements.txt" -Force
Copy-Item "streamlit_app_production.py" "streamlit_app.py" -Force

# Deploy to App Engine
Write-Host "Deploying to App Engine..." -ForegroundColor Cyan

$deployArgs = @(
    "app", "deploy", "app.yaml",
    "--version", $Version,
    "--quiet"
)

if ($Promote) {
    $deployArgs += "--promote"
} else {
    $deployArgs += "--no-promote"
}

& gcloud @deployArgs

# Get the service URL
$ServiceUrl = "https://$ProjectId.uc.r.appspot.com"
if (-not $Promote) {
    $ServiceUrl = "https://$Version-dot-$ProjectId.uc.r.appspot.com"
}

Write-Host "`nDeployment completed!" -ForegroundColor Green
Write-Host "Service URL: $ServiceUrl" -ForegroundColor Yellow

# Restore original files
Write-Host "Restoring original files..." -ForegroundColor Cyan
git checkout -- requirements.txt streamlit_app.py 2>$null

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "1. Update your OAuth redirect URI to: $ServiceUrl/auth/callback" -ForegroundColor White
Write-Host "2. Test the application at: $ServiceUrl" -ForegroundColor White
Write-Host "3. Monitor logs with: gcloud app logs tail -s default" -ForegroundColor White
Write-Host "4. If testing is successful and not promoted, promote with: gcloud app versions migrate $Version" -ForegroundColor White