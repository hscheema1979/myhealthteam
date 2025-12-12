-- =================================================================================
-- Unmapped Staff Codes Preservation Table
-- =================================================================================
-- Purpose: Store staff codes that cannot be mapped to users for future correction
-- These codes are found in CSV files but don't have corresponding entries in
-- staff_code_mapping table. This allows us to track them and update mappings
-- when additional staff information becomes available.

CREATE TABLE IF NOT EXISTS unmapped_staff_codes (
    staff_code TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    staff_type TEXT CHECK (staff_type IN ('COORDINATOR', 'PROVIDER')) NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,
    task_count INTEGER DEFAULT 0,
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_unmapped_staff_type
ON unmapped_staff_codes(staff_type);

CREATE INDEX IF NOT EXISTS idx_unmapped_source_file
ON unmapped_staff_codes(source_file);

CREATE INDEX IF NOT EXISTS idx_unmapped_last_seen
ON unmapped_staff_codes(last_seen);

-- View for easy analysis of unmapped codes
DROP VIEW IF EXISTS v_unmapped_staff_summary;
CREATE VIEW v_unmapped_staff_summary AS
SELECT
    staff_code,
    staff_type,
    source_file,
    SUM(occurrence_count) as total_occurrences,
    MIN(first_seen) as first_seen_date,
    MAX(last_seen) as last_seen_date,
    SUM(task_count) as total_tasks,
    notes
FROM unmapped_staff_codes
GROUP BY staff_code, staff_type;

-- Sample query to identify high-priority unmapped codes
-- (those with many tasks that need mapping)
/*
SELECT
    staff_code,
    staff_type,
    SUM(task_count) as task_count,
    MAX(last_seen) as most_recent
FROM unmapped_staff_codes
WHERE staff_type = 'COORDINATOR'
GROUP BY staff_code
ORDER BY task_count DESC
LIMIT 10;
*/

-- Example of how to move a code from unmapped to mapped when you get new info:
/*
-- 1. Insert into staff_code_mapping
INSERT INTO staff_code_mapping (staff_code, user_id, mapping_type, confidence_level, notes)
VALUES ('ChaZu000', 25, 'COORDINATOR', 'HIGH', 'New hire Charise Zuniga');

-- 2. Remove from unmapped table
DELETE FROM unmapped_staff_codes
WHERE staff_code = 'ChaZu000' AND staff_type = 'COORDINATOR';

-- 3. Re-run transform to pickup the new mapping
-- python transform_production_data_v3_fixed.py
*/
```

---
