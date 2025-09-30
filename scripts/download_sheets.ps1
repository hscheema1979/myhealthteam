# Master Data Import Orchestrator
# This script runs the complete data import workflow in sequence
param(
    [string]$spreadsheetId = "1-heDIbBHykxfwGl7U9YYIjQo7o5PbOVZL-VahyvG8_k"
)

Write-Host "========================================="
Write-Host "  MASTER DATA IMPORT WORKFLOW"
Write-Host "========================================="
Write-Host "This will run the complete 3-step process:"
Write-Host "1. Download all CSV files from Google Sheets"
Write-Host "2. Consolidate files into cmlog.csv and psl.csv" 
Write-Host "3. Import consolidated data to production.db"
Write-Host ""

# Check if we're in the scripts directory
if (!(Test-Path "1_download_files_complete.ps1")) {
    Write-Error "Please run this script from the scripts directory"
    exit 1
}

# Step 1: Download files
Write-Host "========================================="
Write-Host "STEP 1: DOWNLOADING FILES"
Write-Host "========================================="
try {
    & .\1_download_files_complete.ps1 -spreadsheetId $spreadsheetId
    if ($LASTEXITCODE -ne 0) { throw "Download failed" }
    Write-Host "✓ Step 1 completed successfully"
}
catch {
    Write-Error "Step 1 failed: $_"
    exit 1
}

Write-Host ""

# Step 2: Consolidate files
Write-Host "========================================="
Write-Host "STEP 2: CONSOLIDATING FILES"
Write-Host "========================================="
try {
    & .\2_consolidate_files.ps1
    if ($LASTEXITCODE -ne 0) { throw "Consolidation failed" }
    Write-Host "✓ Step 2 completed successfully"
}
catch {
    Write-Error "Step 2 failed: $_"
    exit 1
}

Write-Host ""

# Step 3: Import to database
Write-Host "========================================="
Write-Host "STEP 3: IMPORTING TO DATABASE"
Write-Host "========================================="
try {
    & .\3_import_to_database.ps1
    if ($LASTEXITCODE -ne 0) { throw "Database import failed" }
    Write-Host "✓ Step 3 completed successfully"
}
catch {
    Write-Error "Step 3 failed: $_"
    exit 1
}

Write-Host ""
Write-Host "========================================="
Write-Host "  WORKFLOW COMPLETED SUCCESSFULLY!"
Write-Host "========================================="
Write-Host "Data has been imported to production.db:"
Write-Host "- source_coordinator_tasks_history"
Write-Host "- source_provider_tasks_history" 
Write-Host "- SOURCE_PATIENT_DATA"
Write-Host ""
Write-Host "You can now run the Streamlit app to view the data."