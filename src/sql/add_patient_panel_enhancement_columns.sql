-- ============================================================================
-- Add Patient Panel & HH Column Enhancements
--
-- This script adds new columns to the patients and patient_panel tables
-- to support enhanced patient tracking and management features.
--
-- Columns to add:
-- 1. transportation_status - TEXT: [Available / Unavailable]
-- 2. hh_status - TEXT: [Active / Discharged]
-- 3. medlist_date - TEXT: Last updated timestamp for medication list
-- 4. smartph_active - INTEGER: Boolean flag [0 = No, 1 = Yes]
-- 5. language - TEXT: Patient's preferred language
-- 6. rpm_team - TEXT: Category tags [BP, DM, Obese]
-- 7. bh_team - INTEGER: Boolean flag [0 = No, 1 = Yes]
-- 8. cog_team - INTEGER: Boolean flag [0 = No, 1 = Yes]
-- 9. pcp_name - TEXT: Primary Care Physician name
-- 10. consents - TEXT: Consent form status/link
-- ============================================================================

-- Add columns to patients table (source of truth)
ALTER TABLE patients ADD COLUMN transportation_status TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN hh_status TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN medlist_date TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN smartph_active INTEGER DEFAULT 0;
ALTER TABLE patients ADD COLUMN language TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN rpm_team TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN bh_team INTEGER DEFAULT 0;
ALTER TABLE patients ADD COLUMN cog_team INTEGER DEFAULT 0;
ALTER TABLE patients ADD COLUMN pcp_name TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN consents TEXT DEFAULT NULL;

-- Add columns to patient_panel table (display/editing view)
ALTER TABLE patient_panel ADD COLUMN transportation_status TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN hh_status TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN medlist_date TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN smartph_active INTEGER DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN language TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN rpm_team TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN bh_team INTEGER DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN cog_team INTEGER DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN pcp_name TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN consents TEXT DEFAULT NULL;

-- Create indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_patients_hh_status ON patients(hh_status);
CREATE INDEX IF NOT EXISTS idx_patients_smartph_active ON patients(smartph_active);
CREATE INDEX IF NOT EXISTS idx_patients_bh_team ON patients(bh_team);
CREATE INDEX IF NOT EXISTS idx_patients_cog_team ON patients(cog_team);
CREATE INDEX IF NOT EXISTS idx_patients_rpm_team ON patients(rpm_team);

CREATE INDEX IF NOT EXISTS idx_patient_panel_hh_status ON patient_panel(hh_status);
CREATE INDEX IF NOT EXISTS idx_patient_panel_smartph_active ON patient_panel(smartph_active);
CREATE INDEX IF NOT EXISTS idx_patient_panel_bh_team ON patient_panel(bh_team);
CREATE INDEX IF NOT EXISTS idx_patient_panel_cog_team ON patient_panel(cog_team);
CREATE INDEX IF NOT EXISTS idx_patient_panel_rpm_team ON patient_panel(rpm_team);

-- Verification queries (commented out - run manually to verify)
-- PRAGMA table_info(patients);
-- PRAGMA table_info(patient_panel);
-- SELECT patient_id, transportation_status, hh_status, medlist_date, smartph_active,
--        language, rpm_team, bh_team, cog_team, pcp_name, consents
-- FROM patients LIMIT 5;
