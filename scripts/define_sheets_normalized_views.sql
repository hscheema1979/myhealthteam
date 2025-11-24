-- Define normalized, production-equivalent views inside sheets_data.db
-- Non-destructive: raw SOURCE_* tables remain unchanged

PRAGMA foreign_keys = OFF;

-- Helper note: We currently strip known system prefixes minimally (ZEN-).
-- If you approve, we can extend to additional prefixes (e.g., PM-, etc.).

-- View: V_PROVIDER_TASKS_NORM (aligns with staging_provider_tasks columns)
DROP VIEW IF EXISTS V_PROVIDER_TASKS_NORM;
CREATE VIEW V_PROVIDER_TASKS_NORM AS
SELECT
  -- Canonical patient identifier: remove commas and common system prefixes; keep LAST FIRST DOB ordering
  -- Unified normalization: strip known system prefixes (ZEN-, PM-, ZMN-, BlessedCare/BleessedCare, 3PR), convert commas to spaces, collapse whitespace, trim
  TRIM(
    REPLACE(
      REPLACE(
        REPLACE(
          REPLACE(
            REPLACE(
              REPLACE(
                REPLACE(
                  REPLACE(
                    REPLACE(REPLACE("Patient Last, First DOB", ',', ' '), 'ZEN-', ''),
                    'PM-', ''
                  ),
                  'ZMN-', ''
                ),
                'BlessedCare-', ''
              ),
              'BLESSEDCARE-', ''
            ),
            'BleessedCare-', ''
          ),
          'BLEESSEDCARE-', ''
        ),
        '3PR-', ''
      ),
      '3PR -', ''
    )
  ) AS patient_id,
  "Patient Last, First DOB" AS patient_name_raw,
  TRIM("Prov") AS provider_code,
  UPPER(TRIM("Prov")) AS provider_code_norm,
  TRIM("Service") AS service,
  CASE
    WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
    WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
    ELSE NULL
  END AS activity_date,
  CASE
    WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '_' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER))
    WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '_' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER))
    ELSE NULL
  END AS year_month
FROM SOURCE_PROVIDER_TASKS_HISTORY
WHERE "Patient Last, First DOB" IS NOT NULL AND TRIM("Patient Last, First DOB") != '';

-- View: V_COORDINATOR_TASKS_NORM (aligns with staging_coordinator_tasks columns)
DROP VIEW IF EXISTS V_COORDINATOR_TASKS_NORM;
CREATE VIEW V_COORDINATOR_TASKS_NORM AS
SELECT
  -- Unified normalization
  TRIM(
    REPLACE(
      REPLACE(
        REPLACE(
          REPLACE(
            REPLACE(
              REPLACE(
                REPLACE(
                  REPLACE(
                    REPLACE(REPLACE("Pt Name", ',', ' '), 'ZEN-', ''),
                    'PM-', ''
                  ),
                  'ZMN-', ''
                ),
                'BlessedCare-', ''
              ),
              'BLESSEDCARE-', ''
            ),
            'BleessedCare-', ''
          ),
          'BLEESSEDCARE-', ''
        ),
        '3PR-', ''
      ),
      '3PR -', ''
    )
  ) AS patient_id,
  "Pt Name" AS patient_name_raw,
  TRIM("Staff") AS staff_code,
  UPPER(TRIM("Staff")) AS staff_code_norm,
  TRIM("Type") AS task_type,
  TRIM("Notes") AS notes,
  CASE
    WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
    WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
    ELSE NULL
  END AS activity_date,
  CASE
    WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '_' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER))
    WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '_' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER))
    ELSE NULL
  END AS year_month
FROM SOURCE_COORDINATOR_TASKS_HISTORY
WHERE "Pt Name" IS NOT NULL AND TRIM("Pt Name") != '';

