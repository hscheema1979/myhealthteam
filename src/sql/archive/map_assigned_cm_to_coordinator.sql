-- Map SOURCE_PATIENT_DATA."Assigned CM" -> users.user_id -> patients.assigned_coordinator_id
PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
-- 1) How many exact full-name matches would we get?
SELECT 'exact_name_matches' AS metric,
    COUNT(*) AS value
FROM SOURCE_PATIENT_DATA spd
    JOIN users u ON LOWER(TRIM(spd."Assigned CM")) = LOWER(TRIM(u.full_name))
    JOIN patients p ON p.last_first_dob = spd."LAST FIRST DOB";
-- 2) Snapshot current assigned_coordinator_id for safety
DROP TABLE IF EXISTS patients_assigned_coordinator_snapshot;
CREATE TABLE patients_assigned_coordinator_snapshot AS
SELECT patient_id,
    assigned_coordinator_id
FROM patients;
-- 3) Counts before update
SELECT 'before_null_assigned_coordinator_count' AS metric,
    COUNT(*) AS value
FROM patients
WHERE assigned_coordinator_id IS NULL
    OR assigned_coordinator_id = '';
-- 4) Update patients.assigned_coordinator_id when source Assigned CM exactly matches users.full_name
UPDATE patients
SET assigned_coordinator_id = (
        SELECT u.user_id
        FROM SOURCE_PATIENT_DATA spd
            JOIN users u ON LOWER(TRIM(spd."Assigned CM")) = LOWER(TRIM(u.full_name))
        WHERE spd."LAST FIRST DOB" = patients.last_first_dob
        LIMIT 1
    )
WHERE (
        assigned_coordinator_id IS NULL
        OR assigned_coordinator_id = ''
    )
    AND EXISTS (
        SELECT 1
        FROM SOURCE_PATIENT_DATA spd2
            JOIN users u2 ON LOWER(TRIM(spd2."Assigned CM")) = LOWER(TRIM(u2.full_name))
        WHERE spd2."LAST FIRST DOB" = patients.last_first_dob
    );
-- 4b) Fallback: match SOURCE Assigned CM to patients' Last, First concatenation and map via users.full_name
SELECT 'fallback_potential_matches' AS metric,
    COUNT(*) AS value
FROM SOURCE_PATIENT_DATA spd
    JOIN patients p ON spd."LAST FIRST DOB" = p.last_first_dob
    JOIN users u ON LOWER(TRIM(spd."Assigned CM")) = LOWER(TRIM(p.last_name || ', ' || p.first_name))
    AND LOWER(TRIM(u.full_name)) = LOWER(TRIM(p.last_name || ', ' || p.first_name));
UPDATE patients
SET assigned_coordinator_id = (
        SELECT u.user_id
        FROM users u
        WHERE LOWER(TRIM(u.full_name)) = LOWER(
                TRIM(
                    patients.last_name || ', ' || patients.first_name
                )
            )
        LIMIT 1
    )
WHERE (
        assigned_coordinator_id IS NULL
        OR assigned_coordinator_id = ''
    )
    AND EXISTS (
        SELECT 1
        FROM SOURCE_PATIENT_DATA spd3
        WHERE spd3."LAST FIRST DOB" = patients.last_first_dob
            AND LOWER(TRIM(spd3."Assigned CM")) = LOWER(
                TRIM(
                    patients.last_name || ', ' || patients.first_name
                )
            )
    );
-- 5) Counts after update
SELECT 'after_null_assigned_coordinator_count' AS metric,
    COUNT(*) AS value
FROM patients
WHERE assigned_coordinator_id IS NULL
    OR assigned_coordinator_id = '';
-- 6) How many were assigned in this step (difference)
SELECT 'assigned_now' AS metric,
    (
        (
            SELECT COUNT(*)
            FROM patients_assigned_coordinator_snapshot
            WHERE assigned_coordinator_id IS NULL
                OR assigned_coordinator_id = ''
        ) - (
            SELECT COUNT(*)
            FROM patients
            WHERE assigned_coordinator_id IS NULL
                OR assigned_coordinator_id = ''
        )
    ) AS value;
-- 7) Show sample of mapped patients (patient_id, name, assigned_coordinator_id, coordinator name)
SELECT p.patient_id,
    p.first_name || ' ' || p.last_name AS patient_name,
    p.last_first_dob,
    p.assigned_coordinator_id,
    u.full_name AS coordinator_full_name
FROM patients p
    LEFT JOIN users u ON u.user_id = p.assigned_coordinator_id
WHERE p.assigned_coordinator_id IS NOT NULL
ORDER BY p.patient_id
LIMIT 50;
COMMIT;
PRAGMA foreign_keys = ON;