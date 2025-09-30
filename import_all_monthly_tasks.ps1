$providerCsvFolder = "downloads/monthly_PSL"
$coordinatorCsvFolder = "downloads/monthly_CM"
$sqliteDb = "sandbox/production.db"

# Provider tasks import
foreach ($file in Get-ChildItem $providerCsvFolder -Filter "provider_tasks_*.csv") {
    $ym = $file.BaseName -replace "provider_tasks_", ""
    $stagingTable = "SOURCE_PSL_TASKS_$ym"
    $finalTable = "provider_tasks_$ym"

    $createTableSql = @"
DROP TABLE IF EXISTS $stagingTable;
CREATE TABLE $stagingTable (
    [1] INTEGER,
    Prov TEXT,
    Coding TEXT,
    [Patient Last, First DOB] TEXT,
    DOS TEXT,
    Service TEXT,
    Minutes TEXT,
    Hospice TEXT,
    Notes TEXT,
    [WC Size  (sqcm)] TEXT,
    [WC Diagnosis (HH-OK to free type)] TEXT,
    [Graft Info] TEXT,
    [Wound#] TEXT,
    [Session#] TEXT,
    [Multiple Grafts] TEXT,
    [Billed Date  Notes] TEXT,
    [Paid by Patient] TEXT
);
"@
    sqlite3 $sqliteDb "$createTableSql"
    sqlite3 $sqliteDb ".mode csv"
    sqlite3 $sqliteDb ".import '$($file.FullName)' $stagingTable"
    $insertSql = @"
DELETE FROM $finalTable;
INSERT INTO $finalTable (
    patient_id,
    provider_id,
    task_date,
    minutes_of_service,
    task_description,
    notes,
    billing_code,
    created_date
)
SELECT
    COALESCE(p.patient_id, psl.[Patient Last, First DOB]) AS patient_id,
    scm.user_id,
    psl.DOS,
    psl.Minutes,
    psl.Service,
    psl.Notes,
    psl.Coding,
    CURRENT_TIMESTAMP
FROM $stagingTable psl
LEFT JOIN patients p ON TRIM(UPPER(psl.[Patient Last, First DOB])) = TRIM(UPPER(p.last_first_dob))
LEFT JOIN staff_code_mapping scm ON psl.Prov = scm.staff_code
WHERE psl.[Patient Last, First DOB] IS NOT NULL
  AND TRIM(psl.[Patient Last, First DOB]) != '';
"@
    sqlite3 $sqliteDb "$insertSql"
}

# Coordinator tasks import
foreach ($file in Get-ChildItem $coordinatorCsvFolder -Filter "coordinator_tasks_*.csv") {
    $ym = $file.BaseName -replace "coordinator_tasks_", ""
    $stagingTable = "SOURCE_CM_TASKS_$ym"
    $finalTable = "coordinator_tasks_$ym"

    $createTableSql = @"
DROP TABLE IF EXISTS $stagingTable;
CREATE TABLE $stagingTable (
    Staff TEXT,
    [Pt Name] TEXT,
    Type TEXT,
    [Date Only] TEXT,
    [Start Time] TEXT,
    Notes TEXT,
    [Stop Time] TEXT,
    [Start Time B] TEXT,
    [Stop Time B] TEXT,
    [Mins B] TEXT,
    ZEN TEXT,
    [Total Mins] TEXT,
    Current TEXT,
    [Last, First DOB] TEXT,
    NotZEN TEXT,
    [Start Time A] TEXT,
    [Stop Time A] TEXT
);
"@
    sqlite3 $sqliteDb "$createTableSql"
    sqlite3 $sqliteDb ".mode csv"
    sqlite3 $sqliteDb ".import '$($file.FullName)' $stagingTable"
    $insertSql = @"
DELETE FROM $finalTable;
INSERT INTO $finalTable (
    patient_id,
    coordinator_id,
    task_date,
    duration_minutes,
    task_type,
    notes,
    raw_date,
    created_at
)
SELECT
    COALESCE(p.patient_id, cm.[Last, First DOB]) AS patient_id,
    scm.user_id,
    cm.[Date Only],
    cm.[Total Mins],
    cm.Type,
    cm.Notes,
    cm.[Date Only],
    CURRENT_TIMESTAMP
FROM $stagingTable cm
LEFT JOIN patients p ON TRIM(UPPER(cm.[Last, First DOB])) = TRIM(UPPER(p.last_first_dob))
LEFT JOIN staff_code_mapping scm ON cm.Staff = scm.staff_code
WHERE cm.[Last, First DOB] IS NOT NULL
  AND TRIM(cm.[Last, First DOB]) != '';
"@
    sqlite3 $sqliteDb "$insertSql"
}
