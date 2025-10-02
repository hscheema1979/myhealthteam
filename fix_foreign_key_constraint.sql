-- Fix foreign key constraint in dashboard_patient_zip_map table
-- This script corrects the foreign key reference from "patients_old" to "patients"

BEGIN TRANSACTION;

-- Create a temporary table with the correct foreign key constraint
CREATE TABLE IF NOT EXISTS "dashboard_patient_zip_map_temp" (
    map_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    zip_code TEXT NOT NULL,
    city TEXT,
    state TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES "patients"(patient_id)
);

-- Copy data from the old table to the new table
INSERT INTO dashboard_patient_zip_map_temp (map_id, patient_id, zip_code, city, state, created_date, updated_date)
SELECT map_id, patient_id, zip_code, city, state, created_date, updated_date
FROM dashboard_patient_zip_map;

-- Drop the old table
DROP TABLE dashboard_patient_zip_map;

-- Rename the temporary table to the original name
ALTER TABLE dashboard_patient_zip_map_temp RENAME TO dashboard_patient_zip_map;

-- Recreate the indexes
CREATE INDEX idx_patient_zip_map_patient ON dashboard_patient_zip_map(patient_id);
CREATE INDEX idx_patient_zip_map_zip ON dashboard_patient_zip_map(zip_code);

COMMIT;