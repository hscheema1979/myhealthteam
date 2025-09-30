# Update OAuth Redirect URI Script
# This script provides the exact steps and URLs to update your OAuth configuration

param(
    [string]$ClientId = "223722902991-jqch1qpuo4u9i5agk6erhneugc7fhhtq.apps.googleusercontent.com",
    [string]$ProductionUrl = "https://oauth-streamlit-223722902991.us-central1.run.app",
    [string]$ProjectId = "pcops-470417"
)

Write-Host "=== OAuth Redirect URI Update Guide ===" -ForegroundColor Green
Write-Host ""

Write-Host "Your OAuth Client ID: $ClientId" -ForegroundColor Yellow
Write-Host "Production URL: $ProductionUrl" -ForegroundColor Yellow
Write-Host "Callback URL to add: $ProductionUrl/auth/callback" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== Method 1: Google Cloud Console (Recommended) ===" -ForegroundColor Green
Write-Host "1. Open: https://console.cloud.google.com/apis/credentials?project=$ProjectId" -ForegroundColor White
Write-Host "2. Click on your OAuth 2.0 Client ID: $ClientId" -ForegroundColor White
Write-Host "3. In 'Authorized redirect URIs', add:" -ForegroundColor White
Write-Host "   $ProductionUrl/auth/callback" -ForegroundColor Cyan
Write-Host "4. Click 'Save'" -ForegroundColor White
Write-Host ""

Write-Host "=== Method 2: Direct Link ===" -ForegroundColor Green
$directLink = "https://console.cloud.google.com/apis/credentials?project=$ProjectId"
Write-Host "Direct link to credentials page: $directLink" -ForegroundColor Cyan
Write-Host "Then click on: $ClientId" -ForegroundColor White
Write-Host ""

Write-Host "=== Method 3: Using gcloud (Advanced) ===" -ForegroundColor Green
Write-Host "Unfortunately, gcloud doesn't have direct OAuth client update commands." -ForegroundColor Yellow
Write-Host "The Google Cloud Console web interface is the most reliable method." -ForegroundColor Yellow
Write-Host ""

Write-Host "=== After Update ===" -ForegroundColor Green
Write-Host "Test your application at: $ProductionUrl" -ForegroundColor Cyan
Write-Host ""

# Open the direct link in browser
Write-Host "Opening Google Cloud Console..." -ForegroundColor Green
Start-Process $directLink

Write-Host "=== Authorized JavaScript Origins Should Include ===" -ForegroundColor Green
Write-Host "✓ http://localhost:5001 (for local development)" -ForegroundColor White
Write-Host "✓ $ProductionUrl (for production)" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== Authorized Redirect URIs Should Include ===" -ForegroundColor Green
Write-Host "✓ http://localhost:5001/auth/callback (for local development)" -ForegroundColor White
Write-Host "✓ $ProductionUrl/auth/callback (for production)" -ForegroundColor Cyan
Write-Host ""

Write-Host "=== IMPORTANT: Update BOTH Origins AND Redirect URIs ===" -ForegroundColor Red
Write-Host "1. Authorized JavaScript origins: Add $ProductionUrl" -ForegroundColor Yellow
Write-Host "2. Authorized redirect URIs: Add $ProductionUrl/auth/callback" -ForegroundColor Yellow
Write-Host ""

Write-Host "Script completed! Please update BOTH origins and redirect URIs in the opened browser window." -ForegroundColor Green