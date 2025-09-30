-- Migration script: Add new columns to 'patients' table if they do not exist
-- Columns: labs, dme, imaging, specialty, med_refill, prior_authorization
-- Usage: sqlite3 production.db ".read scripts/add_patient_columns_labs_dme_etc.sql"
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;
-- SQLite does not support IF NOT EXISTS for ALTER TABLE ADD COLUMN, so this will error if the column exists.
-- Only run this ONCE, or check schema before running.
ALTER TABLE patients
ADD COLUMN labs TEXT;
ALTER TABLE patients
ADD COLUMN dme TEXT;
ALTER TABLE patients
ADD COLUMN imaging TEXT;
ALTER TABLE patients
ADD COLUMN specialty TEXT;
ALTER TABLE patients
ADD COLUMN med_refill TEXT;
ALTER TABLE patients
ADD COLUMN prior_authorization TEXT;
COMMIT;
PRAGMA foreign_keys = on;