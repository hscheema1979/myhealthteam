-- Add Nurse POC and Telehealth columns to patients and patient_panel tables
-- Run this on both local and VPS2 databases

-- Add to patients table
ALTER TABLE patients ADD COLUMN nurse_poc_name TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN nurse_phone TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN telehealth_capable TEXT DEFAULT NULL;

-- Add to patient_panel table
ALTER TABLE patient_panel ADD COLUMN nurse_poc_name TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN nurse_phone TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN telehealth_capable TEXT DEFAULT NULL;
