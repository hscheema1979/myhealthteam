# Step 4: Transform and Validate Data
# This script runs the post-import transformation and validation steps

Write-Host "========================================="
Write-Host "STEP 4: TRANSFORM AND VALIDATE DATA"
Write-Host "========================================="
Write-Host "This will:"
Write-Host "1. Add new staff code mappings"
Write-Host "2. Run SQL transformation scripts"
Write-Host "3. Compare CSV vs database for validation"
Write-Host ""

# Check if we're in the scripts directory and database exists
if (!(Test-Path "../production.db")) {
    Write-Error "production.db not found. Please run steps 1-3 first."
    exit 1
}

# Step 4.1: Add new staff mappings
Write-Host "----------------------------------------"
Write-Host "4.1: Adding new staff code mappings..."
Write-Host "----------------------------------------"
cd ..
python "src/utils/add_new_staff_mappings.py"
$exitCode = $LASTEXITCODE
cd scripts
if ($exitCode -ne 0) { 
    Write-Error "Staff mapping failed"
    exit 1 
}
Write-Host "✓ Staff mappings updated"

Write-Host ""

# Step 4.2: Run SQL transformation scripts
Write-Host "----------------------------------------"
Write-Host "4.2: Running SQL transformation scripts..."
Write-Host "----------------------------------------"

$sqlScripts = @(
    "populate_coordinator_tasks.sql",
    "populate_coordinator_monthly_summary.sql", 
    "populate_provider_tasks_by_column.sql",
    "populate_provider_monthly_summary.sql",
    "populate_provider_weekly_summary.sql"
)

foreach ($script in $sqlScripts) {
    $scriptPath = "../src/sql/$script"
    if (Test-Path $scriptPath) {
        Write-Host "Running $script..."
        # Use sqlite3 with -init flag to read the SQL file
        sqlite3 -init "$scriptPath" "../production.db" ".quit"
        if ($LASTEXITCODE -ne 0) { 
            Write-Error "SQL script failed: $script"
            exit 1 
        }
        Write-Host "✓ $script completed"
    }
    else {
        Write-Warning "Script not found: $scriptPath"
    }
}

Write-Host ""

# Step 4.3: Validation and comparison
Write-Host "----------------------------------------"
Write-Host "4.3: Running validation checks..."
Write-Host "----------------------------------------"
cd ..
python "src/utils/compare_csv_vs_database.py"
$exitCode = $LASTEXITCODE
cd scripts
if ($exitCode -ne 0) { 
    Write-Error "Validation failed"
    exit 1 
}
Write-Host "✓ Validation completed"

Write-Host ""
Write-Host "========================================="
Write-Host "  STEP 4 COMPLETED SUCCESSFULLY!"
Write-Host "========================================="
Write-Host "Data transformation and validation complete."
Write-Host "The following tables have been populated:"
Write-Host "- coordinator_tasks"
Write-Host "- coordinator_monthly_summary"
Write-Host "- provider_tasks (by column)"
Write-Host "- provider_monthly_summary" 
Write-Host "- provider_weekly_summary"
Write-Host ""
Write-Host "Your data is now ready for the Streamlit dashboard!"
