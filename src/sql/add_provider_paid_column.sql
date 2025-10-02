-- Add provider_paid column to provider_tasks table
ALTER TABLE provider_tasks ADD COLUMN provider_paid INTEGER DEFAULT 0;

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_provider_tasks_provider_paid ON provider_tasks(provider_paid);

-- Verification
SELECT 'Provider Paid Column Added' as description;

-- Show column structure
PRAGMA table_info(provider_tasks);