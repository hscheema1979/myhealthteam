-- Staging coordinator tasks: normalize date and pt name
DROP TABLE IF EXISTS staging.staging_coordinator_tasks;
CREATE TABLE staging.staging_coordinator_tasks AS
SELECT "Staff" AS staff_code,
  "Pt Name" AS patient_name_raw,
  TRIM("Type") AS task_type,
  TRIM("Notes") AS notes,
  "Mins B" AS minutes_raw,
  -- normalized ISO date (YYYY-MM-DD) when possible
  CASE
    WHEN TRIM("Date Only") GLOB '??/??/????' THEN substr(TRIM("Date Only"), 7, 4) || '-' || printf(
      '%02d',
      CAST(substr(TRIM("Date Only"), 1, 2) AS INTEGER)
    ) || '-' || printf(
      '%02d',
      CAST(substr(TRIM("Date Only"), 4, 2) AS INTEGER)
    )
    WHEN TRIM("Date Only") GLOB '??/??/??' THEN '20' || substr(TRIM("Date Only"), 7, 2) || '-' || printf(
      '%02d',
      CAST(substr(TRIM("Date Only"), 1, 2) AS INTEGER)
    ) || '-' || printf(
      '%02d',
      CAST(substr(TRIM("Date Only"), 4, 2) AS INTEGER)
    )
    ELSE NULL
  END AS activity_date,
  -- derived partition key 'YYYY_MM'
  CASE
    WHEN TRIM("Date Only") IS NOT NULL THEN CASE
      WHEN TRIM("Date Only") GLOB '??/??/????' THEN substr(TRIM("Date Only"), 7, 4) || '_' || printf(
        '%02d',
        CAST(substr(TRIM("Date Only"), 1, 2) AS INTEGER)
      )
      WHEN TRIM("Date Only") GLOB '??/??/??' THEN '20' || substr(TRIM("Date Only"), 7, 2) || '_' || printf(
        '%02d',
        CAST(substr(TRIM("Date Only"), 1, 2) AS INTEGER)
      )
      ELSE NULL
    END
    ELSE NULL
  END AS year_month
FROM SOURCE_COORDINATOR_TASKS_HISTORY;
CREATE INDEX IF NOT EXISTS staging.idx_staging_coordinator_year_month ON staging_coordinator_tasks(year_month);
CREATE INDEX IF NOT EXISTS staging.idx_staging_coordinator_activity_date ON staging_coordinator_tasks(activity_date);