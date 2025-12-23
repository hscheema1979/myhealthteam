@echo off
chcp 65001 >nul
echo ========================================
echo   PyGWalker - Data Visualization Tool
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "production.db" (
    echo ERROR: production.db not found!
    echo Please run this from D:\Git\myhealthteam2\Dev
    echo.
    pause
    exit /b 1
)

REM Check if the PyGWalker script exists
if not exist "simple_pygwalker.py" (
    echo ERROR: simple_pygwalker.py not found!
    echo Make sure all files are in place.
    echo.
    pause
    exit /b 1
)

REM Try using conda first (has pygwalker installed)
where conda >nul 2>nul
if %errorlevel% equ 0 (
    echo Using conda environment...
    echo.
    conda run -n base python simple_pygwalker.py
    if %errorlevel% equ 0 (
        echo.
        echo PyGWalker started successfully!
    ) else (
        echo.
        echo ERROR: Failed to start PyGWalker with conda
        echo Trying system Python...
        echo.
        python simple_pygwalker.py
    )
) else (
    echo Using system Python...
    echo.
    python simple_pygwalker.py
)

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo  TROUBLESHOOTING
    echo ========================================
    echo.
    echo If you see "No module named 'pygwalker'", install it:
    echo.
    echo Using conda:
    echo   conda install -c conda-forge pygwalker pandas
    echo.
    echo Using pip:
    echo   pip install pygwalker pandas
    echo.
    pause
)

echo.
echo ========================================
echo  PyGWalker has been closed
echo ========================================
pause
