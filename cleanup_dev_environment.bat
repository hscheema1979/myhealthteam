@echo off
REM Clean up development environment files for Admin Dashboard Testing

echo ===============================================
echo Cleaning up Development Environment Files
echo ===============================================
echo.

REM Remove test database files
if exist "test_admin_enhancements.db" (
    echo Removing test database...
    del test_admin_enhancements.db
    echo ✅ Test database removed
) else (
    echo ℹ️ Test database not found
)

REM Remove test database backups
for %%f in (test_admin_enhancements_backup_*.db) do (
    if exist "%%f" (
        echo Removing backup: %%f
        del "%%f"
    )
)

REM Remove development scripts
if exist "start_test_environment.bat" (
    del start_test_environment.bat
    echo ✅ start_test_environment.bat removed
)

if exist "test_admin_enhancements.bat" (
    del test_admin_enhancements.bat
    echo ✅ test_admin_enhancements.bat removed
)

REM Remove documentation
if exist "SAFE_TESTING_GUIDE.md" (
    del SAFE_TESTING_GUIDE.md
    echo ✅ SAFE_TESTING_GUIDE.md removed
)

if exist "DEV_ENVIRONMENT_SETUP.md" (
    del DEV_ENVIRONMENT_SETUP.md
    echo ✅ DEV_ENVIRONMENT_SETUP.md removed
)

REM Remove environment setup files
if exist "src\test_config.py" (
    del src\test_config.py
    echo ✅ src\test_config.py removed
)

if exist "src\test_environment_setup.py" (
    del src\test_environment_setup.py
    echo ✅ src\test_environment_setup.py removed
)

echo.
echo 🎯 Development environment cleanup complete!
echo 📋 Note: The .gitignore entries remain for future development.
echo.
pause