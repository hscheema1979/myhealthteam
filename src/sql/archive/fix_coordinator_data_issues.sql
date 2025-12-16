-- fix_coordinator_data_issues.sql
-- Create minimal patient records from staging_coordinator_tasks where patient_name_raw contains DOB in MM/DD/YYYY
-- Insert new patients (avoid duplicates)
INSERT INTO patients (
        first_name,
        last_name,
        date_of_birth,
        last_first_dob
    )
SELECT DISTINCT trim(
        substr(
            patient_name_raw,
            instr(patient_name_raw, ',') + 1,
            instr(substr(patient_name_raw, instr(patient_name_raw, ',') + 1), ' ') - 1
        )
    ) AS first_name,
    trim(
        substr(patient_name_raw, 1, instr(patient_name_raw, ',') - 1)
    ) AS last_name,
    date(
        substr(patient_name_raw, -10, 4) || '-' || substr(patient_name_raw, -7, 2) || '-' || substr(patient_name_raw, -4, 2)
    ) AS date_of_birth,
    patient_name_raw AS last_first_dob
FROM staging_coordinator_tasks
WHERE length(patient_name_raw) >= 10
    AND instr(patient_name_raw, ',') > 0
    AND instr(patient_name_raw, '/') > 0
    AND NOT EXISTS (
        SELECT 1
        FROM patients p
        WHERE p.last_first_dob = staging_coordinator_tasks.patient_name_raw
    );

