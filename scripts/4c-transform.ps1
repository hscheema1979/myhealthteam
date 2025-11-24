# Step 4c: Visits, Summary, and Reporting Phase (Staging-Aware)
#
# This script finalizes the post-import transformations. By default it operates in STAGING-ONLY mode
# to prevent overwriting curated tables. It creates staging_* equivalents for visits and summaries.
#
# Use -StagingOnly:$false to run the legacy curated path (DANGEROUS). Only do this intentionally.

param(
    [string]$DatabasePath = "..\production.db",
    [string]$StagingDatabasePath = ".\sheets_data.db",
    [switch]$StagingOnly = $true,
    [switch]$Force = $false
)

Write-Host "==============================="
Write-Host "Step 4c: Visits, Summary, and Reporting Phase"
Write-Host "==============================="
Write-Host "Database: $DatabasePath"
Write-Host "Staging DB: $StagingDatabasePath"
$mode = "CURATED TABLES (DANGEROUS)"
if ($StagingOnly) { $mode = "STAGING-ONLY (SAFE)" }
Write-Host "Mode: $mode"
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

function Invoke-InlineSQL {
    param(
        [string]$Sql,
        [string]$Description
    )
    Write-Host "Running: $Description"
    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        Set-Content -Path $tmp -Value $Sql -Encoding UTF8
        $result = sqlite3 $DatabasePath ".read $tmp" 2>&1
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
    } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

function Invoke-SQLScript {
    param(
        [string]$ScriptPath,
        [string]$Description
    )
    Write-Host "Running: $Description ($ScriptPath)"
    if (-not (Test-Path $ScriptPath)) { Write-Host "ERROR: Script not found: $ScriptPath"; return $false }
    try {
        $result = Get-Content $ScriptPath | sqlite3 $DatabasePath 2>&1
        if ($LASTEXITCODE -eq 0) { Write-Host "Success: $Description"; return $true }
        else { Write-Host "ERROR in $Description (Exit code: $LASTEXITCODE)"; if ($result) { Write-Host "   Error details: $result" }; return $false }
    } catch { Write-Host "EXCEPTION in $Description : $($_.Exception.Message)"; return $false }
}

# Attach staging DB and expose useful TEMP VIEWs
try {
    sqlite3 $DatabasePath "ATTACH DATABASE '$StagingDatabasePath' AS staging;" 2>$null
    sqlite3 $DatabasePath "CREATE TEMP VIEW IF NOT EXISTS SOURCE_PATIENT_DATA AS SELECT * FROM staging.SOURCE_PATIENT_DATA;" 2>$null
    sqlite3 $DatabasePath "CREATE TEMP VIEW IF NOT EXISTS SOURCE_COORDINATOR_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_COORDINATOR_TASKS_HISTORY;" 2>$null
    sqlite3 $DatabasePath "CREATE TEMP VIEW IF NOT EXISTS SOURCE_PROVIDER_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_PROVIDER_TASKS_HISTORY;" 2>$null
} catch { Write-Host "WARN: Could not attach staging DB or create TEMP VIEWs." }

# Utility
# Helper: get table count (uses main database connection; staging tables are in main unless explicitly namespaced)
function Run-SQLQuery {
  param(
    [Parameter(Mandatory=$true)][string]$Sql
  )
  try {
    $result = sqlite3 $DatabasePath $Sql 2>&1
    if ($LASTEXITCODE -eq 0) { return $result }
    else { Write-Host "ERROR running query"; if ($result) { Write-Host "   Error details: $result" }; return $null }
  } catch { Write-Host "EXCEPTION running query: $($_.Exception.Message)"; return $null }
}

