# Step 4: Post-Import Data Transformation - Complete Patient Processing (Staging-Aware)
# Enhanced version that handles all patient-related foreign key relationships

param(
    [string]$DatabasePath = ".\production.db",
    [string]$StagingDatabasePath = ".\sheets_data.db",
    [switch]$StagingOnly = $true,
    [switch]$Force = $false,
    [switch]$SkipBackup = $false
)

Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Step 4: Complete Post-Import Data Transformation" -ForegroundColor Cyan  
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "Database: $DatabasePath" -ForegroundColor Yellow
Write-Host "Staging: $StagingDatabasePath" -ForegroundColor Yellow
Write-Host "Mode: " ($StagingOnly ? "STAGING-ONLY" : "CURATED TABLES (DANGEROUS)") -ForegroundColor Yellow
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
Write-Host ""

# Check if database exists
if (-not (Test-Path $DatabasePath)) {
    Write-Host "❌ ERROR: Database not found at $DatabasePath" -ForegroundColor Red
    exit 1
}

# Create backup unless skipped
if (-not $SkipBackup) {
    $backupPath = "$DatabasePath.backup.step4.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "📁 Creating backup: $backupPath" -ForegroundColor Yellow
    try {
        Copy-Item $DatabasePath $backupPath -Force
        Write-Host "✅ Backup created successfully" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ ERROR creating backup: $($_.Exception.Message)" -ForegroundColor Red
        if (-not $Force) { exit 1 }
    }
}

