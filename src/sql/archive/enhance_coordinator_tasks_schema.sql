-- Schema Enhancement for coordinator_tasks table
-- Adding missing columns required for differential import
-- Disable foreign key constraints during schema changes
PRAGMA foreign_keys = OFF;
-- Add missing columns to coordinator_tasks table
ALTER TABLE coordinator_tasks
ADD COLUMN IF NOT EXISTS user_id INTEGER;
ALTER TABLE coordinator_tasks
ADD COLUMN IF NOT EXISTS coordinator_name TEXT;
ALTER TABLE coordinator_tasks
ADD COLUMN IF NOT EXISTS source_hash TEXT;
-- Re-enable foreign key constraints
PRAGMA foreign_keys = ON;
-- Verify the changes
-- SELECT sql FROM sqlite_master WHERE type='table' AND name='coordinator_tasks';