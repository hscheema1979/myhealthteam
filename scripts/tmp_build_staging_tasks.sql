ATTACH './sheets_data.db' AS staging;
CREATE TEMP VIEW IF NOT EXISTS SOURCE_COORDINATOR_TASKS_HISTORY AS SELECT * FROM staging.source_coordinator_tasks_history;
CREATE TEMP VIEW IF NOT EXISTS SOURCE_PROVIDER_TASKS_HISTORY AS SELECT * FROM staging.SOURCE_PROVIDER_TASKS_HISTORY;

-- Build staging_coordinator_tasks from SOURCE_COORDINATOR_TASKS_HISTORY
DROP TABLE IF EXISTS staging_coordinator_tasks;
CREATE TABLE staging_coordinator_tasks AS
SELECT
  "Staff" AS staff_code,
  "Pt Name" AS patient_name_raw,
  TRIM("Type") AS task_type,
  TRIM("Notes") AS notes,
  "Mins B" AS minutes_raw,
  -- normalized ISO date (YYYY-MM-DD) when possible
  CASE
    WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
    WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
    ELSE NULL
  END AS activity_date,
  -- derived partition key 'YYYY_MM'
  CASE
    WHEN "Date Only" IS NOT NULL THEN
      CASE
        WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '_' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER))
        WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '_' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER))
        ELSE NULL
      END
    ELSE NULL
  END AS year_month
FROM SOURCE_COORDINATOR_TASKS_HISTORY;

CREATE INDEX IF NOT EXISTS idx_staging_coordinator_year_month ON staging_coordinator_tasks(year_month);
CREATE INDEX IF NOT EXISTS idx_staging_coordinator_activity_date ON staging_coordinator_tasks(activity_date);

-- Build staging_provider_tasks from SOURCE_PROVIDER_TASKS_HISTORY
DROP TABLE IF EXISTS staging_provider_tasks;
CREATE TABLE staging_provider_tasks AS
SELECT
  "Prov" AS provider_code,
  "Patient Last, First DOB" AS patient_name_raw,
  TRIM("Service") AS service,
  TRIM("Coding") AS billing_code,
  "Minutes" AS minutes_raw,
  CASE
    WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
    WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
    ELSE NULL
  END AS activity_date,
  CASE
    WHEN "DOS" IS NOT NULL THEN
      CASE
        WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '_' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER))
        WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '_' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER))
        ELSE NULL
      END
    ELSE NULL
  END AS year_month
FROM SOURCE_PROVIDER_TASKS_HISTORY;

CREATE INDEX IF NOT EXISTS idx_staging_provider_year_month ON staging_provider_tasks(year_month);
CREATE INDEX IF NOT EXISTS idx_staging_provider_activity_date ON staging_provider_tasks(activity_date);