function Invoke-SQLScript {
    param(
        [string]$ScriptPath,
        [string]$Description,
        [switch]$ContinueOnError = $false
    )
    Write-Host "🔄 $Description..." -ForegroundColor Yellow
    if (-not (Test-Path $ScriptPath)) {
        Write-Host "❌ ERROR: Script not found: $ScriptPath" -ForegroundColor Red
        if (-not $ContinueOnError) { return $false }
    }
    try {
        $startTime = Get-Date
        $result = Get-Content $ScriptPath | sqlite3 $DatabasePath 2>&1
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $Description completed successfully ($([math]::Round($duration, 2))s)" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ ERROR in $Description (Exit code: $LASTEXITCODE)" -ForegroundColor Red
            if ($result) { Write-Host "   Error details: $result" -ForegroundColor Red }
            return $false
        }
    }
    catch {
        Write-Host "❌ EXCEPTION in $Description : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Invoke-InlineSQL {
    param(
        [string]$Sql,
        [string]$Description
    )
    Write-Host "🔄 $Description..." -ForegroundColor Yellow
    try {
        $result = sqlite3 $DatabasePath $Sql 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $Description completed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ ERROR in $Description" -ForegroundColor Red
            if ($result) { Write-Host "   Error details: $result" -ForegroundColor Red }
            return $false
        }
    } catch {
        Write-Host "❌ EXCEPTION in $Description : $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Attach staging DB and TEMP SOURCE_* views
try {
    sqlite3 $DatabasePath "ATTACH '$StagingDatabasePath' AS staging;" 2>$null
    sqlite3 $DatabasePath "CREATE TEMP VIEW IF NOT EXISTS SOURCE_PATIENT_DATA AS SELECT * FROM staging.SOURCE_PATIENT_DATA;" 2>$null
    sqlite3 $DatabasePath "CREATE TEMP VIEW IF NOT EXISTS SOURCE_COORDINATOR_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_COORDINATOR_TASKS_HISTORY;" 2>$null
    sqlite3 $DatabasePath "CREATE TEMP VIEW IF NOT EXISTS SOURCE_PROVIDER_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_PROVIDER_TASKS_HISTORY;" 2>$null
    Write-Host "🔗 Attached staging DB and created TEMP SOURCE_* views" -ForegroundColor Green
}
catch {
    Write-Host "❌ ERROR: Could not attach staging DB or create temp views: $($_.Exception.Message)" -ForegroundColor Red
    if (-not $Force) { exit 1 }
}

Write-Host "📊 Pre-transformation Status:" -ForegroundColor Cyan
$prePatients = (sqlite3 $DatabasePath "SELECT COUNT(*) FROM patients;" 2>$null)
$preAssignments = (sqlite3 $DatabasePath "SELECT COUNT(*) FROM patient_assignments;" 2>$null)
$preProviderTasks = (sqlite3 $DatabasePath "SELECT COUNT(*) FROM provider_tasks;" 2>$null)
$preCoordinatorTasks = (sqlite3 $DatabasePath "SELECT COUNT(*) FROM coordinator_tasks;" 2>$null)
Write-Host "   • Patients: $prePatients" -ForegroundColor White
Write-Host "   • Patient Assignments: $preAssignments" -ForegroundColor White
Write-Host "   • Provider Tasks: $preProviderTasks" -ForegroundColor White
Write-Host "   • Coordinator Tasks: $preCoordinatorTasks" -ForegroundColor White
Write-Host ""

if ($StagingOnly) {
    Write-Host "🛡️ STAGING-ONLY MODE: Curated tables will NOT be modified." -ForegroundColor Yellow

    # Build staging task tables
    $okCt = Invoke-SQLScript -ScriptPath ".\src\sql\staging_coordinator_tasks.sql" -Description "Building staging_coordinator_tasks"
    if (-not $okCt -and -not $Force) { exit 1 }

    $okPt = Invoke-SQLScript -ScriptPath ".\src\sql\staging_provider_tasks.sql" -Description "Building staging_provider_tasks"
    if (-not $okPt -and -not $Force) { exit 1 }

    # Build staging patients (same logic as 4a)
    $stagingPatientsSql = @"
DROP TABLE IF EXISTS staging_patients;
CREATE TABLE staging_patients AS
SELECT DISTINCT 
    TRIM(REPLACE(REPLACE(REPLACE(TRIM(spd."Last") || ' ' || TRIM(spd."First") || ' ' || TRIM(spd."DOB"), ', ', ' '), ',', ' '), '  ', ' ')) as patient_id,
    NULL as region_id,
    TRIM(spd."First") as first_name,
    TRIM(spd."Last") as last_name,
    spd."DOB" as date_of_birth,
    NULL as gender,
    CASE WHEN spd."Phone" IS NOT NULL AND spd."Phone" != '' AND spd."Phone" != 'zPhone' THEN TRIM(spd."Phone") ELSE NULL END as phone_primary,
    NULL as phone_secondary,
    NULL as email,
    CASE WHEN spd."Street" IS NOT NULL AND spd."Street" != '' AND spd."Street" != 'zStreet' THEN TRIM(spd."Street") ELSE NULL END as address_street,
    CASE WHEN spd."City" IS NOT NULL AND spd."City" != '' AND spd."City" != 'zCity' THEN TRIM(spd."City") ELSE NULL END as address_city,
    CASE WHEN spd."State" IS NOT NULL AND spd."State" != '' AND spd."State" != 'zState' THEN TRIM(spd."State") ELSE NULL END as address_state,
    CASE WHEN spd."Zip" IS NOT NULL AND spd."Zip" != '' AND spd."Zip" != 'zZip' THEN TRIM(spd."Zip") ELSE NULL END as address_zip,
    CASE WHEN spd."Contact Name" IS NOT NULL AND spd."Contact Name" != '' AND spd."Contact Name" != 'zContact' THEN TRIM(spd."Contact Name") ELSE NULL END as emergency_contact_name,
    NULL as emergency_contact_phone,
    NULL as emergency_contact_relationship,
    CASE WHEN spd."Ins1" IS NOT NULL AND spd."Ins1" != '' AND spd."Ins1" != 'zIns' THEN TRIM(spd."Ins1") ELSE NULL END as insurance_primary,
    CASE WHEN spd."Policy" IS NOT NULL AND spd."Policy" != '' AND spd."Policy" != 'zPolicy' THEN TRIM(spd."Policy") ELSE NULL END as insurance_policy_number,
    NULL as insurance_secondary,
    NULL as medical_record_number,
    NULL as enrollment_date,
    NULL as discharge_date,
    TRIM(COALESCE(NULLIF(spd."List6 Notes", ''), NULLIF(spd."Prescreen Call Notes", ''), NULLIF(spd."Initial TV Notes", ''), NULLIF(spd."TV Note", ''), NULLIF(spd."eMed Records Routing Notes", ''), NULLIF(spd."Schedule HV 2w Notes", ''), '')) as notes,
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date,
    NULL as created_by,
    NULL as updated_by,
    CASE WHEN spd."Fac" IS NOT NULL AND TRIM(spd."Fac") != '' AND TRIM(spd."Fac") != 'zFac' THEN (
        SELECT f.facility_id FROM facilities f WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(spd."Fac")) LIMIT 1
    ) ELSE NULL END as current_facility_id,
    0 as hypertension,
    0 as mental_health_concerns,
    0 as dementia,
    NULL as last_annual_wellness_visit,
    TRIM(REPLACE(REPLACE(REPLACE(TRIM(spd."LAST FIRST DOB"), ', ', ' '), ',', ' '), '  ', ' ')) as last_first_dob,
    CASE WHEN spd."Pt Status" IS NOT NULL AND spd."Pt Status" != '' THEN TRIM(spd."Pt Status") ELSE 'Active' END as status,
    FALSE as medical_records_requested,
    FALSE as referral_documents_received,
    FALSE as insurance_cards_received,
    FALSE as emed_signature_received,
    NULL as last_visit_date,
    NULL as facility,
    NULL as assigned_coordinator_id,
    NULL as er_count_1yr,
    NULL as hospitalization_count_1yr,
    NULL as clinical_biometric,
    NULL as chronic_conditions_provider,
    NULL as cancer_history,
    NULL as subjective_risk_level,
    FALSE as provider_mh_schizophrenia,
    FALSE as provider_mh_depression,
    FALSE as provider_mh_anxiety,
    FALSE as provider_mh_stress,
    FALSE as provider_mh_adhd,
    FALSE as provider_mh_bipolar,
    FALSE as provider_mh_suicidal,
    NULL as active_specialists,
    NULL as code_status,
    NULL as cognitive_function,
    NULL as functional_status,
    NULL as goals_of_care,
    NULL as active_concerns,
    NULLIF(spd."Initial TV Date", '') as initial_tv_completed_date,
    NULLIF(spd."Initial TV Notes", '') as initial_tv_notes,
    NULL as service_type,
    NULLIF(spd."Initial TV Date", '') as tv_date,
    CASE WHEN spd."Initial TV Date" IS NOT NULL AND spd."Initial TV Date" != '' THEN TRUE ELSE FALSE END as tv_scheduled,
    CASE WHEN spd."CM Notified" IS NOT NULL AND spd."CM Notified" != '' THEN TRUE ELSE FALSE END as patient_notified,
    NULLIF(spd."Initial TV Prov", '') as initial_tv_provider
FROM SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL AND spd."LAST FIRST DOB" != '' AND spd."LAST FIRST DOB"
Invoke-InlineSQL -Sql $stagingPatientsSql -Description "Building staging_patients" | Out-Null

# Build staging_patient_assignments based on SOURCE_PATIENT_DATA + users
$stagingAssignmentsSql = @"
DROP TABLE IF EXISTS staging_patient_assignments;
CREATE TABLE staging_patient_assignments AS
SELECT p.patient_id,
    (
        SELECT u.user_id
        FROM SOURCE_PATIENT_DATA spd2
        JOIN users u ON TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(spd2."Assigned  Reg Prov", 'MD', ''),'NP',''),'PA',''),'ZZ',''),' ,',','),', ',','),'  ',' '))
            = TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(u.full_name, 'MD', ''),'NP',''),'PA',''),'ZZ',''),' ,',','),', ',','),'  ',' '))
        WHERE spd2."Assigned  Reg Prov" IS NOT NULL
          AND spd2."Assigned  Reg Prov" != ''
          AND TRIM(spd2."Last") || ' ' || TRIM(spd2."First") || ' ' || TRIM(spd2."DOB") = p.patient_id
        LIMIT 1
    ) AS provider_id,
    (
        SELECT u.user_id
        FROM SOURCE_PATIENT_DATA spd2
        JOIN users u ON LOWER(TRIM(u.first_name)) = LOWER(TRIM(CASE WHEN INSTR(spd2."Assigned CM", ',') > 0 THEN SUBSTR(spd2."Assigned CM", INSTR(spd2."Assigned CM", ',') + 1) ELSE spd2."Assigned CM" END))
        WHERE spd2."Assigned CM" IS NOT NULL
          AND spd2."Assigned CM" != ''
          AND TRIM(spd2."Last") || ' ' || TRIM(spd2."First") || ' ' || TRIM(spd2."DOB") = p.patient_id
        LIMIT 1
    ) AS coordinator_id,
    CURRENT_TIMESTAMP as assignment_date,
    'both' as assignment_type,
    CASE WHEN p.status LIKE '%Active%' THEN 'active' ELSE 'inactive' END as status,
    'standard' as priority_level,
    'Imported from SOURCE_PATIENT_DATA' as notes,
    CURRENT_TIMESTAMP as created_date,
    CURRENT_TIMESTAMP as updated_date,
    NULL as initial_tv_provider_id
