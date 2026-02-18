-- Create deleted_provider_tasks table for soft delete functionality
-- This table stores deleted provider tasks that can be restored if needed

CREATE TABLE IF NOT EXISTS deleted_provider_tasks (
    deleted_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_task_id INTEGER NOT NULL,
    original_table_name TEXT NOT NULL,
    provider_id INTEGER NOT NULL,
    provider_name TEXT,
    patient_id TEXT NOT NULL,
    patient_name TEXT,
    task_date DATE NOT NULL,
    task_description TEXT,
    notes TEXT,
    minutes_of_service INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    deleted_by_user_id INTEGER,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restored_at TIMESTAMP,
    restored_by_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_deleted_provider_id ON deleted_provider_tasks(provider_id);
CREATE INDEX IF NOT EXISTS idx_deleted_patient_id ON deleted_provider_tasks(patient_id);
CREATE INDEX IF NOT EXISTS idx_deleted_date ON deleted_provider_tasks(deleted_at);
CREATE INDEX IF NOT EXISTS idx_deleted_original_table ON deleted_provider_tasks(original_table_name);
