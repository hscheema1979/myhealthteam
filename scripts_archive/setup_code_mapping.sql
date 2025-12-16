PRAGMA foreign_keys = OFF;

-- Provider code mapping table: maps normalized provider_code to users.user_id
CREATE TABLE IF NOT EXISTS provider_code_map (
  provider_code_norm TEXT PRIMARY KEY,
  user_id INTEGER
);

-- Coordinator code mapping table: maps normalized staff_code to users.user_id
CREATE TABLE IF NOT EXISTS coordinator_code_map (
  staff_code_norm TEXT PRIMARY KEY,
  user_id INTEGER
);

-- View: staging provider tasks with mapped provider user id (non-destructive)
DROP VIEW IF EXISTS staging_provider_tasks_mapped;
CREATE VIEW staging_provider_tasks_mapped AS
SELECT 
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(spt.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
  spt.activity_date,
  spt.provider_code AS provider_code_raw,
  UPPER(TRIM(spt.provider_code)) AS provider_code_norm,
  pcm.user_id AS provider_user_id
FROM staging_provider_tasks spt
LEFT JOIN provider_code_map pcm ON pcm.provider_code_norm = UPPER(TRIM(spt.provider_code));

-- View: staging coordinator tasks with mapped coordinator user id (non-destructive)
DROP VIEW IF EXISTS staging_coordinator_tasks_mapped;
CREATE VIEW staging_coordinator_tasks_mapped AS
SELECT 
  TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE(sct.patient_name_raw, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', '')) AS patient_id,
  sct.activity_date,
  sct.staff_code AS staff_code_raw,
  UPPER(TRIM(REPLACE(CAST(sct.staff_code AS TEXT), '.0', ''))) AS staff_code_norm,
  ccm.user_id AS coordinator_user_id
FROM staging_coordinator_tasks sct
LEFT JOIN coordinator_code_map ccm ON ccm.staff_code_norm = UPPER(TRIM(REPLACE(CAST(sct.staff_code AS TEXT), '.0', '')));