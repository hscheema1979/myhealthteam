-- Migration script: Add created_at_pst column to all existing coordinator_tasks tables
-- This ensures each entry has a unique timestamp for identification
-- Run this script to add the column to existing monthly tables

-- Add created_at_pst column to all existing coordinator_tasks tables
-- Tables are named coordinator_tasks_YYYY_MM

-- Check each existing table and add the column if it doesn't exist
-- The column will be NULL for existing records, but new records will have PST timestamps

-- 2024 tables (adjust based on your actual existing tables)
ALTER TABLE coordinator_tasks_2024_01 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_02 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_03 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_04 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_05 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_06 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_07 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_08 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_09 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_10 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_11 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2024_12 ADD COLUMN created_at_pst TEXT;

-- 2025 tables
ALTER TABLE coordinator_tasks_2025_01 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_02 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_03 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_04 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_05 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_06 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_07 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_08 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_09 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_10 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_11 ADD COLUMN created_at_pst TEXT;
ALTER TABLE coordinator_tasks_2025_12 ADD COLUMN created_at_pst TEXT;

-- 2026 tables
ALTER TABLE coordinator_tasks_2026_01 ADD COLUMN created_at_pst TEXT;

-- For future months, the ensure_monthly_coordinator_tasks_table() function in database.py
-- will automatically add this column when creating new tables

-- Optional: If you want to backfill timestamps for existing records, you can run:
-- UPDATE coordinator_tasks_YYYY_MM
-- SET created_at_pst = printf('%04d-%02d-%02d %02d:%02d:%02d',
--     CAST(substr(task_date, 1, 4) AS INTEGER),
--     CAST(substr(task_date, 6, 2) AS INTEGER),
--     CAST(substr(task_date, 9, 2) AS INTEGER),
--     12, 0, 0)  -- Default to noon PST as a reasonable default
-- WHERE created_at_pst IS NULL;
