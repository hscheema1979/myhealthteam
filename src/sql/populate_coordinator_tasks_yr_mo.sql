-- Create coordinator_tasks_yr_mo table from fresh FRESH_COORDINATOR_TASKS_HISTORY data
-- This includes the most recent July/August/September 2025 data
CREATE TABLE IF NOT EXISTS coordinator_tasks_yr_mo (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    coordinator_id INTEGER,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (coordinator_id) REFERENCES users(user_id)
);
-- Clear any existing data
DELETE FROM coordinator_tasks_yr_mo;
-- Insert fresh data with proper date conversion and filtering
INSERT INTO coordinator_tasks_yr_mo (
        patient_id,
        coordinator_id,
        task_date,
        duration_minutes,
        task_type,
        notes
    )
SELECT p.patient_id,
    u.user_id as coordinator_id,
    -- Convert MM/DD/YY format to YYYY-MM-DD
    CASE
        WHEN LENGTH([Date Only]) = 8
        AND [Date Only] LIKE '%/%/%' THEN CASE
            WHEN CAST(SUBSTR([Date Only], -2) AS INTEGER) >= 50 THEN '19' || SUBSTR([Date Only], -2) || '-' || PRINTF(
                '%02d',
                CAST(
                    SUBSTR([Date Only], 1, INSTR([Date Only], '/') - 1) AS INTEGER
                )
            ) || '-' || PRINTF(
                '%02d',
                CAST(
                    SUBSTR(
                        [Date Only],
                        INSTR([Date Only], '/') + 1,
                        INSTR(
                            SUBSTR([Date Only], INSTR([Date Only], '/') + 1),
                            '/'
                        ) - 1
                    ) AS INTEGER
                )
            )
            ELSE '20' || SUBSTR([Date Only], -2) || '-' || PRINTF(
                '%02d',
                CAST(
                    SUBSTR([Date Only], 1, INSTR([Date Only], '/') - 1) AS INTEGER
                )
            ) || '-' || PRINTF(
                '%02d',
                CAST(
                    SUBSTR(
                        [Date Only],
                        INSTR([Date Only], '/') + 1,
                        INSTR(
                            SUBSTR([Date Only], INSTR([Date Only], '/') + 1),
                            '/'
                        ) - 1
                    ) AS INTEGER
                )
            )
        END
        WHEN LENGTH([Date Only]) = 9
        AND [Date Only] LIKE '%/%/%' THEN CASE
            WHEN CAST(SUBSTR([Date Only], -2) AS INTEGER) >= 50 THEN '19' || SUBSTR([Date Only], -2) || '-' || PRINTF(
                '%02d',
                CAST(
                    SUBSTR([Date Only], 1, INSTR([Date Only], '/') - 1) AS INTEGER
                )
            ) || '-' || PRINTF(
                '%02d',
                CAST(
                    SUBSTR(
                        [Date Only],
                        INSTR([Date Only], '/') + 1,
                        INSTR(
                            SUBSTR([Date Only], INSTR([Date Only], '/') + 1),
                            '/'
                        ) - 1
                    ) AS INTEGER
                )
            )
            ELSE '20' || SUBSTR([Date Only], -2) || '-' || PRINTF(
                '%02d',
                CAST(
                    SUBSTR([Date Only], 1, INSTR([Date Only], '/') - 1) AS INTEGER
                )
            ) || '-' || PRINTF(
                '%02d',
                CAST(
                    SUBSTR(
                        [Date Only],
                        INSTR([Date Only], '/') + 1,
                        INSTR(
                            SUBSTR([Date Only], INSTR([Date Only], '/') + 1),
                            '/'
                        ) - 1
                    ) AS INTEGER
                )
            )
        END
        WHEN LENGTH([Date Only]) = 10
        AND [Date Only] LIKE '%/%/%' THEN SUBSTR([Date Only], -4) || '-' || PRINTF(
            '%02d',
            CAST(
                SUBSTR([Date Only], 1, INSTR([Date Only], '/') - 1) AS INTEGER
            )
        ) || '-' || PRINTF(
            '%02d',
            CAST(
                SUBSTR(
                    [Date Only],
                    INSTR([Date Only], '/') + 1,
                    INSTR(
                        SUBSTR([Date Only], INSTR([Date Only], '/') + 1),
                        '/'
                    ) - 1
                ) AS INTEGER
            )
        )
        ELSE [Date Only]
    END as task_date,
    CAST([Mins B] AS INTEGER) as duration_minutes,
    [Type] as task_type,
    [Notes] as notes
FROM FRESH_COORDINATOR_TASKS_HISTORY fh
    LEFT JOIN patients p ON TRIM(fh.[Pt Name]) = TRIM(p.patient_name)
    LEFT JOIN users u ON TRIM(fh.Staff) = TRIM(u.username)
WHERE fh.[Date Only] IS NOT NULL
    AND fh.[Date Only] != ''
    AND fh.[Mins B] IS NOT NULL
    AND fh.[Mins B] > 0
    AND TRIM(fh.[Pt Name]) != 'Aaa, Aaa' -- Exclude placeholder data
    AND fh.[Type] IS NOT NULL
    AND fh.[Type] != ''
    AND NOT (fh.[Type] LIKE '%Place holder%');
-- Clean up the temporary table
DROP TABLE IF EXISTS FRESH_COORDINATOR_TASKS_HISTORY;