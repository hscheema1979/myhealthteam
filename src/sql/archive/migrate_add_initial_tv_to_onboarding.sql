-- Migration: Add Initial TV fields to onboarding_patients table
-- This fixes the error: no column initial_tv_completed or initial_tv_date

-- Add initial_tv_completed column (boolean/integer)
ALTER TABLE onboarding_patients
ADD COLUMN initial_tv_completed INTEGER DEFAULT 0;

-- Add initial_tv_completed_date column (text/date)
ALTER TABLE onboarding_patients
ADD COLUMN initial_tv_completed_date TEXT;

-- Add initial_tv_notes column for completeness (referenced in other parts of the system)
ALTER TABLE onboarding_patients
ADD COLUMN initial_tv_notes TEXT;

-- Add initial_tv_provider column for completeness (referenced in other parts of the system)
ALTER TABLE onboarding_patients
ADD COLUMN initial_tv_provider TEXT;