-- Migration script: Add 'goc' column to 'patients' table if it does not exist
-- Safe for production: will not overwrite or drop any data
-- Usage: sqlite3 production.db ".read scripts/add_goc_column_to_patients.sql"
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;
-- SQLite does not support IF NOT EXISTS for ALTER TABLE ADD COLUMN, so this will error if the column exists.
-- Only run this ONCE, or check schema before running.
ALTER TABLE patients
ADD COLUMN goc TEXT;
COMMIT;
PRAGMA foreign_keys = on;