-- After creating patients, you can re-run the transform to pick up numeric patient_id matches
-- Fix Date Format Inconsistencies and Add Missing Patients
-- This script standardizes all date formats and creates missing patient records
-- Step 1: Fix inconsistent date formats in coordinator_tasks
UPDATE coordinator_tasks
SET task_date = CASE
        -- Handle MM/DD/YY format (2-digit year) - assume 20XX for dates 00-30, 19XX for 31-99
        WHEN task_date LIKE '__/__/__'
        AND length(task_date) = 8 THEN substr(task_date, 7, 2) || CASE
            WHEN CAST(substr(task_date, 7, 2) AS INTEGER) <= 30 THEN '20'
            ELSE '19'
        END || substr(task_date, 7, 2) || '-' || printf('%02d', CAST(substr(task_date, 1, 2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(task_date, 4, 2) AS INTEGER)) -- Handle MM/DD/YY format
        WHEN task_date LIKE '__/__/____'
        AND length(task_date) = 10 THEN substr(task_date, 7, 4) || '-' || printf('%02d', CAST(substr(task_date, 1, 2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(task_date, 4, 2) AS INTEGER)) -- Handle MM/D/YYYY format
        WHEN task_date LIKE '__/_/____'
        AND length(task_date) = 9 THEN substr(task_date, 6, 4) || '-' || printf('%02d', CAST(substr(task_date, 1, 2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(task_date, 4, 1) AS INTEGER)) -- Handle M/DD/YYYY format
        WHEN task_date LIKE '_/__/____'
        AND length(task_date) = 9 THEN substr(task_date, 6, 4) || '-' || printf('%02d', CAST(substr(task_date, 1, 1) AS INTEGER)) || '-' || printf('%02d', CAST(substr(task_date, 3, 2) AS INTEGER)) -- Handle M/D/YYYY format
        WHEN task_date LIKE '_/_/____'
        AND length(task_date) = 8 THEN substr(task_date, 5, 4) || '-' || printf('%02d', CAST(substr(task_date, 1, 1) AS INTEGER)) || '-' || printf('%02d', CAST(substr(task_date, 3, 1) AS INTEGER)) -- Handle weird formats with day names - try to extract date part
        WHEN task_date LIKE '%/%'
        AND task_date LIKE '%/%' THEN -- For formats like "MM/DD/WWW", extract just the date part
        CASE
            WHEN instr(task_date, '/') > 0
            AND instr(
                substr(task_date, instr(task_date, '/') + 1),
                '/'
            ) > 0 THEN -- Extract year part after second slash, take first 2 or 4 digits
            '20' || CASE
                WHEN length(
                    substr(
                        task_date,
                        instr(
                            substr(task_date, instr(task_date, '/') + 1),
                            '/'
                        ) + instr(task_date, '/') + 1,
                        2
                    )
                ) = 2 THEN substr(
                    task_date,
                    instr(
                        substr(task_date, instr(task_date, '/') + 1),
                        '/'
                    ) + instr(task_date, '/') + 1,
                    2
                )
                ELSE substr(
                    task_date,
                    instr(
                        substr(task_date, instr(task_date, '/') + 1),
                        '/'
                    ) + instr(task_date, '/') + 1,
                    4
                )
            END || '-' || printf('%02d', CAST(substr(task_date, 1, 2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(task_date, 4, 2) AS INTEGER))
            ELSE task_date -- Leave as-is if can't parse
        END -- Already in YYYY-MM-DD format
        WHEN task_date LIKE '____-__-__' THEN task_date -- Default: try to salvage anything that looks like a date
        ELSE task_date
    END
WHERE task_date IS NOT NULL
    AND task_date NOT LIKE '____-__-__';
-- Step 2: Create missing patients based on coordinator_tasks references
-- First, parse the "Last, First DOB" format to extract components
INSERT
    OR IGNORE INTO patients (
        last_name,
        first_name,
        date_of_birth,
        last_first_dob,
        status,
        created_date,
        updated_date
    )
SELECT DISTINCT -- Extract last name (everything before first comma)
    TRIM(
        substr(ct.patient_id, 1, instr(ct.patient_id, ',') - 1)
    ) as last_name,
    -- Extract first name (between comma and date)
    TRIM(
        substr(
            ct.patient_id,
            instr(ct.patient_id, ',') + 1,
            instr(ct.patient_id, ' ') - instr(ct.patient_id, ',') - 1
        )
    ) as first_name,
    -- Extract and standardize DOB (assumes MM/DD/YYYY format at end)
    CASE
        WHEN ct.patient_id LIKE '%/%/%' THEN -- Find the last date-like pattern
        substr(ct.patient_id, -10, 4) || '-' || printf(
            '%02d',
            CAST(substr(ct.patient_id, -10, 2) AS INTEGER)
        ) || '-' || printf(
            '%02d',
            CAST(substr(ct.patient_id, -7, 2) AS INTEGER)
        )
        ELSE NULL
    END as date_of_birth,
    ct.patient_id as last_first_dob,
    'Active' as status,
    datetime('now') as created_date,
    datetime('now') as updated_date
FROM coordinator_tasks ct
WHERE ct.patient_id IS NOT NULL
    AND ct.patient_id NOT IN (
        SELECT patient_id
        FROM patients
        WHERE patient_id IS NOT NULL
    )
    AND ct.patient_id NOT IN (
        SELECT last_first_dob
        FROM patients
        WHERE last_first_dob IS NOT NULL
    )
    AND ct.patient_id LIKE '%,%' -- Must contain comma (Last, First format)
    AND ct.patient_id LIKE '%/%/%' -- Must contain date pattern
    AND length(ct.patient_id) > 10;
-- Must be reasonable length
-- Step 3: Update coordinator_tasks to link to newly created patients
UPDATE coordinator_tasks
SET patient_id = (
        SELECT p.patient_id
        FROM patients p
        WHERE p.last_first_dob = coordinator_tasks.patient_id
        LIMIT 1
    )
WHERE patient_id IS NOT NULL
    AND patient_id NOT IN (
        SELECT CAST(patient_id AS TEXT)
        FROM patients
        WHERE patient_id IS NOT NULL
    )
    AND EXISTS (
        SELECT 1
        FROM patients p
        WHERE p.last_first_dob = coordinator_tasks.patient_id
    );
-- Step 4: Add patient display names for tasks that have valid patient_id links
UPDATE coordinator_tasks
SET patient_name = (
        SELECT p.first_name || ' ' || p.last_name
        FROM patients p
        WHERE CAST(p.patient_id AS TEXT) = coordinator_tasks.patient_id
        LIMIT 1
    )
WHERE patient_name IS NULL
    AND patient_id IS NOT NULL
    AND patient_id IN (
        SELECT CAST(patient_id AS TEXT)
        FROM patients
        WHERE patient_id IS NOT NULL
    );
-- Report results
SELECT 'Date Standardization Results' as report_section,
    COUNT(*) as total_records,
    COUNT(
        CASE
            WHEN task_date LIKE '____-__-__' THEN 1
        END
    ) as standardized_dates,
    COUNT(
        CASE
            WHEN task_date NOT LIKE '____-__-__' THEN 1
        END
    ) as non_standard_dates
FROM coordinator_tasks
WHERE task_date IS NOT NULL
UNION ALL
SELECT 'Patient Creation Results' as report_section,
    COUNT(*) as patients_created,
    0 as standardized_dates,
    0 as non_standard_dates
FROM patients
WHERE notes LIKE '%Auto-created from coordinator tasks%'
UNION ALL
SELECT 'Task-Patient Linking Results' as report_section,
    COUNT(*) as tasks_with_valid_patients,
    0 as standardized_dates,
    0 as non_standard_dates
FROM coordinator_tasks ct
WHERE ct.patient_id IS NOT NULL
    AND EXISTS (
        SELECT 1
        FROM patients p
        WHERE p.patient_id = ct.patient_id
    );