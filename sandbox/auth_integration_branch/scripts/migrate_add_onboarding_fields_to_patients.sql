-- Migration: Add onboarding-specific fields to patients table
ALTER TABLE patients
ADD COLUMN stage1_complete INTEGER DEFAULT 0;
ALTER TABLE patients
ADD COLUMN stage2_complete INTEGER DEFAULT 0;
ALTER TABLE patients
ADD COLUMN initial_tv_completed INTEGER DEFAULT 0;
ALTER TABLE patients
ADD COLUMN initial_tv_completed_date TEXT;
ALTER TABLE patients
ADD COLUMN initial_tv_notes TEXT;
-- Add more onboarding-specific fields here as needed