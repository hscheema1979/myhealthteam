@echo off
REM Master wrapper script for running the unified import process
REM This script provides a simple interface for running the unified import

title Healthcare Dashboard - Unified Import Process
color 0A

echo.
echo ==========================================
echo  Healthcare Dashboard - Unified Import
echo ==========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and ensure it's available in PATH
    pause
    exit /b 1
)

echo Python found. Starting import process...
echo.

REM Ask user for start date (optional)
set /p start_date="Enter start date (YYYY-MM-DD) or press Enter for incremental (latest): "
if "%start_date%"=="" (
    set start_date_arg=
) else (
    set start_date_arg=--start-date %start_date%
)

REM Ask user if they want to skip backup
set /p skip_backup="Skip database backup? (y/N): "
if /i "%skip_backup%"=="y" (
    set backup_arg=--no-backup
) else (
    set backup_arg=
)

echo.
echo Starting import with options:
echo   Start Date: %start_date%
echo   Backup: %backup_arg%
echo.
echo This process will:
echo   1. Create database backup (if not skipped)
echo   2. Import CSV files to staging database
echo   3. Transform data using existing scripts
echo   4. Validate results
echo.

pause

REM Run the unified import script
python scripts\unified_import.py %start_date_arg% %backup_arg%

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo  Import completed successfully!
    echo ==========================================
    echo.
    echo Check the logs directory for detailed logs:
    echo   logs\unified_import_*.log
    echo.
    echo Next steps:
    echo   1. Review staging tables in sheets_data.db
    echo   2. Run verification scripts if needed
    echo   3. Consider promoting to production if satisfied
) else (
    echo.
    echo ==========================================
    echo  Import failed!
    echo ==========================================
    echo.
    echo Check the logs directory for error details:
    echo   logs\unified_import_*.log
    echo.
    echo Common issues:
    echo   1. Missing CSV files in downloads directory
    echo   2. Database permissions
    echo   3. Date format issues
)

echo.
pause
