-- SIMPLE FIX: Add missing columns for care provider dashboard
-- The subjective_risk_level column is already TEXT (correct), we just need to add 2 missing columns

-- Add missing columns to patients table
ALTER TABLE patients ADD COLUMN task_date DATE DEFAULT NULL;
ALTER TABLE patients ADD COLUMN goc_value TEXT DEFAULT NULL;

-- Add missing columns to patient_panel table (if it exists)
ALTER TABLE patient_panel ADD COLUMN task_date DATE DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN goc_value TEXT DEFAULT NULL;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patients_task_date ON patients(task_date);
CREATE INDEX IF NOT EXISTS idx_patient_panel_task_date ON patient_panel(task_date);

-- Verification queries
-- SELECT COUNT(*) as total_patients FROM patients;
-- PRAGMA table_info(patients);