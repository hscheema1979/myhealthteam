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
    [string]$StagingDatabasePath = ".\sheets_data.db",
    [switch]$RunMonthlyPartitions = $false,
    [switch]$Force = $false
)

Write-Host "==============================="
Write-Host "Step 4b: Task Transformation Phase"
Write-Host "==============================="
Write-Host "Database: $DatabasePath"
Write-Host "Staging: $StagingDatabasePath"
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Attach staging DB and create temp views for SOURCE_* tables (for this session only)
try {
    sqlite3 $DatabasePath "ATTACH '$StagingDatabasePath' AS staging;" 2>$null
    sqlite3 $DatabasePath "CREATE TEMP VIEW IF NOT EXISTS SOURCE_COORDINATOR_TASKS_HISTORY AS SELECT * FROM staging.source_coordinator_tasks_history;" 2>$null
    sqlite3 $DatabasePath "CREATE TEMP VIEW IF NOT EXISTS SOURCE_PROVIDER_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_PROVIDER_TASKS_HISTORY;" 2>$null
    Write-Host "Attached staging and created TEMP SOURCE_* views" -ForegroundColor Green
}
catch {
    Write-Host "ERROR: Could not attach staging DB or create temp views: $($_.Exception.Message)" -ForegroundColor Red
    if (-not $Force) { exit 1 }
}

function Invoke-SQLScript {
    param(
        [string]$ScriptPath,
        [string]$Description,
        [string]$PreSql = ""
    )
    Write-Host "Running: $Description ($ScriptPath)"
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "ERROR: Script not found: $ScriptPath"
        return $false
    }
    try {
        $scriptContent = Get-Content $ScriptPath -Raw
        $fullSql = $PreSql + "`n" + $scriptContent
        $tempFile = Join-Path $env:TEMP ("temp_sql_" + [System.Guid]::NewGuid().ToString() + ".sql")
        Set-Content -Path $tempFile -Value $fullSql -Encoding Ascii
        $result = sqlite3 $DatabasePath ".read $tempFile" 2>&1
        Remove-Item $tempFile -ErrorAction SilentlyContinue
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

# SAFETY: Use staging task transforms that DO NOT touch curated base tables
$preSql = @("ATTACH '" + $StagingDatabasePath + "' AS staging;","CREATE TEMP VIEW IF NOT EXISTS SOURCE_COORDINATOR_TASKS_HISTORY AS SELECT * FROM staging.source_coordinator_tasks_history;","CREATE TEMP VIEW IF NOT EXISTS SOURCE_PROVIDER_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_PROVIDER_TASKS_HISTORY;") -join "`n"
$success1 = Invoke-SQLScript -ScriptPath "$PSScriptRoot/../src/sql/staging_coordinator_tasks.sql" -Description "Building staging_coordinator_tasks from SOURCE_COORDINATOR_TASKS_HISTORY" -PreSql $preSql
if (-not $success1 -and -not $Force) { exit 1 }

$success2 = Invoke-SQLScript -ScriptPath "$PSScriptRoot/../src/sql/staging_provider_tasks.sql" -Description "Building staging_provider_tasks from SOURCE_PROVIDER_TASKS_HISTORY" -PreSql $preSql
if (-not $success2 -and -not $Force) { exit 1 }

# SKIP risky migration into base provider_tasks (staging only)
Write-Host "Skipping populate_provider_tasks_from_coordinator.sql in staging mode to avoid modifying curated provider_tasks" -ForegroundColor Yellow

if ($RunMonthlyPartitions) {
    $monthlyScripts = @(
        "2025_10", "2025_11", "2025_12"
    )

    foreach ($month in $monthlyScripts) {
        # Self-contained monthly scripts: no PreSql; just check source table existence in staging DB
        $cmExists = sqlite3 $StagingDatabasePath "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='SOURCE_CM_TASKS_${month}';" 2>$null
        $pslExists = sqlite3 $StagingDatabasePath "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='SOURCE_PSL_TASKS_${month}';" 2>$null

        if (([int]$cmExists -eq 0) -and ([int]$pslExists -eq 0)) {
            Write-Host "Skipping ${month}: No SOURCE_CM_TASKS_${month} or SOURCE_PSL_TASKS_${month} found in staging" -ForegroundColor Yellow
            continue
        }

        $scriptPath = "$PSScriptRoot/../src/sql/populate_provider_coordinator_tasks_${month}.sql"
        $desc = "Transforming provider/coordinator tasks for $month (WARNING: may overwrite monthly tables)"
        $result = Invoke-SQLScript -ScriptPath $scriptPath -Description $desc -PreSql ""
        if (-not $result -and -not $Force) { exit 1 }
    }
}

Write-Host "Step 4b complete (staging-safe). Continue with 4c-transform.ps1 or validation."
