-- Add Results Reviewer (RR) Role
-- This role will handle all lab and imaging results review tasks from workflows
-- Replaces CM (Coordinator Manager) for results review workflow steps

-- Add the new role (role_id 43)
INSERT INTO roles (role_id, role_name, description)
VALUES (43, 'RR', 'Results Reviewer - Review lab and imaging results')
ON CONFLICT(role_id) DO UPDATE SET
    description = 'Results Reviewer - Review lab and imaging results';

-- Update workflow steps to assign results review tasks to RR instead of CM
-- This affects LAB ROUTINE, LAB URGENT, LAB FUTURE, IMAGING ROUTINE, IMAGING URGENT templates

-- Update "Alert CP of received results" steps - change owner from CM to RR
UPDATE workflow_steps
SET owner = 'RR'
WHERE owner = 'CM'
  AND (
    task_name LIKE '%Alert CP of received results%'
    OR task_name LIKE '%Assign review results task%'
  );

-- Update "CP reviews results" steps - change owner from CM to RR
UPDATE workflow_steps
SET owner = 'RR'
WHERE owner = 'CM'
  AND task_name LIKE '%CP reviews results%';

-- Verify the changes
SELECT
    wt.template_name,
    ws.step_order,
    ws.task_name,
    ws.owner,
    ws.deliverable
FROM workflow_steps ws
JOIN workflow_templates wt ON ws.template_id = wt.template_id
WHERE ws.owner = 'RR'
ORDER BY wt.template_name, ws.step_order;

-- Expected output should show:
-- LAB ROUTINE - step 5: Alert CP of received results
-- LAB ROUTINE - step 6: CP reviews results
-- LAB URGENT - step 5: Alert CP of received results
-- LAB URGENT - step 6: CP reviews results
-- LAB FUTURE - step 5: Alert CP of received results
-- LAB FUTURE - step 6: CP reviews results
-- IMAGING ROUTINE - step 5: Alert CP of received results
-- IMAGING ROUTINE - step 6: CP reviews results
-- IMAGING URGENT - step 5: Alert CP of received results
-- IMAGING URGENT - step 6: CP reviews results
