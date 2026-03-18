-- ============================================================================
-- Add 7 New Columns to Patient Panel & Patients Tables
--
-- Feature Request: "7 Columns: DME, eTV Panel, XRx, CareTeam, Folder, AWV, DD"
-- Need By: 3/18
-- All columns are free text (TEXT) fields.
--
-- Columns:
-- 1. dme - TEXT: DME (Durable Medical Equipment)
-- 2. etv_panel - TEXT: eTV Panel
-- 3. xrx - TEXT: XRx
-- 4. care_team - TEXT: CareTeam
-- 5. folder - TEXT: Folder
-- 6. awv - TEXT: AWV (Annual Wellness Visit)
-- 7. dd - TEXT: DD
-- ============================================================================

-- Add columns to patients table (source of truth)
ALTER TABLE patients ADD COLUMN dme TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN etv_panel TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN xrx TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN care_team TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN folder TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN awv TEXT DEFAULT NULL;
ALTER TABLE patients ADD COLUMN dd TEXT DEFAULT NULL;

-- Add columns to patient_panel table (display/editing view)
ALTER TABLE patient_panel ADD COLUMN dme TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN etv_panel TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN xrx TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN care_team TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN folder TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN awv TEXT DEFAULT NULL;
ALTER TABLE patient_panel ADD COLUMN dd TEXT DEFAULT NULL;

-- Verification queries (run manually)
-- PRAGMA table_info(patients);
-- PRAGMA table_info(patient_panel);
