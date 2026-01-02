-- Populate workflow_templates and workflow_steps tables from Workflow Template - Template.csv
-- Excludes the example XYZ workflow
-- 1. Opening Encounter workflow (template_id 15)
INSERT INTO workflow_templates (template_name)
VALUES ('Opening Encounter');
-- Steps for Opening Encounter
INSERT INTO workflow_steps (
        template_id,
        step_order,
        task_name,
        owner,
        deliverable,
        cycle_time
    )
VALUES (
        15,
        1,
        'Start Health Management Encounter',
        'Care Coordinator',
        NULL,
        NULL
    );
-- 2. Medication Reconciliation workflow (template_id 16)
INSERT INTO workflow_templates (template_name)
VALUES ('Medication Reconciliation');
-- Steps for Medication Reconciliation
INSERT INTO workflow_steps (
        template_id,
        step_order,
        task_name,
        owner,
        deliverable,
        cycle_time
    )
VALUES (
        16,
        1,
        'Check medication prescribed by other specialists from previous month, then save and reconcile',
        'Care Coordinator',
        NULL,
        NULL
    ),
    (
        16,
        2,
        'Document reconciled medications',
        'Care Coordinator',
        NULL,
        NULL
    ),
    (
        16,
        3,
        'Number of Active medications, 1 count for same meds with different dosage',
        'Care Coordinator',
        NULL,
        NULL
    );
-- 3. Closing caregap workflow (template_id 17)
INSERT INTO workflow_templates (template_name)
VALUES ('Closing caregap');
-- Steps for Closing caregap
INSERT INTO workflow_steps (
        template_id,
        step_order,
        task_name,
        owner,
        deliverable,
        cycle_time
    )
VALUES (
        17,
        1,
        'Check for any pending tasks',
        'Care Coordinator',
        NULL,
        NULL
    );
-- 4. Closing Encounters workflow (template_id 18)
INSERT INTO workflow_templates (template_name)
VALUES ('Closing Encounters');
-- Steps for Closing Encounters
INSERT INTO workflow_steps (
        template_id,
        step_order,
        task_name,
        owner,
        deliverable,
        cycle_time
    )
VALUES (
        18,
        1,
        'Check Health Management Encounter for completeness',
        'Care Coordinator',
        NULL,
        NULL
    ),
    (
        18,
        2,
        'Total the management minutes and add in Plan',
        'Care Coordinator',
        NULL,
        NULL
    );
-- 5. Signing of documents workflow (template_id 19)
INSERT INTO workflow_templates (template_name)
VALUES ('Signing of documents');
-- Steps for Signing of documents
INSERT INTO workflow_steps (
        template_id,
        step_order,
        task_name,
        owner,
        deliverable,
        cycle_time
    )
VALUES (
        19,
        1,
        'Check details of the document *Split documents if needed',
        'Care Coordinator',
        NULL,
        NULL
    ),
    (
        19,
        2,
        'Sign the document',
        'Care Coordinator',
        NULL,
        NULL
    ),
    (
        19,
        3,
        'Upload document to chart',
        'Care Coordinator',
        NULL,
        NULL
    ),
    (
        19,
        4,
        'Send the signed document to the facility',
        'Care Coordinator',
        NULL,
        NULL
    );
-- 6. Phone review request workflow (template_id 20)
INSERT INTO workflow_templates (template_name)
VALUES ('Phone review request');
-- Steps for Phone review request
INSERT INTO workflow_steps (
        template_id,
        step_order,
        task_name,
        owner,
        deliverable,
        cycle_time
    )
VALUES (
        20,
        1,
        'Check chart to verify the need for an appointment',
        'Care Coordinator',
        NULL,
        NULL
    ),
    (
        20,
        2,
        'Report request to Acutes google chat',
        'Care Coordinator',
        'Appointment request to CM',
        NULL
    ),
    (
        20,
        3,
        'Call patient to inform of appointment schedule',
        'Care Coordinator',
        NULL,
        NULL
    );