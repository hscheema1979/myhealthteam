-- QA: Compare counts from user_patient_assignments vs patients.assigned_coordinator_id
.headers on.mode column -- Counts per coordinator from patients.assigned_coordinator_id
SELECT 'patients_table' AS src,
    p.assigned_coordinator_id AS user_id,
    COUNT(*) AS cnt
FROM patients p
WHERE p.assigned_coordinator_id IS NOT NULL
    AND p.assigned_coordinator_id != ''
GROUP BY p.assigned_coordinator_id
ORDER BY cnt DESC
LIMIT 50;
-- Counts per coordinator from user_patient_assignments
SELECT 'assignments_table' AS src,
    upa.user_id AS user_id,
    COUNT(DISTINCT upa.patient_id) AS cnt
FROM user_patient_assignments upa
GROUP BY upa.user_id
ORDER BY cnt DESC
LIMIT 50;
-- For top coordinators, show phone coverage: count patients assigned (by patients.assigned_coordinator_id) and how many have phone_primary
SELECT p.assigned_coordinator_id AS user_id,
    COUNT(*) AS total_assigned,
    SUM(
        CASE
            WHEN TRIM(COALESCE(p.phone_primary, '')) = '' THEN 0
            ELSE 1
        END
    ) AS with_phone,
    SUM(
        CASE
            WHEN TRIM(COALESCE(p.phone_primary, '')) = '' THEN 1
            ELSE 0
        END
    ) AS without_phone
FROM patients p
WHERE p.assigned_coordinator_id IS NOT NULL
    AND p.assigned_coordinator_id != ''
GROUP BY p.assigned_coordinator_id
ORDER BY total_assigned DESC
LIMIT 50;
-- Show sample patients (id, name, phone_primary) for user_id = 8 (Dianela)
SELECT p.patient_id,
    p.first_name || ' ' || p.last_name AS name,
    TRIM(COALESCE(p.phone_primary, '')) AS phone_primary
FROM patients p
WHERE p.assigned_coordinator_id = 8
ORDER BY p.patient_id
LIMIT 50;