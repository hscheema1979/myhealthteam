-- Create separate monthly coordinator task tables from SOURCE_COORDINATOR_TASKS_HISTORY
-- This script will create tables like coordinator_tasks_2025_07, coordinator_tasks_2025_06, etc.
-- First, let's create a helper view to standardize the dates and clean patient names
CREATE TEMP VIEW date_standardized AS
SELECT *,
    -- Clean patient names by removing ZEN- prefix and trimming
    CASE
        WHEN [Pt Name] LIKE 'ZEN-%' THEN TRIM(SUBSTR([Pt Name], 5))
        ELSE TRIM([Pt Name])
    END as clean_patient_name,
    -- Parse year
    CASE
        -- Handle MM/DD/YY format where YY is 2-digit
        WHEN LENGTH(TRIM([Date Only])) BETWEEN 8 AND 10
        AND [Date Only] LIKE '%/%/%' THEN CASE
            WHEN CAST(SUBSTR(TRIM([Date Only]), -2) AS INTEGER) >= 50 THEN CAST('19' || SUBSTR(TRIM([Date Only]), -2) AS INTEGER)
            ELSE CASE
                WHEN SUBSTR(TRIM([Date Only]), -2) = '25' THEN 2025
                WHEN SUBSTR(TRIM([Date Only]), -1) = '5' THEN 2025 -- Special case for '5' meaning 2025
                ELSE CAST('20' || SUBSTR(TRIM([Date Only]), -2) AS INTEGER)
            END
        END -- Handle MM/DD/YYYY format (like 07/15/2025)
        WHEN LENGTH(TRIM([Date Only])) = 10
        AND [Date Only] LIKE '%/%/%' THEN CAST(SUBSTR(TRIM([Date Only]), -4) AS INTEGER)
        ELSE NULL
    END as year_parsed,
    -- Parse month
    CASE
        WHEN TRIM([Date Only]) LIKE '%/%/%' THEN CAST(
            SUBSTR(
                TRIM([Date Only]),
                1,
                INSTR(TRIM([Date Only]), '/') - 1
            ) AS INTEGER
        )
        ELSE NULL
    END as month_parsed,
    -- Parse day
    CASE
        WHEN TRIM([Date Only]) LIKE '%/%/%' THEN CAST(
            SUBSTR(
                TRIM([Date Only]),
                INSTR(TRIM([Date Only]), '/') + 1,
                INSTR(
                    SUBSTR(
                        TRIM([Date Only]),
                        INSTR(TRIM([Date Only]), '/') + 1
                    ),
                    '/'
                ) - 1
            ) AS INTEGER
        )
        ELSE NULL
    END as day_parsed
FROM SOURCE_COORDINATOR_TASKS_HISTORY
WHERE [Date Only] IS NOT NULL
    AND TRIM([Date Only]) != ''
    AND [Date Only] LIKE '%/%/%'
    AND [Mins B] IS NOT NULL
    AND [Mins B] > 0
    AND TRIM([Pt Name]) != 'Aaa, Aaa' -- Exclude placeholder data
    AND [Type] IS NOT NULL
    AND TRIM([Type]) != ''
    AND NOT ([Type] LIKE '%Place holder%');
-- Create coordinator_tasks_2025_07 (July 2025)
DROP TABLE IF EXISTS coordinator_tasks_2025_07;
CREATE TABLE coordinator_tasks_2025_07 (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    coordinator_id INTEGER,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    raw_date TEXT,
    -- Keep original date for reference
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (coordinator_id) REFERENCES users(user_id)
);
INSERT INTO coordinator_tasks_2025_07 (
        patient_id,
        coordinator_id,
        task_date,
        duration_minutes,
        task_type,
        notes,
        raw_date
    )
SELECT COALESCE(p.patient_id, ds.clean_patient_name) as patient_id,
    -- Use patient_id if found, otherwise keep raw clean name
    COALESCE(u.user_id, ds.Staff) as coordinator_id,
    -- Use user_id if found, otherwise keep raw staff code
    PRINTF('2025-%02d-%02d', ds.month_parsed, ds.day_parsed) as task_date,
    CAST(ds.[Mins B] AS INTEGER) as duration_minutes,
    ds.[Type] as task_type,
    ds.[Notes] as notes,
    ds.[Date Only] as raw_date
FROM date_standardized ds
    LEFT JOIN patients p ON ds.clean_patient_name = p.last_first_dob
    LEFT JOIN users u ON TRIM(ds.Staff) = TRIM(u.username)
