-- Migration: Add intake_notes to onboarding_patients
ALTER TABLE onboarding_patients
ADD COLUMN intake_notes TEXT;