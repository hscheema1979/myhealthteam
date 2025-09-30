-- Drop existing temporary tables if they exist
DROP TABLE IF EXISTS temp_source_key;
DROP TABLE IF EXISTS temp_provider_id;
DROP TABLE IF EXISTS temp_provider_name;
DROP TABLE IF EXISTS temp_patient_id;
DROP TABLE IF EXISTS temp_user_id;
DROP TABLE IF EXISTS temp_billing_code;
DROP TABLE IF EXISTS temp_task_data;
-- Create main key table with source identifiers
CREATE TEMPORARY TABLE temp_source_key AS
SELECT "1" as row_id,
    "Prov" as prov_code
FROM "SOURCE_PROVIDER_TASKS_HISTORY"
WHERE "Prov" IS NOT NULL
    AND "Prov" != ''
    AND "Patient Last, First DOB" IS NOT NULL
    AND "Patient Last, First DOB" != '';
-- Create index on key table
CREATE INDEX IF NOT EXISTS idx_source_key ON temp_source_key(row_id, prov_code);
-- Create provider_id temp table
CREATE TEMPORARY TABLE temp_provider_id AS
SELECT sk.row_id,
    sk.prov_code,
    COALESCE(p.provider_id, sk.prov_code) as provider_id
FROM temp_source_key sk
    LEFT JOIN staff_code_mapping scm ON sk.prov_code = scm.staff_code
    LEFT JOIN providers p ON scm.user_id = p.user_id;
-- Create provider_name temp table
CREATE TEMPORARY TABLE temp_provider_name AS
SELECT sk.row_id,
    sk.prov_code,
    COALESCE(
        u2.first_name || ' ' || u2.last_name,
        sk.prov_code
    ) as provider_name
FROM temp_source_key sk
    LEFT JOIN staff_code_mapping scm ON sk.prov_code = scm.staff_code
    LEFT JOIN providers p ON scm.user_id = p.user_id
    LEFT JOIN users u ON scm.user_id = u.user_id
    LEFT JOIN users u2 ON p.user_id = u2.user_id;
-- Create patient_id temp table
CREATE TEMPORARY TABLE temp_patient_id AS
SELECT sk.row_id,
    sk.prov_code,
    sp."Patient Last, First DOB" as patient_name,
    COALESCE(pat.patient_id, sp."Patient Last, First DOB") as patient_id
FROM temp_source_key sk
    JOIN "SOURCE_PROVIDER_TASKS_HISTORY" sp ON sk.row_id = sp."1"
    AND sk.prov_code = sp."Prov"
    LEFT JOIN patients pat ON TRIM(UPPER(sp."Patient Last, First DOB")) = TRIM(UPPER(pat.last_first_dob));
-- Create user_id temp table
CREATE TEMPORARY TABLE temp_user_id AS
SELECT sk.row_id,
    sk.prov_code,
    COALESCE(scm.user_id, sk.prov_code) as user_id
FROM temp_source_key sk
    LEFT JOIN staff_code_mapping scm ON sk.prov_code = scm.staff_code;
-- Create billing_code temp table with direct join on both coding and service
CREATE TEMPORARY TABLE temp_billing_code AS
SELECT sk.row_id,
    sk.prov_code,
    sp.Coding as coding,
    COALESCE(sp.Coding, 'Unknown') as billing_code,
    COALESCE(bc.description, 'Unknown') as billing_code_description,
    bc.code_id as billing_code_id,
    COALESCE(sp.Service, 'Unknown') as service
FROM temp_source_key sk
    JOIN "SOURCE_PROVIDER_TASKS_HISTORY" sp ON sk.row_id = sp."1"
    AND sk.prov_code = sp."Prov"
    LEFT JOIN task_billing_codes bc ON sp.Coding = bc.billing_code
    AND sp.Service = bc.task_description;
-- Create main task data temp table including service from billing code mapping
CREATE TEMPORARY TABLE temp_task_data AS
SELECT sk.row_id,
    sk.prov_code,
    sp.DOS as task_date,
    CAST(
        SUBSTR(sp.DOS, 1, INSTR(sp.DOS, '/') - 1) AS INTEGER
    ) as month,
    CAST('20' || SUBSTR(sp.DOS, -2) AS INTEGER) as year,
    CAST(sp.Minutes AS INTEGER) as minutes_of_service,
    'completed' as status,
    COALESCE(
        sp."EHR Chief Complaint" || ' ' || sp."EHR Assessment Dx",
        sp."EHR Chief Complaint",
        sp."EHR Assessment Dx"
    ) as notes,
    COALESCE(bc.service, 'Unknown') as service
FROM temp_source_key sk
    JOIN "SOURCE_PROVIDER_TASKS_HISTORY" sp ON sk.row_id = sp."1"
    AND sk.prov_code = sp."Prov"
    LEFT JOIN temp_billing_code bc ON sk.row_id = bc.row_id
    AND sk.prov_code = bc.prov_code;
-- Clear existing data from provider_tasks table
DELETE FROM provider_tasks;
-- Insert data into provider_tasks table from the temporary tables
INSERT INTO provider_tasks (
        provider_task_id,
        provider_id,
        provider_name,
        patient_name,
        user_id,
        patient_id,
        status,
        notes,
        minutes_of_service,
        billing_code_id,
        task_date,
        month,
        year,
        billing_code,
        billing_code_description,
        task_description
    )
SELECT ROW_NUMBER() OVER (
        ORDER BY td.row_id
    ) as provider_task_id,
    pi.provider_id,
    pn.provider_name,
    ptd.patient_name,
    ui.user_id,
    ptd.patient_id,
    td.status,
    td.notes,
    td.minutes_of_service,
    bc.billing_code_id,
    td.task_date,
    td.month,
    td.year,
    bc.billing_code,
    bc.billing_code_description,
    COALESCE(bc.service, 'Unknown') as task_description
FROM temp_task_data td
    JOIN temp_provider_id pi ON td.row_id = pi.row_id
    AND td.prov_code = pi.prov_code
    JOIN temp_provider_name pn ON td.row_id = pn.row_id
    AND td.prov_code = pn.prov_code
    JOIN temp_patient_id ptd ON td.row_id = ptd.row_id
    AND td.prov_code = ptd.prov_code
    JOIN temp_user_id ui ON td.row_id = ui.row_id
    AND td.prov_code = ui.prov_code
    JOIN temp_billing_code bc ON td.row_id = bc.row_id
    AND td.prov_code = bc.prov_code;
-- Verify the results
SELECT 'provider_tasks' as table_name,
    COUNT(*) as row_count
FROM provider_tasks;