-- Add Labs Notes, Imaging Notes, and General Notes columns to patient_panel table
-- Migration script for adding notes fields

-- Add Labs Notes column
ALTER TABLE patient_panel ADD COLUMN labs_notes TEXT;

-- Add Imaging Notes column
ALTER TABLE patient_panel ADD COLUMN imaging_notes TEXT;

-- Add General Notes column
ALTER TABLE patient_panel ADD COLUMN general_notes TEXT;

-- Also add to patients table for consistency
ALTER TABLE patients ADD COLUMN labs_notes TEXT;
ALTER TABLE patients ADD COLUMN imaging_notes TEXT;
ALTER TABLE patients ADD COLUMN general_notes TEXT;