-- View: V_PATIENT_VISITS_EQUIV (aligns with production patient_visits minimal fields)
-- Uses provider tasks as source of last visit
DROP VIEW IF EXISTS V_PATIENT_VISITS_EQUIV;
CREATE VIEW V_PATIENT_VISITS_EQUIV AS
WITH provider AS (
  SELECT patient_id, activity_date, service
  FROM V_PROVIDER_TASKS_NORM
  WHERE activity_date IS NOT NULL
), latest AS (
  SELECT patient_id, MAX(activity_date) AS last_visit_date
  FROM provider
  GROUP BY patient_id
)
SELECT l.patient_id,
       l.last_visit_date,
       (SELECT TRIM(p.service) FROM provider p WHERE p.patient_id = l.patient_id AND p.activity_date = l.last_visit_date LIMIT 1) AS service_type
FROM latest l;

-- View: V_PATIENT_PANEL_LAST_VISIT_EQUIV (aligns with production panel last-visit fields)
DROP VIEW IF EXISTS V_PATIENT_PANEL_LAST_VISIT_EQUIV;
CREATE VIEW V_PATIENT_PANEL_LAST_VISIT_EQUIV AS
SELECT v.patient_id,
       v.last_visit_date,
       v.service_type AS last_visit_service_type
FROM V_PATIENT_VISITS_EQUIV v;

-- View: V_PATIENTS_EQUIV (aligns with curated patients minimal fields from SOURCE_PATIENT_DATA)
DROP VIEW IF EXISTS V_PATIENTS_EQUIV;
CREATE VIEW V_PATIENTS_EQUIV AS
SELECT
  -- Prefer [LAST FIRST DOB] if present; else construct from Last/First/DOB
  -- Unified normalization over preferred patient identifier source
  TRIM(
    REPLACE(
      REPLACE(
        REPLACE(
          REPLACE(
            REPLACE(
              REPLACE(
                REPLACE(
                  REPLACE(
                    REPLACE(
                      REPLACE(
                        COALESCE(TRIM([LAST FIRST DOB]), TRIM(COALESCE(Last,'') || ' ' || COALESCE(First,'') || ' ' || COALESCE(DOB,''))),
                        ',', ' '
                      ),
                      'ZEN-', ''
                    ),
                    'PM-', ''
                  ),
                  'ZMN-', ''
                ),
                'BlessedCare-', ''
              ),
              'BLESSEDCARE-', ''
            ),
            'BleessedCare-', ''
          ),
          'BLEESSEDCARE-', ''
        ),
        '3PR-', ''
      ),
      '3PR -', ''
    )
  ) AS patient_id,
  TRIM(Last) AS last_name,
  TRIM(First) AS first_name,
  TRIM(DOB) AS dob_raw,
  CASE
    WHEN TRIM(DOB) GLOB '??/??/????' THEN substr(DOB,7,4) || '-' || printf('%02d', CAST(substr(DOB,1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(DOB,4,2) AS INTEGER))
    WHEN TRIM(DOB) GLOB '??/??/??' THEN '20' || substr(DOB,7,2) || '-' || printf('%02d', CAST(substr(DOB,1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr(DOB,4,2) AS INTEGER))
    ELSE NULL
  END AS dob_yyyy_mm_dd
FROM SOURCE_PATIENT_DATA
WHERE (
  [LAST FIRST DOB] IS NOT NULL AND TRIM([LAST FIRST DOB]) <> ''
) OR (
  (Last IS NOT NULL OR First IS NOT NULL OR DOB IS NOT NULL)
  AND TRIM(COALESCE(Last,'') || ' ' || COALESCE(First,'') || ' ' || COALESCE(DOB,'')) <> ''
);

-- Optional: convenience views over existing EXPORT_* tables (if staging_curated_exports.sql was used)
DROP VIEW IF EXISTS V_EXPORT_PATIENT_VISITS;
CREATE VIEW V_EXPORT_PATIENT_VISITS AS
SELECT patient_id, last_visit_date, service_type FROM EXPORT_PATIENT_VISITS;

DROP VIEW IF EXISTS V_EXPORT_PATIENT_PANEL_LAST_VISIT;
CREATE VIEW V_EXPORT_PATIENT_PANEL_LAST_VISIT AS
SELECT patient_id, last_visit_date, last_visit_service_type FROM EXPORT_PATIENT_PANEL_LAST_VISIT;