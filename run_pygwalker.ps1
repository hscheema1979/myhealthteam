# PyGWalker PowerShell Launcher
# Run this script to start PyGWalker with all unified views

Write-Host "========================================" -ForegroundColor Green
Write-Host "  PyGWalker - Data Visualization Tool  " -ForegroundColor Green
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

# Check if the PyGWalker script exists
if (-not (Test-Path "simple_pygwalker.py")) {
    Write-Host "ERROR: simple_pygwalker.py not found!" -ForegroundColor Red
    Write-Host "Make sure all files are in place." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
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

# Check if pygwalker is installed
try {
    python -c "import pygwalker" 2>&1 | Out-Null
    Write-Host "PyGWalker is installed" -ForegroundColor Green
} catch {
    Write-Host "WARNING: PyGWalker not found!" -ForegroundColor Yellow
    Write-Host "You may need to install it:" -ForegroundColor Yellow
    Write-Host "  conda install -c conda-forge pygwalker" -ForegroundColor White
    Write-Host "  OR" -ForegroundColor White
    Write-Host "  pip install pygwalker" -ForegroundColor White
    Write-Host ""
}

Write-Host ""
Write-Host "Starting PyGWalker..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Features:" -ForegroundColor Cyan
Write-Host "- Loads all 7 unified views" -ForegroundColor White
Write-Host "- Interactive drag-and-drop visualization" -ForegroundColor White
Write-Host "- Filter by '_view_name' column" -ForegroundColor White
Write-Host "- Export charts and data" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop (if it hangs)" -ForegroundColor Yellow
Write-Host ""

# Try using conda first (has pygwalker installed)
$condaPath = Get-Command conda -ErrorAction SilentlyContinue
if ($condaPath) {
    Write-Host "Using conda environment..." -ForegroundColor Green
    Write-Host ""
    conda run -n base python simple_pygwalker.py
} else {
    Write-Host "Using system Python..." -ForegroundColor Green
    Write-Host ""
    python simple_pygwalker.py
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  TROUBLESHOOTING" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "If you see 'No module named pygwalker':" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Using conda:" -ForegroundColor White
    Write-Host "  conda install -c conda-forge pygwalker pandas" -ForegroundColor White
    Write-Host ""
    Write-Host "Using pip:" -ForegroundColor White
    Write-Host "  pip install pygwalker pandas" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  PyGWalker has been closed" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to close"
