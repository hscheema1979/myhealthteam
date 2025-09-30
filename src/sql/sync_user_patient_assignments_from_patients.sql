-- Sync user_patient_assignments from patients.assigned_coordinator_id
PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;
-- Snapshot current user_patient_assignments
DROP TABLE IF EXISTS user_patient_assignments_snapshot_sync;
CREATE TABLE user_patient_assignments_snapshot_sync AS
SELECT *
FROM user_patient_assignments;
-- Count current assignments
SELECT 'before_total_assignments' AS metric,
    COUNT(*) AS value
FROM user_patient_assignments;
-- Insert missing assignments: for each patient with assigned_coordinator_id set, ensure a row exists
INSERT INTO user_patient_assignments (user_id, patient_id)
SELECT p.assigned_coordinator_id AS user_id,
    p.patient_id
FROM patients p
WHERE p.assigned_coordinator_id IS NOT NULL
    AND p.assigned_coordinator_id != ''
    AND NOT EXISTS (
        SELECT 1
        FROM user_patient_assignments upa
        WHERE upa.user_id = p.assigned_coordinator_id
            AND upa.patient_id = p.patient_id
    );
-- Counts after insert
SELECT 'after_total_assignments' AS metric,
    COUNT(*) AS value
FROM user_patient_assignments;
-- Show how many assignments were added per user (top 20)
SELECT user_id,
    COUNT(*) AS added_count
FROM (
        SELECT upa.user_id,
            upa.patient_id
        FROM user_patient_assignments upa
            LEFT JOIN user_patient_assignments_snapshot_sync s ON s.user_id = upa.user_id
            AND s.patient_id = upa.patient_id
        WHERE s.user_id IS NULL
    )
GROUP BY user_id
ORDER BY added_count DESC
LIMIT 50;
-- Show sample assignments for user_id = 8
SELECT user_id,
    patient_id
FROM user_patient_assignments
WHERE user_id = 8
ORDER BY patient_id
LIMIT 20;
COMMIT;
PRAGMA foreign_keys = ON;