-- Add provider_name and coordinator_name columns to existing task tables
-- This allows the updated transform script to populate names during import
-- Add provider_name to all existing provider_tasks tables
-- Find all provider_tasks tables
SELECT name
FROM sqlite_master
WHERE type = 'table'
    AND name LIKE 'provider_tasks_%';
-- For each provider_tasks table, add the provider_name column if it doesn't exist
-- We'll do this with a SQL script that can be executed
-- Add coordinator_name to all existing coordinator_tasks tables  
SELECT name
FROM sqlite_master
WHERE type = 'table'
    AND name LIKE 'coordinator_tasks_%';
-- For each coordinator_tasks table, add the coordinator_name column if it doesn't exist