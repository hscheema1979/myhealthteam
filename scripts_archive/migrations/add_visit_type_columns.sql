-- Migration: Add visit type and billing information columns to onboarding_patients table
-- Date: 2024-01-XX
-- Purpose: Support home visit vs telehealth visit selection with billing defaults

-- Add visit_type column (Home Visit or Telehealth Visit)
ALTER TABLE onboarding_patients ADD COLUMN visit_type TEXT DEFAULT 'Home Visit';

-- Add billing_code column for visit billing
ALTER TABLE onboarding_patients ADD COLUMN billing_code TEXT DEFAULT '99345';

-- Add duration_minutes column for visit duration
ALTER TABLE onboarding_patients ADD COLUMN duration_minutes INTEGER DEFAULT 45;

-- Update existing records to have default values
UPDATE onboarding_patients 
SET visit_type = 'Home Visit', 
    billing_code = '99345', 
    duration_minutes = 45 
WHERE visit_type IS NULL OR billing_code IS NULL OR duration_minutes IS NULL;