-- Migration: Add missing columns to onboarding_patients table
-- Date: 2025-01-27
-- Purpose: Add all missing columns referenced in onboarding_dashboard.py

-- Add chart creation related columns (Stage 3)
ALTER TABLE onboarding_patients ADD COLUMN emed_chart_created BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN chart_id TEXT;
ALTER TABLE onboarding_patients ADD COLUMN facility_confirmed BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN chart_notes TEXT;

-- Add intake processing related columns (Stage 4)
ALTER TABLE onboarding_patients ADD COLUMN intake_call_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE onboarding_patients ADD COLUMN intake_notes TEXT;

-- Verify the columns were added successfully
.schema onboarding_patients