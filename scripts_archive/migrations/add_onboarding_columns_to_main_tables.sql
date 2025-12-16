-- Migration: Add onboarding columns to patient_panel and patients tables
-- Date: 2025-01-25
-- Purpose: Sync onboarding workflow data across all patient tables

-- Add onboarding columns to patient_panel table
ALTER TABLE patient_panel ADD COLUMN eligibility_status TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN eligibility_notes TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN eligibility_verified INTEGER DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN emed_chart_created INTEGER DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN chart_id TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN facility_confirmed INTEGER DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN chart_notes TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN intake_call_completed INTEGER DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN intake_notes TEXT DEFAULT NULL;

-- Add onboarding columns to patients table
ALTER TABLE patients ADD COLUMN eligibility_status TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN eligibility_notes TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN eligibility_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN emed_chart_created BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN chart_id TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN facility_confirmed BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN chart_notes TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN intake_call_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE patients ADD COLUMN intake_notes TEXT DEFAULT NULL;

-- Verify the columns were added successfully
.print "Verifying patient_panel table columns:"
PRAGMA table_info(patient_panel);

.print "Verifying patients table columns:"
PRAGMA table_info(patients);

.print "Migration completed successfully!"