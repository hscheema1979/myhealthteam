# Datasette PowerShell Launcher with Dashboards
# Run this script to start Datasette on http://localhost:8001

Write-Host "========================================" -ForegroundColor Green
Write-Host "  Datasette - SQLite Database Browser  " -ForegroundColor Green
Write-Host "        WITH PRE-BUILT DASHBOARDS      " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Check if production.db exists
if (-not (Test-Path "production.db")) {
    Write-Host "ERROR: production.db not found!" -ForegroundColor Red
    Write-Host "Make sure you're running from D:\Git\myhealthteam2\Dev" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if dashboard.yml exists
if (-not (Test-Path "dashboard.yml")) {
    Write-Host "WARNING: dashboard.yml not found!" -ForegroundColor Yellow
    Write-Host "Dashboards will not be available." -ForegroundColor Yellow
    Write-Host ""
}

# Check for Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found in PATH!" -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if Datasette is installed
try {
    python -c "import datasette" 2>&1 | Out-Null
    Write-Host "Datasette is installed" -ForegroundColor Green
} catch {
    Write-Host
