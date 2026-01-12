-- Add General Phone Inquiries Workflow
-- This workflow is for general phone calls that don't fall under other existing workflows
-- CCs will just add progress notes if needed

-- Insert workflow template
INSERT INTO workflow_templates (template_name)
VALUES ('General Phone Inquiries');

-- Insert the single step for this workflow
INSERT INTO workflow_steps (
    template_id,
    step_order,
    task_name,
    owner,
    deliverable,
    cycle_time
)
SELECT
    template_id,
    1 as step_order,
    'General Phone Inquiries' as task_name,
    'CC' as owner,
    'Progress notes added if needed' as deliverable,
    NULL as cycle_time
FROM workflow_templates
WHERE template_name = 'General Phone Inquiries';
