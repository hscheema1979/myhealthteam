-- Migration: Add location_type and patient_type columns to existing monthly task tables
-- These columns are needed for the billing workflow and task review functionality

-- Add to provider_tasks tables (2025-01 through 2026-12)
ALTER TABLE provider_tasks_2025_01 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_01 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_02 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_02 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_03 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_03 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_04 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_04 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_05 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_05 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_06 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_06 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_07 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_07 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_08 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_08 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_09 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_09 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_10 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_10 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_11 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_11 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2025_12 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2025_12 ADD COLUMN patient_type TEXT;

ALTER TABLE provider_tasks_2026_01 ADD COLUMN location_type TEXT;
ALTER TABLE provider_tasks_2026_01 ADD COLUMN patient_type TEXT;

-- 2026-02 should already have it from manual fix, but include for safety
-- ALTER TABLE provider_tasks_2026_02 ADD COLUMN location_type TEXT;
-- ALTER TABLE provider_tasks_2026_02 ADD COLUMN patient_type TEXT;

-- Add to coordinator_tasks tables (2025-01 through 2026-12)
ALTER TABLE coordinator_tasks_2025_01 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_01 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_02 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_02 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_03 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_03 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_04 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_04 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_05 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_05 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_06 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_06 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_07 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_07 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_08 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_08 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_09 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_09 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_10 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_10 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_11 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_11 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2025_12 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2025_12 ADD COLUMN patient_type TEXT;

ALTER TABLE coordinator_tasks_2026_01 ADD COLUMN location_type TEXT;
ALTER TABLE coordinator_tasks_2026_01 ADD COLUMN patient_type TEXT;

-- 2026-02 should already have it from manual fix, but include for safety
-- ALTER TABLE coordinator_tasks_2026_02 ADD COLUMN location_type TEXT;
-- ALTER TABLE coordinator_tasks_2026_02 ADD COLUMN patient_type TEXT;
