-- Verify coordinator vs patient counts
.headers on.mode column -- Totals overview
SELECT 'total_source_rows' AS metric,
    COUNT(*) AS value
FROM SOURCE_PATIENT_DATA;
SELECT 'total_patients_rows' AS metric,
    COUNT(*) AS value
FROM patients;
SELECT 'total_user_patient_assignments' AS metric,
    COUNT(*) AS value
FROM user_patient_assignments;
-- Per-coordinator summary: source Assigned CM matches, patients.assigned_coordinator_id, user_patient_assignments
SELECT u.user_id,
    u.full_name,
    COALESCE(src.source_count, 0) AS source_count,
    COALESCE(pat.patients_count, 0) AS patients_count,
    COALESCE(upa.assignments_count, 0) AS assignments_count
FROM users u
    LEFT JOIN (
        SELECT LOWER(TRIM(spd."Assigned CM")) AS assigned_cm_lc,
            COUNT(*) AS source_count
        FROM SOURCE_PATIENT_DATA spd
        GROUP BY assigned_cm_lc
    ) src ON LOWER(TRIM(u.full_name)) = src.assigned_cm_lc
    LEFT JOIN (
        SELECT assigned_coordinator_id AS user_id,
            COUNT(*) AS patients_count
        FROM patients
        WHERE assigned_coordinator_id IS NOT NULL
            AND assigned_coordinator_id != ''
        GROUP BY assigned_coordinator_id
    ) pat ON pat.user_id = u.user_id
    LEFT JOIN (
        SELECT user_id,
            COUNT(*) AS assignments_count
        FROM user_patient_assignments
        GROUP BY user_id
    ) upa ON upa.user_id = u.user_id
ORDER BY source_count DESC,
    patients_count DESC,
    assignments_count DESC;
-- Show users that have source counts but are not in users table (i.e., unmapped names)
SELECT src.assigned_cm AS missing_full_name,
    src.source_count
FROM (
        SELECT LOWER(TRIM(spd."Assigned CM")) AS assigned_cm,
            COUNT(*) AS source_count
        FROM SOURCE_PATIENT_DATA spd
        GROUP BY assigned_cm
    ) src
    LEFT JOIN users u ON LOWER(TRIM(u.full_name)) = src.assigned_cm
WHERE u.user_id IS NULL
ORDER BY src.source_count DESC;