# Pre-run curated baseline snapshot (only when staging-only mode)
if ($StagingOnly) {
  Write-Host "[4c] Validation: capturing curated baseline counts before staging-only run"
  $global:CuratedBaseline = @{}
  $curatedCore = @('patients','patient_panel','patient_visits')
  foreach ($t in $curatedCore) { $global:CuratedBaseline[$t] = Get-TableCount -TableName $t }
  # Dynamically include monthly/summary curated tables if present
  $monthlyNamesRaw = Run-SQLQuery -Sql "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE 'coordinator_monthly_summary%' OR name LIKE 'provider_weekly_summary%' OR name LIKE 'provider_monthly_summary%' OR name LIKE 'coordinator_minutes%');"
  if ($monthlyNamesRaw) {
    $monthlyNames = $monthlyNamesRaw.Trim().Split([Environment]::NewLine) | Where-Object { $_ -ne '' }
    foreach ($t in $monthlyNames) { $global:CuratedBaseline[$t] = Get-TableCount -TableName $t }
  }
}

if ($StagingOnly) {
    Write-Host "Pre-transformation (staging) Status:"
    Write-Host "   staging_patients:            $(Get-TableCount 'staging_patients')"
    Write-Host "   staging_provider_tasks:      $(Get-TableCount 'staging_provider_tasks')"
    Write-Host "   staging_coordinator_tasks:   $(Get-TableCount 'staging_coordinator_tasks')"
    Write-Host "   staging_patient_panel:       $(Get-TableCount 'staging_patient_panel')"

    function Get-TableCount {
      param(
        [Parameter(Mandatory=$true)][string]$TableName
      )
      try {
        $existsRaw = sqlite3 $DatabasePath "SELECT COUNT(1) FROM sqlite_master WHERE type='table' AND name='$TableName';" 2>&1
        if ($LASTEXITCODE -ne 0) { return 0 }
        $exists = [int]($existsRaw.Trim().Split([Environment]::NewLine)[-1])
        if ($exists -eq 0) { return 0 }
        $countRaw = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $TableName;" 2>&1
        if ($LASTEXITCODE -ne 0) { return 0 }
        return $countRaw.Trim().Split([Environment]::NewLine)[-1]
      } catch { return 0 }
    }
    $sqlVisits = @'
    CREATE TABLE IF NOT EXISTS staging_patient_visits (
        patient_id TEXT PRIMARY KEY,
        last_visit_date TEXT,
        service_type TEXT
    );
    DELETE FROM staging_patient_visits;
    INSERT INTO staging_patient_visits (patient_id, last_visit_date, service_type)
    WITH norm AS (
        SELECT REPLACE(patient_name_raw, ',', '') AS patient_id,
               activity_date,
               service
        FROM staging_provider_tasks
    )
    , latest AS (
        SELECT patient_id, MAX(activity_date) AS last_visit_date
        FROM norm
        GROUP BY patient_id
    )
    SELECT latest.patient_id,
           latest.last_visit_date,
           MIN(n.service) AS service_type
    FROM latest
    LEFT JOIN norm n
      ON n.patient_id = latest.patient_id AND n.activity_date = latest.last_visit_date
    GROUP BY latest.patient_id, latest.last_visit_date;
'@
    $ok1 = Invoke-InlineSQL -Sql $sqlVisits -Description "Build staging_patient_visits"
    if (-not $ok1 -and -not $Force) { exit 1 }

    $sqlUpdatePanel = @'
    UPDATE staging_patient_panel
    SET last_visit_date = (
        SELECT v.last_visit_date FROM staging_patient_visits v
        WHERE v.patient_id = REPLACE(staging_patient_panel.last_name || ' ' || staging_patient_panel.first_name || ' ' || staging_patient_panel.date_of_birth, ',', '')
    ),
    last_visit_service_type = (
        SELECT v.service_type FROM staging_patient_visits v
        WHERE v.patient_id = REPLACE(staging_patient_panel.last_name || ' ' || staging_patient_panel.first_name || ' ' || staging_patient_panel.date_of_birth, ',', '')
    )
    WHERE EXISTS (
        SELECT 1 FROM staging_patient_visits v
        WHERE v.patient_id = REPLACE(staging_patient_panel.last_name || ' ' || staging_patient_panel.first_name || ' ' || staging_patient_panel.date_of_birth, ',', '')
    );
'@

    $panelExists = Run-SQLQuery -Sql "SELECT CASE WHEN EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='staging_patient_panel') THEN 1 ELSE 0 END;"
    if ($panelExists -and ([int]($panelExists.Trim().Split([Environment]::NewLine)[-1]) -eq 1)) {
        $ok2 = Invoke-InlineSQL -Sql $sqlUpdatePanel -Description "Update staging_patient_panel last visit fields"
        if (-not $ok2 -and -not $Force) { exit 1 }
    }
    else {
        Write-Host "Skipping update of staging_patient_panel: table does not exist" -ForegroundColor Yellow
    }

    $sqlSummaries = @'
    CREATE TABLE IF NOT EXISTS staging_provider_weekly_summary (
        provider_id TEXT,
        week TEXT,
        year TEXT,
        total_tasks INT
    );
    DELETE FROM staging_provider_weekly_summary;
    INSERT INTO staging_provider_weekly_summary (provider_id, week, year, total_tasks)
    SELECT provider_code, strftime('%W', activity_date) AS week, strftime('%Y', activity_date) AS year, COUNT(*) AS total_tasks
    FROM staging_provider_tasks
    GROUP BY provider_code, strftime('%W', activity_date), strftime('%Y', activity_date);
    
    CREATE TABLE IF NOT EXISTS staging_provider_monthly_billing (
        provider_id TEXT,
        patient_id TEXT,
        billing_code TEXT,
        total_tasks INT,
        month TEXT,
        year TEXT
    );
    DELETE FROM staging_provider_monthly_billing;
    INSERT INTO staging_provider_monthly_billing (provider_id, patient_id, billing_code, total_tasks, month, year)
    SELECT provider_code, REPLACE(patient_name_raw, ',', '') AS patient_id, billing_code,
           COUNT(*) AS total_tasks, strftime('%m', activity_date) AS month, strftime('%Y', activity_date) AS year
    FROM staging_provider_tasks
    GROUP BY provider_code, REPLACE(patient_name_raw, ',', ''), billing_code, strftime('%m', activity_date), strftime('%Y', activity_date);
    
    CREATE TABLE IF NOT EXISTS staging_coordinator_monthly_summary (
        patient_id TEXT,
        coordinator_id TEXT,
        total_minutes INT,
        month TEXT,
        year TEXT
    );
    DELETE FROM staging_coordinator_monthly_summary;
    INSERT INTO staging_coordinator_monthly_summary (patient_id, coordinator_id, total_minutes, month, year)
    SELECT REPLACE(patient_name_raw, ',', '') AS patient_id, staff_code AS coordinator_id,
           SUM(COALESCE(CAST(minutes_raw AS INT),0)) AS total_minutes,
           strftime('%m', activity_date) AS month, strftime('%Y', activity_date) AS year
    FROM staging_coordinator_tasks
    GROUP BY REPLACE(patient_name_raw, ',', ''), staff_code, strftime('%m', activity_date), strftime('%Y', activity_date);
    
    CREATE TABLE IF NOT EXISTS staging_coordinator_minutes (
        coordinator_id TEXT,
        total_minutes INT,
        month TEXT,
        year TEXT
    );
    DELETE FROM staging_coordinator_minutes;
    INSERT INTO staging_coordinator_minutes (coordinator_id, total_minutes, month, year)
    SELECT staff_code AS coordinator_id, SUM(COALESCE(CAST(minutes_raw AS INT),0)) AS total_minutes,
           strftime('%m', activity_date) AS month, strftime('%Y', activity_date) AS year
    FROM staging_coordinator_tasks
    GROUP BY staff_code, strftime('%m', activity_date), strftime('%Y', activity_date);
'@
    $ok3 = Invoke-InlineSQL -Sql $sqlSummaries -Description "Build staging summaries (weekly/monthly)"
    if (-not $ok3 -and -not $Force) { exit 1 }

    Write-Host ""
    Write-Host "Post-transformation (staging) Status:"
    Write-Host "   staging_patient_visits:      $(Get-TableCount 'staging_patient_visits')"
    Write-Host "   staging_provider_weekly_summary: $(Get-TableCount 'staging_provider_weekly_summary')"
    Write-Host "   staging_provider_monthly_billing: $(Get-TableCount 'staging_provider_monthly_billing')"
    Write-Host "   staging_coordinator_monthly_summary: $(Get-TableCount 'staging_coordinator_monthly_summary')"
    Write-Host "   staging_coordinator_minutes: $(Get-TableCount 'staging_coordinator_minutes')"

} else {
    Write-Host "WARNING: Running legacy curated path. Ensure backups and intent before proceeding."

    Write-Host "Pre-transformation Status (curated):"
    Write-Host "   Patients:              $(Get-TableCount 'patients')"
    Write-Host "   Patient Assignments:   $(Get-TableCount 'patient_assignments')"
    Write-Host "   Patient Panel:         $(Get-TableCount 'patient_panel')"

    $success1 = Invoke-SQLScript -ScriptPath "..\src\sql\create_patient_visits.sql" -Description "Creating patient visits"
    if (-not $success1 -and -not $Force) { exit 1 }

    $success2 = Invoke-SQLScript -ScriptPath "..\src\sql\update_last_visit.sql" -Description "Updating last visit info"
    if (-not $success2 -and -not $Force) { exit 1 }

    $success3 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_summary_tables.sql" -Description "Updating summary tables"
    $success4 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_coordinator_monthly_summary.sql" -Description "Updating coordinator monthly summaries"
    $success5 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_provider_monthly_summary.sql" -Description "Updating provider monthly summaries"
    $success6 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_provider_weekly_summary.sql" -Description "Updating provider weekly summaries (no billing codes/status)"
    $success7 = Invoke-SQLScript -ScriptPath "..\src\sql\populate_provider_weekly_summary_with_billing.sql" -Description "Updating provider weekly summaries (with billing codes and status)"

    Write-Host ""
    Write-Host "Post-transformation Status (curated):"
    Write-Host "   patient_visits:        $(Get-TableCount 'patient_visits')"
    Write-Host "   dashboard_patient_assignment_summary: $(Get-TableCount 'dashboard_patient_assignment_summary')"
    Write-Host "   dashboard_patient_county_map:        $(Get-TableCount 'dashboard_patient_county_map')"
    Write-Host "   dashboard_patient_zip_map:           $(Get-TableCount 'dashboard_patient_zip_map')"
}

