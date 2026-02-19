-- Add Patient Assignment History Table
-- This table tracks all coordinator and provider reassignments for audit trail

CREATE TABLE IF NOT EXISTS patient_assignment_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT NOT NULL,
    old_coordinator_id TEXT,
    new_coordinator_id TEXT,
    old_provider_id INTEGER,
    new_provider_id INTEGER,
    changed_by_user_id INTEGER,
    changed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_notes TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (changed_by_user_id) REFERENCES users(user_id)
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_patient_assignment_history_patient
ON patient_assignment_history(patient_id);

CREATE INDEX IF NOT EXISTS idx_patient_assignment_history_date
ON patient_assignment_history(changed_date DESC);

-- Verification
SELECT 'patient_assignment_history table created successfully' as status;
SELECT COUNT(*) as column_count FROM pragma_table_info('patient_assignment_history');