WHERE ds.year_parsed = 2025
    AND ds.month_parsed = 7;
-- Create coordinator_tasks_2025_06 (June 2025)
DROP TABLE IF EXISTS coordinator_tasks_2025_06;
CREATE TABLE coordinator_tasks_2025_06 (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    coordinator_id INTEGER,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    raw_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (coordinator_id) REFERENCES users(user_id)
);
INSERT INTO coordinator_tasks_2025_06 (
        patient_id,
        coordinator_id,
        task_date,
        duration_minutes,
        task_type,
        notes,
        raw_date
    )
SELECT COALESCE(p.patient_id, ds.clean_patient_name) as patient_id,
    COALESCE(u.user_id, ds.Staff) as coordinator_id,
    PRINTF('2025-%02d-%02d', ds.month_parsed, ds.day_parsed) as task_date,
    CAST(ds.[Mins B] AS INTEGER) as duration_minutes,
    ds.[Type] as task_type,
    ds.[Notes] as notes,
    ds.[Date Only] as raw_date
FROM date_standardized ds
    LEFT JOIN patients p ON ds.clean_patient_name = p.last_first_dob
    LEFT JOIN users u ON TRIM(ds.Staff) = TRIM(u.username)
WHERE ds.year_parsed = 2025
    AND ds.month_parsed = 6;
-- Create coordinator_tasks_2025_05 (May 2025)
DROP TABLE IF EXISTS coordinator_tasks_2025_05;
CREATE TABLE coordinator_tasks_2025_05 (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    coordinator_id INTEGER,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    raw_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (coordinator_id) REFERENCES users(user_id)
);
INSERT INTO coordinator_tasks_2025_05 (
        patient_id,
        coordinator_id,
        task_date,
        duration_minutes,
        task_type,
        notes,
        raw_date
    )
SELECT COALESCE(p.patient_id, ds.clean_patient_name) as patient_id,
    COALESCE(u.user_id, ds.Staff) as coordinator_id,
    PRINTF('2025-%02d-%02d', ds.month_parsed, ds.day_parsed) as task_date,
    CAST(ds.[Mins B] AS INTEGER) as duration_minutes,
    ds.[Type] as task_type,
    ds.[Notes] as notes,
    ds.[Date Only] as raw_date
FROM date_standardized ds
    LEFT JOIN patients p ON ds.clean_patient_name = p.last_first_dob
    LEFT JOIN users u ON TRIM(ds.Staff) = TRIM(u.username)
WHERE ds.year_parsed = 2025
    AND ds.month_parsed = 5;
-- Create coordinator_tasks_2025_04 (April 2025)
DROP TABLE IF EXISTS coordinator_tasks_2025_04;
CREATE TABLE coordinator_tasks_2025_04 (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    coordinator_id INTEGER,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    raw_date TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (coordinator_id) REFERENCES users(user_id)
);
INSERT INTO coordinator_tasks_2025_04 (
        patient_id,
        coordinator_id,
        task_date,
        duration_minutes,
        task_type,
        notes,
        raw_date
    )
SELECT COALESCE(p.patient_id, ds.clean_patient_name) as patient_id,
    COALESCE(u.user_id, ds.Staff) as coordinator_id,
    PRINTF('2025-%02d-%02d', ds.month_parsed, ds.day_parsed) as task_date,
    CAST(ds.[Mins B] AS INTEGER) as duration_minutes,
    ds.[Type] as task_type,
    ds.[Notes] as notes,
    ds.[Date Only] as raw_date
FROM date_standardized ds
    LEFT JOIN patients p ON ds.clean_patient_name = p.last_first_dob
    LEFT JOIN users u ON TRIM(ds.Staff) = TRIM(u.username)
WHERE ds.year_parsed = 2025
    AND ds.month_parsed = 4;
-- Display summary of created tables
SELECT 'coordinator_tasks_2025_07' as table_name,
    COUNT(*) as records
FROM coordinator_tasks_2025_07
UNION ALL
SELECT 'coordinator_tasks_2025_06' as table_name,
    COUNT(*) as records
FROM coordinator_tasks_2025_06
UNION ALL
SELECT 'coordinator_tasks_2025_05' as table_name,
    COUNT(*) as records
FROM coordinator_tasks_2025_05
UNION ALL
SELECT 'coordinator_tasks_2025_04' as table_name,
    COUNT(*) as records
FROM coordinator_tasks_2025_04;