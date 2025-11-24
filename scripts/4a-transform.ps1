# Step 4a: Patient Import Phase (Staging-Safe)
#
# Workflow Overview (2025-09):
#   1. Build staging_patients from SOURCE_PATIENT_DATA (no writes to patients)
#   2. Build staging_patient_assignments from staging_patients + users (no writes to patient_assignments)
#   3. Build staging_patient_panel from staging_patients + staging_patient_assignments (no writes to patient_panel)
#
# This script is part 1 of 3 for the full transformation workflow:
#   - 4a-transform.ps1 (this script): Patient import (staging-only by default)
#   - 4b-transform.ps1: Task transformation (staging-safe)
#   - 4c-transform.ps1: Visits, summary, and reporting
#
# See the other scripts for the remaining steps.

param(
    [string]$DatabasePath = ".\production.db",
    [string]$StagingDatabasePath = ".\scripts\sheets_data.db",
    [switch]$Force = $false
)

Write-Host "==============================="
Write-Host "Step 4a: Patient Import Phase (Staging-Safe)"
Write-Host "==============================="
Write-Host "Database: $DatabasePath"
Write-Host "Staging: $StagingDatabasePath"
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# Staging database is now attached within the Invoke-InlineSQL function.

function Invoke-InlineSQL {
    param(
        [string]$Sql,
        [string]$Description
    )
    Write-Host "Running: $Description"
    $tmp = [System.IO.Path]::GetTempFileName()
    try {
        $attachSql = "ATTACH DATABASE '$StagingDatabasePath' AS staging;`n"
        Set-Content -Path $tmp -Value ($attachSql + $Sql) -Encoding UTF8
        $result = sqlite3 $DatabasePath ".read $tmp" 2>&1
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
    finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

# Facilities table presence check for sandbox-safe run
$hasFacilities = $false
try {
    $__res = sqlite3 $DatabasePath "SELECT 1 FROM sqlite_master WHERE type='table' AND name='facilities' LIMIT 1" 2>&1
    if ($LASTEXITCODE -eq 0 -and $__res -match '1') { $hasFacilities = $true }
}
catch { $hasFacilities = $false }

# Define facility lookup column snippets based on facilities table presence
if ($hasFacilities -eq $true) {
    $facilityCurrentIdColumnSPD = @"
CASE WHEN spd."Fac" IS NOT NULL AND TRIM(spd."Fac") != '' AND TRIM(spd."Fac") != 'zFac' THEN (
    SELECT f.facility_id FROM facilities f WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(spd."Fac")) LIMIT 1
) ELSE NULL END as current_facility_id,
"@
    $facilityCurrentIdPanel = @"
COALESCE(p.current_facility_id, (
    SELECT f.facility_id FROM facilities f WHERE LOWER(TRIM(f.facility_name)) = LOWER(TRIM(p.facility)) LIMIT 1
)) AS current_facility_id,
"@
}
else {
    $facilityCurrentIdColumnSPD = 'NULL as current_facility_id,'
    $facilityCurrentIdPanel = 'p.current_facility_id AS current_facility_id,'
}

# 1) Build staging_patients with the same transformation logic as populate_patients.sql, without touching patients
$stagingPatientsSql = @"
DROP TABLE IF EXISTS staging.staging_patients;
CREATE TABLE staging.staging_patients AS
SELECT DISTINCT 
    UPPER(TRIM(REPLACE(REPLACE(REPLACE(TRIM(spd."Last") || ' ' || TRIM(spd."First") || ' ' || TRIM(spd."DOB"), ', ', ' '), ',', ' '), '  ', ' '))) as patient_id,
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
    $facilityCurrentIdColumnSPD
    0 as hypertension,
    0 as mental_health_concerns,
    0 as dementia,
    NULL as last_annual_wellness_visit,
    UPPER(TRIM(REPLACE(REPLACE(REPLACE(TRIM(spd."LAST FIRST DOB"), ', ', ' '), ',', ' '), '  ', ' '))) as last_first_dob,
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
    NULL as appointment_contact_name,
    NULL as appointment_contact_phone,
    NULL as appointment_contact_email,
    NULL as medical_contact_name,
    NULL as medical_contact_phone,
    NULL as medical_contact_email,
    NULL as primary_care_provider,
    NULL as pcp_last_seen,
    NULL as active_specialist,
    NULL as specialist_last_seen,
    NULL as chronic_conditions_onboarding,
    FALSE as mh_schizophrenia,
    FALSE as mh_depression,
    FALSE as mh_anxiety,
    FALSE as mh_stress,
    FALSE as mh_adhd,
    FALSE as mh_bipolar,
    FALSE as mh_suicidal,
    NULLIF(spd."Initial TV Date", '') as tv_date,
    CASE WHEN spd."Initial TV Date" IS NOT NULL AND spd."Initial TV Date" != '' THEN TRUE ELSE FALSE END as tv_scheduled,
    CASE WHEN spd."CM Notified" IS NOT NULL AND spd."CM Notified" != '' THEN TRUE ELSE FALSE END as patient_notified,
    NULLIF(spd."Initial TV Prov", '') as initial_tv_provider
FROM staging.SOURCE_PATIENT_DATA spd
WHERE spd."LAST FIRST DOB" IS NOT NULL AND spd."LAST FIRST DOB" != '' AND spd."LAST FIRST DOB" != 'LAST FIRST DOB'
  AND TRIM(spd."First") IS NOT NULL AND TRIM(spd."Last") IS NOT NULL AND spd."DOB" IS NOT NULL;
"@

$ok1 = Invoke-InlineSQL -Sql $stagingPatientsSql -Description "Building staging_patients from SOURCE_PATIENT_DATA"
if (-not $ok1 -and -not $Force) { exit 1 }

# Detect users table presence; if absent, create an empty staging_patient_assignments
$hasUsers = $false
try {
    $__users = sqlite3 $DatabasePath "SELECT 1 FROM sqlite_master WHERE type='table' AND name='users' LIMIT 1" 2>&1
    if ($LASTEXITCODE -eq 0 -and $__users -match '1') { $hasUsers = $true }
}
catch { $hasUsers = $false }

# 2) Build staging_patient_assignments from staging_patients + users (or stub if users missing)
if ($hasUsers -eq $true) {
    $stagingAssignmentsSql = @"
DROP TABLE IF EXISTS staging.staging_patient_assignments;
CREATE TABLE staging.staging_patient_assignments AS
SELECT p.patient_id,
    (
        SELECT u.user_id
        FROM staging.SOURCE_PATIENT_DATA spd2
        JOIN users u ON TRIM(u.full_name) = TRIM(spd2."Assigned  Reg Prov")
        WHERE spd2."Assigned  Reg Prov" IS NOT NULL AND spd2."Assigned  Reg Prov" != ''
          AND TRIM(spd2."Last") || ' ' || TRIM(spd2."First") || ' ' || TRIM(spd2."DOB") = p.patient_id
        LIMIT 1
    ) AS provider_id,
    (
        SELECT u.user_id
        FROM staging.SOURCE_PATIENT_DATA spd2
        JOIN users u ON LOWER(TRIM(u.first_name)) = LOWER(TRIM(CASE WHEN INSTR(spd2."Assigned CM", ',') > 0 THEN SUBSTR(spd2."Assigned CM", INSTR(spd2."Assigned CM", ',') + 1) ELSE spd2."Assigned CM" END))
        WHERE spd2."Assigned CM" IS NOT NULL AND spd2."Assigned CM" != ''
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
FROM staging.staging_patients p;
"@
}
else {
    $stagingAssignmentsSql = @"
DROP TABLE IF EXISTS staging.staging_patient_assignments;
CREATE TABLE staging.staging_patient_assignments AS
SELECT p.patient_id,
    NULL AS provider_id,
    NULL AS coordinator_id,
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
}

$ok2 = Invoke-InlineSQL -Sql $stagingAssignmentsSql -Description "Building staging_patient_assignments from staging_patients (+ users if present)"
if (-not $ok2 -and -not $Force) { exit 1 }

# 3) Build staging_patient_panel from staging tables
if ($hasUsers -eq $true) {
    $stagingPanelSql = @"
DROP TABLE IF EXISTS staging.staging_patient_panel;
CREATE TABLE staging.staging_patient_panel AS
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
    $facilityCurrentIdPanel
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
FROM staging.staging_patients p
LEFT JOIN (
    SELECT patient_id,
        MAX(provider_id) AS provider_id,
        MAX(coordinator_id) AS coordinator_id
    FROM staging.staging_patient_assignments
    WHERE provider_id > 0 OR coordinator_id > 0
    GROUP BY patient_id
) pa ON pa.patient_id = p.patient_id
LEFT JOIN users up ON pa.provider_id = up.user_id
LEFT JOIN users uc ON pa.coordinator_id = uc.user_id;
"@
}
else {
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
    $facilityCurrentIdPanel
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
    NULL as provider_name,
    pa.coordinator_id,
    NULL as coordinator_name,
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
    SELECT patient_id,
        MAX(provider_id) AS provider_id,
        MAX(coordinator_id) AS coordinator_id
    FROM staging_patient_assignments
    GROUP BY patient_id
) pa ON pa.patient_id = p.patient_id;
"@
}

$ok3 = Invoke-InlineSQL -Sql $stagingPanelSql -Description "Building staging_patient_panel from staging tables"
if (-not $ok3 -and -not $Force) { exit 1 }

Write-Host "Step 4a complete (staging-safe). Continue with 4b-transform.ps1."
