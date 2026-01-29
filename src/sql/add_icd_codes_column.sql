-- Add icd_codes column to provider_task_billing_status table
-- Migration script for ICD-10 codes support

-- Add icd_codes column to provider_task_billing_status table
ALTER TABLE provider_task_billing_status ADD COLUMN icd_codes TEXT;

-- Update create_weekly_billing_system.sql schema to include icd_codes column
-- (This is for reference - the actual table modification is done via ALTER TABLE above)
