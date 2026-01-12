-- Fix Workflow Template Spelling and Formatting Issues
-- Date: 2026-01-08

-- Issue 1: Template ID 18 - "Closing caregap" should be "Closing Care Gap"
UPDATE workflow_templates
SET template_name = 'Closing Care Gap'
WHERE template_id = 18;

-- Issue 2: Template ID 19 - "Closing Encoungters" is misspelled, should be "Closing Encounters"
UPDATE workflow_templates
SET template_name = 'Closing Encounters'
WHERE template_id = 19;

-- Verify the changes
SELECT template_id, template_name
FROM workflow_templates
WHERE template_id IN (18, 19, 22)
ORDER BY template_id;