FROM staging_patients p;
"@
Invoke-InlineSQL -Sql $stagingAssignmentsSql -Description "Building staging_patient_assignments" | Out-Null

# Build staging_patient_panel from staging_patients and staging_patient_assignments
$stagingPanelSql = @"
DROP TABLE IF EXISTS staging_patient_panel;
CREATE TABLE staging_patient_panel AS
SELECT DISTINCT p.patient_id,
    p.first_name,
    p.last_name,
    p.date_of_birth,
    p.gender,
    p.phone_primary,
    p.phone_secondary,
    p.email,
    p.address_street,
    p.address_city,
    p.address_state,
    p.address_zip,
    p.emergency_contact_name,
    p.emergency_contact_phone,
    p.emergency_contact_relationship,
    p.insurance_primary,
    p.insurance_policy_number,
    p.insurance_secondary,
    p.medical_record_number,
    p.enrollment_date,
    p.discharge_date,
    TRIM(COALESCE(p.notes, '') || CASE WHEN p.initial_tv_notes IS NOT NULL AND p.initial_tv_notes != '' THEN '\nInitial TV: ' || p.initial_tv_notes ELSE '' END) as notes,
    p.created_date,
    p.updated_date,
    p.created_by,
    p.updated_by,
    p.current_facility_id,
    p.hypertension,
    p.mental_health_concerns,
    p.dementia,
    p.last_annual_wellness_visit,
    p.last_first_dob,
    p.status,
    p.medical_records_requested,
    p.referral_documents_received,
    p.insurance_cards_received,
    p.emed_signature_received,
    p.last_visit_date,
    p.facility,
    p.assigned_coordinator_id,
    p.er_count_1yr,
    p.hospitalization_count_1yr,
    p.clinical_biometric,
    p.chronic_conditions_provider,
    p.cancer_history,
    p.subjective_risk_level,
    p.provider_mh_schizophrenia,
    p.provider_mh_depression,
    p.provider_mh_anxiety,
    p.provider_mh_stress,
    p.provider_mh_adhd,
    p.provider_mh_bipolar,
    p.provider_mh_suicidal,
    p.active_specialists,
    p.code_status,
    p.cognitive_function,
    p.functional_status,
    p.goals_of_care,
    p.active_concerns,
    p.initial_tv_completed_date,
    p.initial_tv_notes,
    p.initial_tv_provider,
    pa.provider_id,
    up.full_name as provider_name,
    pa.coordinator_id,
    uc.full_name as coordinator_name,
    NULL as stage1_complete,
    NULL as stage2_complete,
    NULL as initial_tv_completed,
    'staging_patients' as source_table,
    NULL as source_column,
    NULL as last_visit_provider_id,
    NULL as last_visit_provider_name,
    p.service_type as last_visit_service_type,
    p.region_id
