# Master Data Import and Transform Orchestrator
# This script runs the complete 4-step data workflow
param(
    [string]$spreadsheetId = "1-heDIbBHykxfwGl7U9YYIjQo7o5PbOVZL-VahyvG8_k",
    [switch]$AllMonths = $false,
    [switch]$Step1 = $false,
    [switch]$Step2 = $false,
    [switch]$Step3 = $false,
    [switch]$Step4 = $false
)

[string]$yearMonth = (Get-Date -Format 'yyyy_MM')
if ($AllMonths) {
    Write-Host "Batch mode: All months will be processed in transformation step." -ForegroundColor Cyan
}
else {
    Write-Host "Current month for update: $yearMonth" -ForegroundColor Cyan
}

# Determine which steps to run
$runAll = -not ($Step1 -or $Step2 -or $Step3 -or $Step4)

Write-Host "DEBUG: Step switches - Step1: $Step1, Step2: $Step2, Step3: $Step3, Step4: $Step4, runAll: $runAll" -ForegroundColor Cyan

Write-Host "========================================="
Write-Host "  COMPLETE DATA WORKFLOW ORCHESTRATOR"
Write-Host "========================================="
Write-Host "This will run the complete 4-step process:"
Write-Host "1. Download all CSV files from Google Sheets"
Write-Host "2. Consolidate files into cmlog.csv and psl.csv" 
Write-Host "3. Import consolidated data to production.db"
Write-Host "4. Transform data and run validation"
Write-Host ""
Write-Host "Transformation mode: $(if ($AllMonths) { 'All Months Batch' } else { 'Single Month' })" -ForegroundColor Yellow

# Check if we're in the scripts directory
if (!(Test-Path "1_download_files_complete.ps1")) {
    Write-Host "WARNING: Not running from scripts directory. Attempting to run anyway..." -ForegroundColor Yellow
}

# Step 1: Download files
if ($runAll -or $Step1) {
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
}

# Step 2: Consolidate files
if ($runAll -or $Step2) {
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
}

# Step 3: Import to database
if ($runAll -or $Step3) {
    Write-Host "========================================="
    Write-Host "STEP 3: IMPORTING TO DATABASE"
    Write-Host "========================================="
    try {
        if ($AllMonths) {
            & .\3_import_to_database.ps1 -AllMonths
        }
        else {
            & .\3_import_to_database.ps1
        }
        if ($LASTEXITCODE -ne 0) { throw "Database import failed" }
        Write-Host "✓ Step 3 completed successfully"
    }
    catch {
        Write-Error "Step 3 failed: $_"
        exit 1
    }
    Write-Host ""
}

# Step 4: Transform and validate
if ($runAll -or $Step4) {
    Write-Host "========================================="
    Write-Host "STEP 4: ENHANCED TRANSFORM AND VALIDATE"
    Write-Host "========================================="
    try {
        if ($AllMonths) {
            & .\4_transform_data_enhanced_differential.ps1 -AllMonths
        }
        else {
            & .\4_transform_data_enhanced_differential.ps1 -YearMonth $yearMonth
        }
        if ($LASTEXITCODE -ne 0) { throw "Transformation failed" }
        Write-Host "✓ Step 4 completed successfully"
    }
    catch {
        Write-Error "Step 4 failed: $_"
        exit 1
    }
    Write-Host ""
}
Write-Host "========================================="
Write-Host "  COMPLETE WORKFLOW FINISHED!"
Write-Host "========================================="
Write-Host "All 4 steps completed successfully:"
Write-Host "✓ Data downloaded from Google Sheets"
Write-Host "✓ Files consolidated (cmlog.csv, psl.csv)"
Write-Host "✓ Raw data imported to staging tables"
Write-Host "✓ Enhanced data transformation with complete patient processing"
Write-Host "✓ All patient foreign key relationships established"
Write-Host "✓ Missing facilities created automatically"
Write-Host ""
Write-Host "Your production.db is now fully updated and ready!"
Write-Host "You can run the Streamlit dashboard to view the data."
Write-Host ""
Write-Host "Usage:"
Write-Host "  .\run_complete_workflow.ps1" -ForegroundColor Yellow
Write-Host "  .\run_complete_workflow.ps1 -AllMonths" -ForegroundColor Yellow
Write-Host "  .\run_complete_workflow.ps1 -Step1 -Step3" -ForegroundColor Yellow
Write-Host "  .\run_complete_workflow.ps1 -Step2 -Step4 -AllMonths" -ForegroundColor Yellow
Write-Host ""
Write-Host "-AllMonths: Run transformation for all available months (batch mode)"
Write-Host "-Step1: Run only Step 1 (download files)"
Write-Host "-Step2: Run only Step 2 (consolidate files)"
Write-Host "-Step3: Run only Step 3 (import to database)"
Write-Host "-Step4: Run only Step 4 (transform and validate)"