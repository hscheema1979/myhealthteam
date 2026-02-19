-- ============================================================================
-- WORKFLOW RESTRUCTURING FOR RESULTS REVIEWER (RR) ROLE
-- ============================================================================
-- Purpose: Restructure LAB and IMAGING workflows to use RR as final step
--
-- Changes:
-- 1. Add RR role (role_id 43) if not exists
-- 2. Update LAB workflows (1-3): Remove step 6, consolidate to 5 steps
-- 3. Update IMAGING workflows (4-6): Remove step 5, consolidate to 4 steps
-- 4. Rename final RR step to "Review Patient Results and inform patient/provider"
--
-- Execution: sqlite3 production.db < src/sql/restructure_workflows_for_rr.sql
-- ============================================================================

BEGIN TRANSACTION;

-- ============================================================================
-- STEP 1: Add RR Role
-- ============================================================================
INSERT OR IGNORE INTO roles (role_id, role_name, description)
VALUES (43, 'RR', 'Results Reviewer - Review lab and imaging results');

-- ============================================================================
-- STEP 2: Delete old RR steps (will be recreated with new structure)
-- ============================================================================

-- LAB ROUTINE (template 1): Delete step 6 (will consolidate to step 5)
DELETE FROM workflow_steps WHERE template_id = 1 AND step_order = 6;

-- LAB URGENT (template 2): Delete step 6 (will consolidate to step 5)
DELETE FROM workflow_steps WHERE template_id = 2 AND step_order = 6;

-- LAB FUTURE (template 3): Delete step 6 (will consolidate to step 5)
DELETE FROM workflow_steps WHERE template_id = 3 AND step_order = 6;

-- IMAGING ROUTINE (template 4): Delete step 5 (will consolidate to step 4)
DELETE FROM workflow_steps WHERE template_id = 4 AND step_order = 5;

-- IMAGING URGENT (template 5): Delete step 5 (will consolidate to step 4)
DELETE FROM workflow_steps WHERE template_id = 5 AND step_order = 5;

-- IMAGING FUTURE (template 6): Delete step 5 (will consolidate to step 4)
DELETE FROM workflow_steps WHERE template_id = 6 AND step_order = 5;

-- ============================================================================
-- STEP 3: Update final RR steps with new names
-- ============================================================================

-- LAB ROUTINE (template 1): Update step 5
UPDATE workflow_steps
SET task_name = 'Review Patient Results and inform patient/provider',
    deliverable = 'RR reviews lab/imaging results and informs patient and provider',
    owner = 'RR'
WHERE template_id = 1 AND step_order = 5;

-- LAB URGENT (template 2): Update step 5
UPDATE workflow_steps
SET task_name = 'Review Patient Results and inform patient/provider',
    deliverable = 'RR reviews lab/imaging results and informs patient and provider',
    owner = 'RR'
WHERE template_id = 2 AND step_order = 5;

-- LAB FUTURE (template 3): Update step 5
UPDATE workflow_steps
SET task_name = 'Review Patient Results and inform patient/provider',
    deliverable = 'RR reviews lab/imaging results and informs patient and provider',
    owner = 'RR'
WHERE template_id = 3 AND step_order = 5;

-- IMAGING ROUTINE (template 4): Update step 4
UPDATE workflow_steps
SET task_name = 'Review Patient Results and inform patient/provider',
    deliverable = 'RR reviews lab/imaging results and informs patient and provider',
    owner = 'RR'
WHERE template_id = 4 AND step_order = 4;

-- IMAGING URGENT (template 5): Update step 4
UPDATE workflow_steps
SET task_name = 'Review Patient Results and inform patient/provider',
    deliverable = 'RR reviews lab/imaging results and informs patient and provider',
    owner = 'RR'
WHERE template_id = 5 AND step_order = 4;

-- IMAGING FUTURE (template 6): Update step 4
UPDATE workflow_steps
SET task_name = 'Review Patient Results and inform patient/provider',
    deliverable = 'RR reviews lab/imaging results and informs patient and provider',
    owner = 'RR'
WHERE template_id = 6 AND step_order = 4;

-- ============================================================================
-- STEP 4: Update step 4 for LAB workflows to reflect CC confirmation
-- ============================================================================

-- LAB ROUTINE (template 1): Update step 4
UPDATE workflow_steps
SET task_name = 'Care Coordinator confirms results received',
    deliverable = 'CC confirms lab results were received and ready for RR review',
    owner = 'CC'
WHERE template_id = 1 AND step_order = 4;

-- LAB URGENT (template 2): Update step 4
UPDATE workflow_steps
SET task_name = 'Care Coordinator confirms results received',
    deliverable = 'CC confirms lab results were received and ready for RR review',
    owner = 'CC'
WHERE template_id = 2 AND step_order = 4;

-- LAB FUTURE (template 3): Update step 4
UPDATE workflow_steps
SET task_name = 'Care Coordinator confirms results received',
    deliverable = 'CC confirms lab results were received and ready for RR review',
    owner = 'CC'
WHERE template_id = 3 AND step_order = 4;

-- ============================================================================
-- STEP 5: Update step 3 for IMAGING workflows to reflect CC confirmation
-- ============================================================================

-- IMAGING ROUTINE (template 4): Update step 3
UPDATE workflow_steps
SET task_name = 'Care Coordinator confirms results received',
    deliverable = 'CC confirms imaging results were received and ready for RR review',
    owner = 'CC'
