-- Migration: Add Initial TV fields to patients table if not present
ALTER TABLE patients
ADD COLUMN initial_tv_completed_date TEXT;
ALTER TABLE patients
ADD COLUMN initial_tv_notes TEXT;
ALTER TABLE patients
ADD COLUMN initial_tv_provider TEXT;