FROM staging_patients p
LEFT JOIN (
    SELECT patient_id, MAX(provider_id) AS provider_id, MAX(coordinator_id) AS coordinator_id
    FROM staging_patient_assignments
    WHERE provider_id > 0 OR coordinator_id > 0
    GROUP BY patient_id
) pa ON pa.patient_id = p.patient_id
LEFT JOIN users up ON pa.provider_id = up.user_id
LEFT JOIN users uc ON pa.coordinator_id = uc.user_id;
"@
Invoke-InlineSQL -Sql $stagingPanelSql -Description "Building staging_patient_panel" | Out-Null

# Summaries for staging
$stagingSummarySql = @"
SELECT 'staging_patients' as table_name, COUNT(*) as row_count FROM staging_patients UNION ALL
SELECT 'staging_patient_assignments', COUNT(*) FROM staging_patient_assignments UNION ALL
SELECT 'staging_patient_panel', COUNT(*) FROM staging_patient_panel;
"@
Write-Host (sqlite3 $DatabasePath $stagingSummarySql) -ForegroundColor White

Write-Host "🏁 Step 4 complete (STAGING-ONLY). No curated tables were modified." -ForegroundColor Green
return

} else {
    Write-Host "⚠️ CURATED MODE: Scripts will modify curated tables. Ensure you have backups." -ForegroundColor Yellow

    # Original flow (dangerous). Guard missing scripts with ContinueOnError.
    $success1 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_coordinator_tasks.sql" -Description "Transforming coordinator tasks"
    $success2 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_provider_tasks.sql" -Description "Transforming provider tasks" -ContinueOnError
    $success3 = Invoke-SQLScript -ScriptPath ".\src\sql\complete_patient_transformation.sql" -Description "Complete patient data transformation with all foreign keys" -ContinueOnError
    $success4 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_summary_tables.sql" -Description "Updating summary tables" -ContinueOnError
    $success5 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_coordinator_monthly_summary.sql" -Description "Updating coordinator monthly summaries" -ContinueOnError
    $success6 = Invoke-SQLScript -ScriptPath ".\src\sql\populate_provider_monthly_summary.sql" -Description "Updating provider monthly summaries" -ContinueOnError

    Write-Host "🏁 Step 4 complete (CURATED)" -ForegroundColor Green
}