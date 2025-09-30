-- Staging provider tasks: normalize date and pt name
DROP TABLE IF EXISTS staging_provider_tasks;
CREATE TABLE staging_provider_tasks AS
SELECT
  rowid AS src_rowid,
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