# Step 4a: Patient Import Phase
#
# Workflow Overview (2025-09):
#   1. Import patients (populate_patients.sql)
#   2. Import patient assignments (populate_patient_assignments.sql)
#   3. Import patient panel (populate_patient_panel.sql)
#
# This script is part 1 of 3 for the full transformation workflow:
#   - 4a-transform.ps1 (this script): Patient import
#   - 4b-transform.ps1: Task transformation
#   - 4c-transform.ps1: Visits, summary, and reporting
#
# See the other scripts for the remaining steps.

param(
    [string]$DatabasePath = "..\production.db",
    [switch]$Force = $false
)

Write-Host "==============================="
Write-Host "Step 4a: Patient Import Phase"
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

$success1 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_patients.sql" -Description "Populating patients table"
if (-not $success1 -and -not $Force) { exit 1 }

$success2 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_patient_assignments.sql" -Description "Populating patient assignments"
if (-not $success2 -and -not $Force) { exit 1 }

$success3 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_patient_panel.sql" -Description "Populating patient panel"
if (-not $success3 -and -not $Force) { exit 1 }

Write-Host "Step 4a complete. Continue with 4b-transform.ps1."
