-- Fix Orphaned Patient IDs Script
-- Purpose: Map truncated/simplified patient_ids to their full names in patients table
-- Issue: Task tables have simplified names, patients table has full names

-- ============================================================================
-- ANALYSIS: Find mapping patterns for orphaned records
-- ============================================================================

-- Check top orphaned records and their potential matches
SELECT 'ORPHANED RECORD ANALYSIS' as analysis_step;

-- Sample orphaned records with potential matches
WITH orphaned_samples AS (
    SELECT ct.patient_id as orphaned_id
    FROM coordinator_tasks ct 
    LEFT JOIN patients p ON ct.patient_id = p.patient_id 
    WHERE p.patient_id IS NULL 
      AND ct.patient_id NOT LIKE 'TEST_%'
    GROUP BY ct.patient_id 
    ORDER BY COUNT(*) DESC 
    LIMIT 20
),
potential_matches AS (
    SELECT 
        o.orphaned_id,
        p.patient_id as full_id,
        -- Extract last name and first name from both
        SUBSTR(o.orphaned_id, 1, INSTR(o.orphaned_id, ' ') - 1) as orphaned_lastname,
        SUBSTR(p.patient_id, 1, INSTR(p.patient_id, ' ') - 1) as full_lastname,
        -- Extract date portion (last 10 characters)
        SUBSTR(o.orphaned_id, -10) as orphaned_date,
        SUBSTR(p.patient_id, -10) as full_date
    FROM orphaned_samples o
    CROSS JOIN patients p
    WHERE SUBSTR(o.orphaned_id, -10) = SUBSTR(p.patient_id, -10)  -- Same birth date
      AND (
          -- Last name contains orphaned last name
          INSTR(SUBSTR(p.patient_id, 1, INSTR(p.patient_id, ' ') - 1), 
                SUBSTR(o.orphaned_id, 1, INSTR(o.orphaned_id, ' ') - 1)) > 0
          OR
          -- Orphaned last name contains full last name  
          INSTR(SUBSTR(o.orphaned_id, 1, INSTR(o.orphaned_id, ' ') - 1),
                SUBSTR(p.patient_id, 1, INSTR(p.patient_id, ' ') - 1)) > 0
      )
)
SELECT orphaned_id, full_id, 'POTENTIAL_MATCH' as match_type
FROM potential_matches
ORDER BY orphaned_id
LIMIT 20;

-- ============================================================================
-- SOLUTION 1: Create mapping table for confirmed matches
-- ============================================================================

-- Create temporary mapping table
DROP TABLE IF EXISTS patient_id_mapping;
CREATE TEMPORARY TABLE patient_id_mapping (
    orphaned_id TEXT,
    correct_id TEXT,
    match_confidence TEXT
);

-- Insert high-confidence matches (same birth date + name similarity)
INSERT INTO patient_id_mapping (orphaned_id, correct_id, match_confidence)
WITH orphaned_records AS (
    SELECT DISTINCT ct.patient_id as orphaned_id
    FROM coordinator_tasks ct 
    LEFT JOIN patients p ON ct.patient_id = p.patient_id 
    WHERE p.patient_id IS NULL 
      AND ct.patient_id NOT LIKE 'TEST_%'
),
date_matches AS (
    SELECT 
        o.orphaned_id,
        p.patient_id as correct_id,
        SUBSTR(o.orphaned_id, -10) as orphaned_date,
        SUBSTR(p.patient_id, -10) as correct_date
    FROM orphaned_records o
    CROSS JOIN patients p
    WHERE SUBSTR(o.orphaned_id, -10) = SUBSTR(p.patient_id, -10)  -- Same birth date
),
name_similarity AS (
    SELECT 
        orphaned_id,
        correct_id,
        -- Extract first and last names
        SUBSTR(orphaned_id, 1, INSTR(orphaned_id, ' ') - 1) as orphaned_lastname,
        SUBSTR(correct_id, 1, INSTR(correct_id, ' ') - 1) as correct_lastname,
        CASE 
            WHEN INSTR(LOWER(correct_id), LOWER(orphaned_id)) > 0 THEN 'HIGH'
            WHEN INSTR(LOWER(orphaned_id), LOWER(SUBSTR(correct_id, 1, INSTR(correct_id, ' ') - 1))) > 0 THEN 'MEDIUM'
            ELSE 'LOW'
        END as confidence
    FROM date_matches
)
SELECT orphaned_id, correct_id, confidence
FROM name_similarity 
WHERE confidence IN ('HIGH', 'MEDIUM')
ORDER BY orphaned_id, confidence DESC;

-- Show mapping results
SELECT 'MAPPING RESULTS' as step;
SELECT match_confidence, COUNT(*) as mapping_count 
FROM patient_id_mapping 
GROUP BY match_confidence;

SELECT 'SAMPLE MAPPINGS' as step;
SELECT orphaned_id, correct_id, match_confidence 
FROM patient_id_mapping 
LIMIT 10;

-- ============================================================================
-- SOLUTION 2: Update coordinator_tasks with mapped patient_ids
-- ============================================================================

SELECT 'UPDATING COORDINATOR_TASKS' as step;

-- Update coordinator_tasks using the mapping
UPDATE coordinator_tasks 
SET patient_id = (
    SELECT correct_id 
    FROM patient_id_mapping 
    WHERE patient_id_mapping.orphaned_id = coordinator_tasks.patient_id
)
WHERE patient_id IN (
    SELECT orphaned_id 
    FROM patient_id_mapping 
    WHERE match_confidence = 'HIGH'
);

-- Show update results
SELECT 'COORDINATOR_TASKS UPDATE RESULTS' as step;
SELECT 'Updated records' as type, changes() as count;

-- ============================================================================
-- SOLUTION 3: Update provider_tasks with mapped patient_ids  
-- ============================================================================

SELECT 'UPDATING PROVIDER_TASKS' as step;

-- Update provider_tasks using the mapping
UPDATE provider_tasks 
SET patient_id = (
    SELECT correct_id 
    FROM patient_id_mapping 
    WHERE patient_id_mapping.orphaned_id = provider_tasks.patient_id
)
WHERE patient_id IN (
    SELECT orphaned_id 
    FROM patient_id_mapping 
    WHERE match_confidence = 'HIGH'
);

-- Show update results  
SELECT 'PROVIDER_TASKS UPDATE RESULTS' as step;
SELECT 'Updated records' as type, changes() as count;

-- ============================================================================
-- VALIDATION: Check remaining orphaned records
-- ============================================================================

SELECT 'POST-MAPPING VALIDATION' as step;

-- Count remaining orphaned records
SELECT 'coordinator_tasks remaining orphaned' as table_name, COUNT(*) as orphaned_count
FROM coordinator_tasks ct
LEFT JOIN patients p ON ct.patient_id = p.patient_id
WHERE p.patient_id IS NULL AND ct.patient_id NOT LIKE 'TEST_%';

SELECT 'provider_tasks remaining orphaned' as table_name, COUNT(*) as orphaned_count
FROM provider_tasks pt
LEFT JOIN patients p ON pt.patient_id = p.patient_id
WHERE p.patient_id IS NULL AND pt.patient_id NOT LIKE 'TEST_%';

-- Sample successful matches
SELECT 'SUCCESSFUL MATCHES SAMPLE' as step;
SELECT ct.patient_id, COUNT(*) as task_count
FROM coordinator_tasks ct
JOIN patients p ON ct.patient_id = p.patient_id
GROUP BY ct.patient_id
ORDER BY task_count DESC
LIMIT 5;

SELECT 'ORPHANED MAPPING COMPLETE' as final_status;