# =============================================================================
# ZEN Medical Healthcare Management System - SANDBOX MODE
# =============================================================================
# WARNING: This script runs the SANDBOX version of the application
# All changes made here will NOT affect production systems
# =============================================================================

Write-Host "=============================================================================" -ForegroundColor Red
Write-Host "SANDBOX MODE ACTIVATED - ZEN MEDICAL HEALTHCARE SYSTEM" -ForegroundColor Red -BackgroundColor Yellow
Write-Host "=============================================================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNING: You are running the SANDBOX version of the application" -ForegroundColor Yellow
Write-Host "Changes made here will NOT affect production systems" -ForegroundColor Yellow
Write-Host ""
Write-Host "Sandbox Location: D:\Git\myhealthteam2\Streamlit\sandbox" -ForegroundColor Cyan
Write-Host "Application: ZEN Medical Healthcare Management System" -ForegroundColor Cyan
Write-Host ""
Write-Host "=============================================================================" -ForegroundColor Green

# Change to the sandbox directory
Write-Host "Changing to sandbox directory..." -ForegroundColor Green
Set-Location "D:\Git\myhealthteam2\Streamlit\sandbox"

# Verify we're in the right place
$currentPath = Get-Location
Write-Host "Current directory: $currentPath" -ForegroundColor Green

# Check if app.py exists
$appPath = "D:\Git\myhealthteam2\Streamlit\sandbox\app.py"
if (Test-Path $appPath) {
    Write-Host "Found app.py at: $appPath" -ForegroundColor Green
}
else {
    Write-Host "ERROR: app.py not found at: $appPath" -ForegroundColor Red
    Write-Host "Please ensure the sandbox environment is properly set up." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting Streamlit application in SANDBOX mode..." -ForegroundColor Magenta
Write-Host "=============================================================================" -ForegroundColor Magenta

# Run the Streamlit app
try {
    & streamlit run app.py
}
catch {
    Write-Host "ERROR: Failed to start the application" -ForegroundColor Red
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=============================================================================" -ForegroundColor Blue
Write-Host "Sandbox session ended" -ForegroundColor Blue
Write-Host "=============================================================================" -ForegroundColor Blue