-- Add next_appointment_date column to patients table
ALTER TABLE patients ADD COLUMN next_appointment_date TEXT DEFAULT NULL;

-- Add next_appointment_date column to patient_panel table
ALTER TABLE patient_panel ADD COLUMN next_appointment_date TEXT DEFAULT NULL;
