# PowerShell script to automate daily diff import for coordinator_tasks (template for other tables)
# Usage: .\daily_diff_import_coordinator.ps1 <year> <month>
param(
    [string]$Year = (Get-Date -Format 'yyyy'),
    [string]$Month = (Get-Date -Format 'MM')
)

$ErrorActionPreference = 'Stop'

Write-Host "=== DAILY DIFF IMPORT: COORDINATOR TASKS ==="

# 1. Export current month's data from DB
Write-Host "Exporting current month's data from DB..."
python "../src/utils/export_table_month_to_csv.py" "coordinator_tasks" $Year $Month "../exports/coordinator_tasks_${Year}_${Month}.csv"

# 2. Download and consolidate latest data (reuse existing scripts)
Write-Host "Downloading and consolidating latest data..."
& ./1_download_files_complete.ps1
& ./2_consolidate_files.ps1

# 3. Compare DB export with latest cmlog.csv to get diff
Write-Host "Comparing DB export with latest cmlog.csv to get diff..."
# Key columns for coordinator_tasks: Staff, Pt Name, Date (adjust as needed)
python "../src/utils/csv_diff.py" "../exports/coordinator_tasks_${Year}_${Month}.csv" "../downloads/cmlog.csv" "Staff,Pt Name,Date" "../exports/coordinator_tasks_diff_${Year}_${Month}.csv"

# 4. Import only the diff to staging table
Write-Host "Importing only the diff to source_coordinator_tasks_history..."
python "../src/utils/csv_to_sql.py" "../exports/coordinator_tasks_diff_${Year}_${Month}.csv" -s "../production.db" -t "source_coordinator_tasks_history" -a --skip-empty-columns

# 5. Run transformation for just the new/changed data (reuse existing step 4)
Write-Host "Running transformation scripts (Step 4)..."
& ./4_transform_data_enhanced.ps1

Write-Host "=== DAILY DIFF IMPORT COMPLETE ==="
