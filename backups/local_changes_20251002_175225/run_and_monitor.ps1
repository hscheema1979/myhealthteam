# =============================================================================
# ZEN Medical Healthcare Management System - PRODUCTION MODE
# =============================================================================
# WARNING: This script runs the PRODUCTION version on PORT 8501
# This affects LIVE PRODUCTION DATA and REAL USERS
# =============================================================================

Write-Host "=============================================================================" -ForegroundColor Red
Write-Host "PRODUCTION MODE ACTIVATED - ZEN MEDICAL HEALTHCARE SYSTEM" -ForegroundColor Red -BackgroundColor Yellow
Write-Host "=============================================================================" -ForegroundColor Red
Write-Host ""
Write-Host "WARNING: You are running the PRODUCTION version on PORT 8501" -ForegroundColor Yellow
Write-Host "This affects LIVE PRODUCTION DATA and REAL USERS" -ForegroundColor Yellow
Write-Host ""
Write-Host "Production Location: D:\Git\myhealthteam2\Streamlit" -ForegroundColor Cyan
Write-Host "Database: production.db (LIVE DATA)" -ForegroundColor Cyan
Write-Host "Port: 8501 (PRODUCTION)" -ForegroundColor Cyan
Write-Host ""
Write-Host "=============================================================================" -ForegroundColor Green

# Ensure we're in the correct production directory
Write-Host "Setting production working directory..." -ForegroundColor Green
Set-Location "D:\Git\myhealthteam2\Streamlit"

# Verify we're in the right place
$currentPath = Get-Location
Write-Host "Current directory: $currentPath" -ForegroundColor Green

# Check if app.py exists
$appPath = "D:\Git\myhealthteam2\Streamlit\app.py"
if (Test-Path $appPath) {
    Write-Host "Found app.py at: $appPath" -ForegroundColor Green
}
else {
    Write-Host "ERROR: app.py not found at: $appPath" -ForegroundColor Red
    Write-Host "Please ensure the production environment is properly set up." -ForegroundColor Red
    exit 1
}

# Set production environment variables
$env:STREAMLIT_SERVER_PORT = "8501"
$env:STREAMLIT_SERVER_ADDRESS = "0.0.0.0"
$env:DATABASE_PATH = "D:\Git\myhealthteam2\Streamlit\production.db"

Write-Host ""
Write-Host "Starting Streamlit application in PRODUCTION mode on PORT 8501..." -ForegroundColor Magenta
Write-Host "=============================================================================" -ForegroundColor Magenta

# Start Streamlit app in background with explicit port and production settings
Start-Process -WindowStyle Minimized -FilePath "streamlit" -ArgumentList "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0" -WorkingDirectory "D:\Git\myhealthteam2\Streamlit"

# Start monitor script in background with correct path
Start-Process -WindowStyle Minimized -FilePath "python" -ArgumentList "streamlit_monitor.py" -WorkingDirectory "D:\Git\myhealthteam2\Streamlit"

Write-Host ""
Write-Host "=============================================================================" -ForegroundColor Green
Write-Host "PRODUCTION Streamlit app and monitor started on PORT 8501" -ForegroundColor Green
Write-Host "Application URL: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Monitor log: D:\Git\myhealthteam2\Streamlit\streamlit_monitor.log" -ForegroundColor Cyan
Write-Host "Database: D:\Git\myhealthteam2\Streamlit\production.db" -ForegroundColor Cyan
Write-Host "=============================================================================" -ForegroundColor Green
