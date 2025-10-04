-- Update annual_well_visit from boolean to date field in production database
-- This script converts the annual_well_visit field from BOOLEAN to DATE

-- 1. Update onboarding_patients table
-- First, add a new temporary column
ALTER TABLE onboarding_patients ADD COLUMN annual_well_visit_date DATE;

-- Copy existing boolean data (if true, set to null since we don't have actual dates)
-- We'll leave it null for now and let users input actual dates
UPDATE onboarding_patients 
SET annual_well_visit_date = NULL;

-- Drop the old boolean column
ALTER TABLE onboarding_patients DROP COLUMN annual_well_visit;

-- Rename the new column to the original name
ALTER TABLE onboarding_patients RENAME COLUMN annual_well_visit_date TO annual_well_visit;