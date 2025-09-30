param(
    [string]$DatabasePath = "production.db",
    [string]$YearMonth = "2025_09",
    [int]$Year = 2025,
    [int]$Month = 9,
    [int]$Week = 35
)

$YearMonthFormatted = "{0:D4}_{1:D2}" -f $Year, $Month
$WeekFormatted = "{0:D4}_{1:D2}" -f $Year, $Week

Write-Host "Creating and populating summary tables for $YearMonthFormatted" -ForegroundColor Green
Write-Host "Database: $DatabasePath" -ForegroundColor Yellow

# 1. Create summary tables
Write-Host "Step 1: Creating summary tables..." -ForegroundColor Cyan
$sqlCreate = Get-Content "src\sql\create_summary_tables_2025_09.sql" -Raw
$sqlCreate | sqlite3 $DatabasePath

# 2. Populate coordinator monthly summary
Write-Host "Step 2: Populating coordinator monthly summary..." -ForegroundColor Cyan
$sqlCoordinatorMonthly = Get-Content "src\sql\populate_coordinator_monthly_summary_2025_09.sql" -Raw
$sqlCoordinatorMonthly | sqlite3 $DatabasePath

# 3. Populate coordinator minutes summary
Write-Host "Step 3: Populating coordinator minutes summary..." -ForegroundColor Cyan
$sqlCoordinatorMinutes = Get-Content "src\sql\populate_coordinator_minutes_2025_09.sql" -Raw
$sqlCoordinatorMinutes | sqlite3 $DatabasePath

# 4. Populate provider weekly summary
Write-Host "Step 4: Populating provider weekly summary..." -ForegroundColor Cyan
$sqlProviderWeekly = Get-Content "src\sql\populate_provider_weekly_summary_2025_35.sql" -Raw
$sqlProviderWeekly | sqlite3 $DatabasePath

# 5. Update patient panel last visit
Write-Host "Step 5: Updating patient panel last visit information..." -ForegroundColor Cyan
$sqlUpdatePanel = Get-Content "src\sql\update_patient_panel_last_visit.sql" -Raw
$sqlUpdatePanel | sqlite3 $DatabasePath

Write-Host "Summary tables creation and population completed!" -ForegroundColor Green
Write-Host "Created tables:" -ForegroundColor Yellow
Write-Host "  - coordinator_monthly_summary_$YearMonthFormatted" -ForegroundColor White
Write-Host "  - coordinator_minutes_$YearMonthFormatted" -ForegroundColor White
Write-Host "  - provider_weekly_summary_$WeekFormatted" -ForegroundColor White
Write-Host "Updated:" -ForegroundColor Yellow
Write-Host "  - patient_panel (last_visit_date, last_visit_provider_id, last_visit_provider_name)" -ForegroundColor White