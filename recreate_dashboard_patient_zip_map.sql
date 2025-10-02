-- Recreate dashboard_patient_zip_map table with proper foreign key constraints
PRAGMA foreign_keys = OFF;

-- Backup existing data
CREATE TEMPORARY TABLE dashboard_patient_zip_map_backup AS 
SELECT * FROM dashboard_patient_zip_map;

-- Drop the existing table
DROP TABLE IF EXISTS dashboard_patient_zip_map;

-- Recreate the table with proper foreign key constraint
CREATE TABLE dashboard_patient_zip_map (
    map_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    zip_code TEXT NOT NULL,
    city TEXT,
    state TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

-- Recreate indexes
CREATE INDEX idx_patient_zip_map_patient ON dashboard_patient_zip_map(patient_id);
CREATE INDEX idx_patient_zip_map_zip ON dashboard_patient_zip_map(zip_code);

-- Restore data (only valid records)
INSERT INTO dashboard_patient_zip_map (map_id, patient_id, zip_code, city, state, created_date, updated_date)
SELECT b.map_id, b.patient_id, b.zip_code, b.city, b.state, b.created_date, b.updated_date
FROM dashboard_patient_zip_map_backup b
WHERE b.patient_id IN (SELECT patient_id FROM patients);

-- Clean up
DROP TABLE dashboard_patient_zip_map_backup;

PRAGMA foreign_keys = ON;