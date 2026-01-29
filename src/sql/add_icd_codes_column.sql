-- Add icd_codes and patient_id columns to provider_task_billing_status table
-- Migration script for ICD-10 codes support and patient_id fix

-- Add patient_id column if missing (was omitted from original schema)
ALTER TABLE provider_task_billing_status ADD COLUMN patient_id TEXT;

-- Add icd_codes column to provider_task_billing_status table
ALTER TABLE provider_task_billing_status ADD COLUMN icd_codes TEXT;

-- Populate patient_id from patient_name for existing records
-- Format: 'LASTNAME FIRSTNAME MM/DD/YYYY' -> 'LASTNAME FIRSTNAME YYYY-MM-DD'
UPDATE provider_task_billing_status
SET patient_id = SUBSTR(patient_name, 1, LENGTH(patient_name) - 10) ||
                 SUBSTR(patient_name, LENGTH(patient_name) - 3, 4) || '-' ||
                 SUBSTR(patient_name, LENGTH(patient_name) - 9, 2) || '-' ||
                 SUBSTR(patient_name, LENGTH(patient_name) - 6, 2)
WHERE patient_id IS NULL;

-- Update create_weekly_billing_system.sql schema to include icd_codes and patient_id columns
-- (This is for reference - the actual table modification is done via ALTER TABLE above)
