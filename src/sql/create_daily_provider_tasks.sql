-- Create daily_provider_tasks table to track task descriptions for Primary Care Visits
-- This table focuses on task_description grouped by task_description from task_billing_codes
-- where service_type is 'Primary Care Visit'
DROP TABLE IF EXISTS daily_provider_tasks;
CREATE TABLE IF NOT EXISTS daily_provider_tasks (
    daily_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_description TEXT NOT NULL,
    service_type TEXT DEFAULT 'Primary Care Visit',
    task_count INTEGER DEFAULT 0,
    enabled BOOLEAN DEFAULT 1,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_daily_provider_tasks_description ON daily_provider_tasks(task_description);
-- Populate the table with unique task descriptions from Primary Care Visit service type
INSERT INTO daily_provider_tasks (
        task_description,
        service_type,
        task_count,
        enabled
    )
SELECT DISTINCT tbc.task_description,
    tbc.service_type,
    0 as task_count,
    1 as enabled
FROM task_billing_codes tbc
WHERE tbc.service_type = 'Primary Care Visit'
    AND tbc.task_description IS NOT NULL
    AND tbc.task_description != '';
-- Show the results
SELECT daily_task_id,
    task_description,
    service_type,
    task_count,
    enabled,
    created_date
FROM daily_provider_tasks
ORDER BY task_description;
-- Show count of records inserted
SELECT 'Total Primary Care Visit task descriptions' as description,
    COUNT(*) as count
FROM daily_provider_tasks;