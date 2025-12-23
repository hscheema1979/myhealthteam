@echo off
chcp 65001 >nul
echo ========================================
echo   Datasette - SQLite Database Browser
echo   WITH DASHBOARDS
echo ========================================
echo.
echo Starting Datasette on http://localhost:8001
echo.
echo Features:
echo - Browse all tables and views
echo - Run SQL queries in browser
echo - 3 PRE-BUILT DASHBOARDS with charts
echo - Create your own charts and visualizations
echo - Export data as CSV/JSON
echo - Shareable links
echo.
echo Dashboards Available:
echo 1. Healthcare Metrics Overview
echo 2. Coordinator Performance Dashboard
echo 3. Provider Performance Dashboard
echo 4. Facility Metrics Dashboard
echo.

REM Check if production.db exists
if not exist "production.db" (
    echo ERROR: production.db not found!
    echo Make sure you're running from D:\Git\myhealthteam2\Dev
    echo.
    pause
    exit /b 1
)

REM Check if dashboard.yml exists
if not exist "dashboard.yml" (
    echo WARNING: dashboard.yml not found!
    echo Dashboards will not be available.
    echo.
)

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH!
    echo.
    pause
    exit /b 1
)

REM Check if Datasette is installed
python -c "import datasette" 2>nul
if errorlevel 1 (
    echo ERROR: Datasette not installed!
    echo Install with: pip install datasette datasette-vega datasette-dashboards
    echo.
    pause
    exit /b 1
)

echo Starting Datasette with dashboards...
echo.
echo Press Ctrl+C to stop the server
echo.
echo Open your browser to: http://localhost:8001
echo Dashboards will be at: http://localhost:8001/-/dashboards
echo.

REM Start Datasette with our database and dashboards
datasette production.db ^
  --port 8001 ^
  --setting sql_time_limit_ms 10000 ^
  --setting default_page_size 50 ^
  --setting max_returned_rows 10000 ^
  --setting allow_download on ^
  --metadata dashboard.yml

if errorlevel 1 (
    echo.
    echo ========================================
    echo   TROUBLESHOOTING
    echo ========================================
    echo.
    echo If port 8001 is in use, try:
    echo   datasette production.db --port 8002 --metadata dashboard.yml
    echo.
    echo To install required packages:
    echo   pip install datasette datasette-vega datasette-dashboards
    echo.
    echo If dashboards don't load, check dashboard.yml exists.
    echo.
    pause
)

pause