Write-Host ""
Write-Host "Step 4c complete. Workflow finished."

# Post-run: print staging summary counts and assert curated tables untouched when staging-only mode
if ($StagingOnly) {
  Write-Host "[4c] Validation: staging summary counts"
  $stagingTargets = @('staging_patient_visits','staging_provider_weekly_summary','staging_provider_monthly_billing','staging_coordinator_monthly_summary','staging_coordinator_minutes')
  foreach ($t in $stagingTargets) {
    $cnt = Get-TableCount -TableName $t
    Write-Host (" - {0}: {1}" -f $t, $cnt)
  }
  Write-Host "[4c] Validation: comparing curated baseline vs post-run counts (should be unchanged in staging-only mode)"
  $postCounts = @{}
  foreach ($key in $global:CuratedBaseline.Keys) { $postCounts[$key] = Get-TableCount -TableName $key }
  $differences = @()
  foreach ($key in $global:CuratedBaseline.Keys) {
    if ($global:CuratedBaseline[$key] -ne $postCounts[$key]) { $differences += $key }
  }
  if ($differences.Count -gt 0) {
    Write-Warning ("[4c] Validation FAILED: curated tables changed during staging-only run: {0}" -f ($differences -join ', '))
    Write-Warning "Counts (baseline -> post):"
    foreach ($k in $differences) { Write-Warning (" - {0}: {1} -> {2}" -f $k, $global:CuratedBaseline[$k], $postCounts[$k]) }
    throw "Staging-only invariant violated: curated tables were modified"
  } else {
    Write-Host "[4c] Validation PASSED: curated tables remained unchanged in staging-only mode"
  }
}
