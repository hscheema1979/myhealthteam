# RESET AND REPOPULATE TASK TABLES WITH PROPER UNIQUE CONSTRAINTS
# This script will:
# 1. Drop all task tables and dependent tables
# 2. Recreate them with proper UNIQUE constraints
# 3. Re-run the transform script to repopulate data

Write-Host "=== RESET TASK TABLES WITH UNIQUE CONSTRAINTS ===" -ForegroundColor Yellow
Write-Host "WARNING: This will DELETE ALL TASK DATA!" -ForegroundColor Red
Write-Host "Make sure you have database backups before proceeding." -ForegroundColor Red
Write-Host ""

$confirmation = Read-Host "Do you want to continue? (yes/no)"
if ($confirmation -ne "yes") {
    Write-Host "Operation cancelled." -ForegroundColor Green
    exit
}

# Set working directory
Set-Location $PSScriptRoot

# Step 1: Run the SQL script to drop and recreate tables
Write-Host "Step 1: Dropping and recreating task tables..." -ForegroundColor Cyan
sqlite3 production.db ".read reset_task_tables.sql"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to reset tables!" -ForegroundColor Red
    exit 1
}

Write-Host "Tables reset successfully." -ForegroundColor Green

# Step 2: Re-run the transform script to repopulate data
Write-Host "Step 2: Repopulating data from CSV files..." -ForegroundColor Cyan
python transform_production_data_v3_fixed.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Transform script failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Data repopulation completed successfully." -ForegroundColor Green

# Step 3: Verify the tables have UNIQUE constraints
Write-Host "Step 3: Verifying UNIQUE constraints..." -ForegroundColor Cyan

$tables = sqlite3 production.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'coordinator_tasks_%';"
foreach ($table in $tables) {
    $constraint = sqlite3 production.db "PRAGMA table_info($table);" | Select-String "UNIQUE"
    if ($constraint) {
        Write-Host "✓ $table has UNIQUE constraint" -ForegroundColor Green
    } else {
        Write-Host "✗ $table missing UNIQUE constraint" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== RESET COMPLETE ===" -ForegroundColor Green
Write-Host "Task tables have been reset with proper UNIQUE constraints." -ForegroundColor Green
Write-Host "All data has been repopulated from CSV files." -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test the dashboards to ensure they work correctly" -ForegroundColor White
Write-Host "2. Verify that duplicate entries are now prevented" -ForegroundColor White
Write-Host "3. Check that billing and payroll calculations are accurate" -ForegroundColor White