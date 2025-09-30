# Step 4c: Visits, Summary, and Reporting Phase
#
# Workflow Overview (2025-09):
#   1. Import patients (populate_patients.sql)
#   2. Import patient assignments (populate_patient_assignments.sql)
#   3. Import patient panel (populate_patient_panel.sql)
#   4. Transform coordinator tasks (populate_coordinator_tasks.sql)
#   5. Transform provider tasks (populate_provider_tasks.sql)
#   6. Migrate phone review tasks from coordinator_tasks to provider_tasks (populate_provider_tasks_from_coordinator.sql)
#   7. Transform monthly provider/coordinator tasks for each month (populate_provider_coordinator_tasks_YYYY_MM.sql, e.g., 2025_01 to 2025_09)
#   8. Create patient visits (create_patient_visits.sql)
#   9. Update last visit info (update_last_visit.sql)
#  10. Update summary tables (populate_summary_tables.sql, populate_coordinator_monthly_summary.sql, populate_provider_monthly_summary.sql)
#  11. Analyze staff mapping effectiveness and unmapped staff
#  12. Output pre- and post-transformation status for key tables
#
# This script is part 3 of 3 for the full transformation workflow:
#   - 4a-transform.ps1: Patient import
#   - 4b-transform.ps1: Task transformation
#   - 4c-transform.ps1 (this script): Visits, summary, and reporting
#
# See the other scripts for the remaining steps.

param(
    [string]$DatabasePath = "..\production.db",
    [switch]$Force = $false
)

Write-Host "==============================="
Write-Host "Step 4c: Visits, Summary, and Reporting Phase"
Write-Host "==============================="
Write-Host "Database: $DatabasePath"
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

function Invoke-SQLScript {
    param(
        [string]$ScriptPath,
        [string]$Description
    )
    Write-Host "Running: $Description ($ScriptPath)"
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "ERROR: Script not found: $ScriptPath"
        return $false
    }
    try {
        $result = Get-Content $ScriptPath | sqlite3 $DatabasePath 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Success: $Description"
            return $true
        }
        else {
            Write-Host "ERROR in $Description (Exit code: $LASTEXITCODE)"
            if ($result) { Write-Host "   Error details: $result" }
            return $false
        }
    }
    catch {
        Write-Host "EXCEPTION in $Description : $($_.Exception.Message)"
        return $false
    }
}

# Pre-transformation status
function Get-TableCount {
    param([string]$TableName)
    try {
        $count = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $TableName;" 2>$null
        return [int]$count
    }
    catch {
        return 0
    }
}

Write-Host "Pre-transformation Status:"
$prePatients = Get-TableCount "patients"
$preFacilities = Get-TableCount "facilities"
$preAssignments = Get-TableCount "patient_assignments"
$preUserAssignments = Get-TableCount "user_patient_assignments"
$preCarePlans = Get-TableCount "care_plans"
Write-Host "   Patients: $prePatients"
Write-Host "   Facilities: $preFacilities"
Write-Host "   Patient Assignments: $preAssignments"
Write-Host "   User-Patient Assignments: $preUserAssignments"
Write-Host "   Care Plans: $preCarePlans"
Write-Host ""

$success1 = Invoke-SQLScript -ScriptPath "..\src\sql\create_patient_visits.sql" -Description "Creating patient visits"
if (-not $success1 -and -not $Force) { exit 1 }

$success2 = Invoke-SQLScript -ScriptPath "..\src\sql\update_last_visit.sql" -Description "Updating last visit info"
if (-not $success2 -and -not $Force) { exit 1 }

$success3 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_summary_tables.sql" -Description "Updating summary tables"
$success4 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_coordinator_monthly_summary.sql" -Description "Updating coordinator monthly summaries"

$success5 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_provider_monthly_summary.sql" -Description "Updating provider monthly summaries"

# NEW: Provider weekly summary for pay and billing
$success6 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_provider_weekly_summary.sql" -Description "Updating provider weekly summaries (no billing codes/status)"

# NEW: Provider weekly summary WITH billing codes and status
$success7 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_provider_weekly_summary_with_billing.sql" -Description "Updating provider weekly summaries (with billing codes and status)"

Write-Host ""
Write-Host "Post-transformation Status:"
$postPatients = Get-TableCount "patients"
$postFacilities = Get-TableCount "facilities"
$postAssignments = Get-TableCount "patient_assignments"
$postUserAssignments = Get-TableCount "user_patient_assignments"
$postCarePlans = Get-TableCount "care_plans"
$postDashboardAssignments = Get-TableCount "dashboard_patient_assignment_summary"
$postCountyMappings = Get-TableCount "dashboard_patient_county_map"
$postZipMappings = Get-TableCount "dashboard_patient_zip_map"
Write-Host "   Patients: $postPatients (Delta: $($postPatients - $prePatients))"
Write-Host "   Facilities: $postFacilities (Delta: $($postFacilities - $preFacilities))"
Write-Host "   Patient Assignments: $postAssignments (Delta: $($postAssignments - $preAssignments))"
Write-Host "   User-Patient Assignments: $postUserAssignments (Delta: $($postUserAssignments - $preUserAssignments))"
Write-Host "   Care Plans: $postCarePlans (Delta: $($postCarePlans - $preCarePlans))"
Write-Host "   Dashboard Assignments: $postDashboardAssignments"
Write-Host "   County Mappings: $postCountyMappings"
Write-Host "   ZIP Code Mappings: $postZipMappings"
Write-Host ""

Write-Host "Staff Mapping Analysis:"
try {
    $mappingStats = sqlite3 $DatabasePath "SELECT confidence_level, COUNT(*) as count FROM staff_code_mapping GROUP BY confidence_level;" 2>$null
    if ($mappingStats) {
        $mappingStats -split "`n" | ForEach-Object {
            if ($_ -match '(.+)\|(.+)') {
                Write-Host "   $($matches[1]) confidence: $($matches[2]) mappings"
            }
        }
    }
    $unmappedCoordinators = sqlite3 $DatabasePath "SELECT COUNT(DISTINCT spd.`"Assigned CM`") FROM SOURCE_PATIENT_DATA spd WHERE spd.`"Assigned CM`" IS NOT NULL AND spd.`"Assigned CM`" != '' AND NOT EXISTS (SELECT 1 FROM staff_code_mapping scm WHERE LOWER(TRIM(spd.`"Assigned CM`")) = LOWER(TRIM(scm.staff_name)) AND scm.confidence_level = 'HIGH');" 2>$null
    if ($unmappedCoordinators) {
        Write-Host "   Unmapped coordinators: $unmappedCoordinators"
    }
}
catch {
    Write-Host "   Unable to analyze staff mappings"
}

Write-Host ""
Write-Host "Step 4c complete. Workflow finished."
