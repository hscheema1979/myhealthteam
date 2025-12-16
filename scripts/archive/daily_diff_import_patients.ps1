# PowerShell script to automate daily diff import for patients (template for other tables)
# Usage: .\daily_diff_import_patients.ps1 <year> <month>
param(
    [string]$Year = (Get-Date -Format 'yyyy'),
    [string]$Month = (Get-Date -Format 'MM')
)

$ErrorActionPreference = 'Stop'

Write-Host "=== DAILY DIFF IMPORT: PATIENTS ==="

# 1. Export current month's data from DB
Write-Host "Exporting current month's data from DB..."
python "../src/utils/export_table_month_to_csv.py" "patients" $Year $Month "../exports/patients_${Year}_${Month}.csv"

# 2. Download and consolidate latest data (reuse existing scripts)
Write-Host "Downloading and consolidating latest data..."
& ./1_download_files_complete.ps1
& ./2_consolidate_files.ps1

# 3. Compare DB export with latest ZMO_Main.csv to get diff
Write-Host "Comparing DB export with latest ZMO_Main.csv to get diff..."
# Key columns for patients: Pt Name, Admit Date (adjust as needed)
python "../src/utils/csv_diff.py" "../exports/patients_${Year}_${Month}.csv" "../downloads/patients/ZMO_Main.csv" "Pt Name,Admit Date" "../exports/patients_diff_${Year}_${Month}.csv"

# 4. Import only the diff to staging table
Write-Host "Importing only the diff to SOURCE_PATIENT_DATA..."
python "../src/utils/csv_to_sql.py" "../exports/patients_diff_${Year}_${Month}.csv" -s "../production.db" -t "SOURCE_PATIENT_DATA" --skip-empty-columns

# 5. Run transformation for just the new/changed data (reuse existing step 4)
Write-Host "Running transformation scripts (Step 4)..."
& ./4_transform_data_enhanced.ps1

Write-Host "=== DAILY DIFF IMPORT COMPLETE ==="
