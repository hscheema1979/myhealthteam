# Step 4b: Task Transformation Phase
#
# Workflow Overview (2025-09):
#   1. Import patients (populate_patients.sql)
#   2. Import patient assignments (populate_patient_assignments.sql)
#   3. Import patient panel (populate_patient_panel.sql)
#   4. Transform coordinator tasks (populate_coordinator_tasks.sql)
#   5. Transform provider tasks (populate_provider_tasks.sql)
#   6. Migrate phone review tasks from coordinator_tasks to provider_tasks (populate_provider_tasks_from_coordinator.sql)
#   7. Transform monthly provider/coordinator tasks for each month (populate_provider_coordinator_tasks_YYYY_MM.sql, e.g., 2025_01 to 2025_09)
#
# This script is part 2 of 3 for the full transformation workflow:
#   - 4a-transform.ps1: Patient import
#   - 4b-transform.ps1 (this script): Task transformation
#   - 4c-transform.ps1: Visits, summary, and reporting
#
# See the other scripts for the remaining steps.

param(
    [string]$DatabasePath = "..\production.db",
    [switch]$Force = $false
)

Write-Host "==============================="
Write-Host "Step 4b: Task Transformation Phase"
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
        } else {
            Write-Host "ERROR in $Description (Exit code: $LASTEXITCODE)"
            if ($result) { Write-Host "   Error details: $result" }
            return $false
        }
    } catch {
        Write-Host "EXCEPTION in $Description : $($_.Exception.Message)"
        return $false
    }
}

$success1 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_coordinator_tasks.sql" -Description "Transforming coordinator tasks"
if (-not $success1 -and -not $Force) { exit 1 }

$success2 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_provider_tasks.sql" -Description "Transforming provider tasks"
if (-not $success2 -and -not $Force) { exit 1 }

$success3 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_provider_tasks_from_coordinator.sql" -Description "Migrating phone review tasks from coordinator_tasks to provider_tasks"
if (-not $success3 -and -not $Force) { exit 1 }

$monthlyScripts = @(
    "2025_01", "2025_02", "2025_03", "2025_04", "2025_05", "2025_06", "2025_07", "2025_08", "2025_09"
)
foreach ($month in $monthlyScripts) {
    $scriptPath = "..\src\sql\populate_provider_coordinator_tasks_${month}.sql"
    $desc = "Transforming provider/coordinator tasks for $month"
    $result = Invoke-SQLScript -ScriptPath $scriptPath -Description $desc
    if (-not $result -and -not $Force) { exit 1 }
}

Write-Host "Step 4b complete. Continue with 4c-transform.ps1."