WHERE template_id = 4 AND step_order = 3;

-- IMAGING URGENT (template 5): Update step 3
UPDATE workflow_steps
SET task_name = 'Care Coordinator confirms results received',
    deliverable = 'CC confirms imaging results were received and ready for RR review',
    owner = 'CC'
WHERE template_id = 5 AND step_order = 3;

-- IMAGING FUTURE (template 6): Update step 3
UPDATE workflow_steps
SET task_name = 'Care Coordinator confirms results received',
    deliverable = 'CC confirms imaging results were received and ready for RR review',
    owner = 'CC'
WHERE template_id = 6 AND step_order = 3;

-- ============================================================================
-- STEP 6: Remove "Alert CM" steps (no longer needed)
-- ============================================================================

-- LAB ROUTINE (template 1): Delete old "Alert CM of received results" step
DELETE FROM workflow_steps
WHERE template_id = 1 AND task_name LIKE '%Alert CM of received results%';

-- LAB URGENT (template 2): Delete old "Alert CM of received results" step
DELETE FROM workflow_steps
WHERE template_id = 2 AND task_name LIKE '%Alert CM of received results%';

-- LAB FUTURE (template 3): Delete old "Alert CM of received results" step
DELETE FROM workflow_steps
WHERE template_id = 3 AND task_name LIKE '%Alert CM of received results%';

-- IMAGING ROUTINE (template 4): Delete old "Alert CM of received results" step
DELETE FROM workflow_steps
WHERE template_id = 4 AND task_name LIKE '%Alert CM of received results%';

-- IMAGING URGENT (template 5): Delete old "Alert CM of received results" step
DELETE FROM workflow_steps
WHERE template_id = 5 AND task_name LIKE '%Alert CM of received results%';

-- IMAGING FUTURE (template 6): Delete old "Alert CM of received results" step
DELETE FROM workflow_steps
WHERE template_id = 6 AND task_name LIKE '%Alert CM of received results%';

-- ============================================================================
-- STEP 7: Reorder remaining steps for each workflow
-- ============================================================================

-- LAB workflows (1-3): Steps should be 1-5 after deletions
-- Update step_order to fill gaps
WITH ordered AS (
  SELECT step_id,
         ROW_NUMBER() OVER (PARTITION BY template_id ORDER BY step_order) as new_order
  FROM workflow_steps
  WHERE template_id IN (1, 2, 3)
)
UPDATE workflow_steps
SET step_order = (SELECT new_order FROM ordered WHERE ordered.step_id = workflow_steps.step_id)
WHERE template_id IN (1, 2, 3);

-- IMAGING workflows (4-6): Steps should be 1-4 after deletions
WITH ordered AS (
  SELECT step_id,
         ROW_NUMBER() OVER (PARTITION BY template_id ORDER BY step_order) as new_order
  FROM workflow_steps
  WHERE template_id IN (4, 5, 6)
)
UPDATE workflow_steps
SET step_order = (SELECT new_order FROM ordered WHERE ordered.step_id = workflow_steps.step_id)
WHERE template_id IN (4, 5, 6);

-- ============================================================================
-- STEP 8: Update active workflow instances
-- ============================================================================

-- For LAB workflows (1-3): If current_step > 5, set to 5
UPDATE workflow_instances
SET current_step = 5,
    current_owner_role = 'RR'
WHERE template_id IN (1, 2, 3)
  AND current_step > 5
  AND workflow_status = 'Active';

-- For IMAGING workflows (4-6): If current_step > 4, set to 4
UPDATE workflow_instances
SET current_step = 4,
    current_owner_role = 'RR'
WHERE template_id IN (4, 5, 6)
  AND current_step > 4
  AND workflow_status = 'Active';

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify RR role exists
SELECT '=== RR Role Verification ===' as section;
SELECT role_id, role_name, description
FROM roles
WHERE role_id = 43;

-- Verify LAB workflow structure (5 steps each)
SELECT '=== LAB Workflows (should have 5 steps) ===' as section;
SELECT
    wt.template_name,
    ws.step_order,
    ws.task_name,
    ws.owner,
    ws.deliverable
FROM workflow_steps ws
JOIN workflow_templates wt ON ws.template_id = wt.template_id
WHERE ws.template_id IN (1, 2, 3)
ORDER BY wt.template_id, ws.step_order;

-- Verify IMAGING workflow structure (4 steps each)
SELECT '=== IMAGING Workflows (should have 4 steps) ===' as section;
SELECT
    wt.template_name,
    ws.step_order,
    ws.task_name,
    ws.owner,
    ws.deliverable
FROM workflow_steps ws
JOIN workflow_templates wt ON ws.template_id = wt.template_id
WHERE ws.template_id IN (4, 5, 6)
ORDER BY wt.template_id, ws.step_order;

-- Expected final structure:
--
-- LAB ROUTINE (5 steps):
--   1: Send lab order, confirm receipt (CC)
--   2: Confirm labs were collected/drawn (CC)
--   3: Confirm received results (CC)
--   4: Care Coordinator confirms results received (CC)
--   5: Review Patient Results and inform patient/provider (RR) ← COMPLETES WORKFLOW
--
-- IMAGING ROUTINE (4 steps):
--   1: Send imaging order, confirm receipt (CC)
--   2: Confirm received results (CC)
--   3: Care Coordinator confirms results received (CC)
--   4: Review Patient Results and inform patient/provider (RR) ← COMPLETES WORKFLOW
