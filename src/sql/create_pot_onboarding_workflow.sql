-- POT Onboarding Workflow Template Implementation
-- Execute these SQL statements to create the onboarding workflow system
-- 1. Create the POT_PATIENT_ONBOARDING workflow template
INSERT INTO workflow_templates (template_name)
VALUES ('POT_PATIENT_ONBOARDING');
-- Get the template_id for the steps (assuming it will be the next available ID)
-- Replace 14 with actual template_id returned from above INSERT
-- 2. Create workflow steps for POT onboarding process
INSERT INTO workflow_steps (
        template_id,
        step_order,
        task_name,
        owner,
        deliverable,
        cycle_time
    )
VALUES -- Stage 1: Patient Registration
    (
        14,
        1,
        'Collect patient demographics',
        'POT',
        'Complete patient basic information form',
        'Day1'
    ),
    (
        14,
        2,
        'Collect address and contact information',
        'POT',
        'Complete address and emergency contact details',
        'Day1'
    ),
    (
        14,
        3,
        'Collect referral information',
        'POT',
        'Complete referral source and provider details',
        'Day1'
    ),
    -- Stage 2: Eligibility Verification
    (
        14,
        4,
        'Verify insurance coverage',
        'POT',
        'Verify patient insurance eligibility',
        'Day1'
    ),
    (
        14,
        5,
        'Record eligibility status',
        'POT',
        'Document eligibility verification result',
        'Day1'
    ),
    (
        14,
        6,
        'Document eligibility notes',
        'POT',
        'Record any eligibility issues or notes',
        'Day1'
    ),
    -- Stage 3: Chart Creation
    (
        14,
        7,
        'Create EMed chart (manual verification)',
        'POT',
        'Create patient chart in EMed system',
        'Day1'
    ),
    (
        14,
        8,
        'Assign facility in system',
        'POT',
        'Assign patient to appropriate facility',
        'Day1'
    ),
    (
        14,
        9,
        'Confirm chart creation complete',
        'POT',
        'Verify chart creation and facility assignment',
        'Day1'
    ),
    -- Stage 4: Intake Processing
    (
        14,
        10,
        'Request medical records',
        'POT',
        'Send medical records request to referring provider',
        'Day2'
    ),
    (
        14,
        11,
        'Collect referral documents',
        'POT',
        'Collect and verify referral documentation',
        'Day2'
    ),
    (
        14,
        12,
        'Complete prescreen call',
        'POT',
        'Conduct initial patient prescreen call',
        'Day2'
    ),
    (
        14,
        13,
        'Document received materials',
        'POT',
        'Document all received materials and status',
        'Day3'
    ),
    -- Stage 5: TV Scheduling & Provider Assignment
    (
        14,
        14,
        'Schedule Initial TV',
        'POT',
        'Schedule telehealth visit and assign regional provider',
        'Day3'
    ),
    (
        14,
        15,
        'Notify patient of TV appointment',
        'POT',
        'Send appointment confirmation to patient',
        'Day3'
    );
-- 3. Create onboarding_patients table
CREATE TABLE onboarding_patients (
    onboarding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    -- Links to patients table when created
    workflow_instance_id INTEGER,
    -- Links to workflow_instances
    -- Patient Registration Data (Stage 1)
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    phone_primary TEXT,
    email TEXT,
    gender TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    -- Address Information
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    -- Insurance Information
    insurance_provider TEXT,
    policy_number TEXT,
    group_number TEXT,
    -- Referral Information
    referral_source TEXT,
    referring_provider TEXT,
    referral_date DATE,
    -- System Fields
    patient_status TEXT DEFAULT 'Active',
    facility_assignment TEXT,
    assigned_pot_user_id INTEGER,
    -- Stage Completion Tracking
    stage1_complete BOOLEAN DEFAULT FALSE,
    stage2_complete BOOLEAN DEFAULT FALSE,
    stage3_complete BOOLEAN DEFAULT FALSE,
    stage4_complete BOOLEAN DEFAULT FALSE,
    stage5_complete BOOLEAN DEFAULT FALSE,
    -- Timestamps
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP,
    FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances(instance_id),
    FOREIGN KEY (assigned_pot_user_id) REFERENCES users(user_id)
);
-- 4. Create onboarding_tasks table
CREATE TABLE onboarding_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    onboarding_id INTEGER NOT NULL,
    workflow_step_id INTEGER NOT NULL,
    -- Task Details
    task_name TEXT NOT NULL,
    task_stage INTEGER NOT NULL,
    -- 1-5 for the 5 stages
    task_order INTEGER NOT NULL,
    -- Completion Status
    status TEXT DEFAULT 'Pending',
    -- Pending, In Progress, Complete, Skipped
    completed_by_user_id INTEGER,
    completed_date TIMESTAMP,
    -- Task-Specific Data
    task_data TEXT,
    -- JSON for flexible data storage
    notes TEXT,
    -- MVP Checkbox Fields for Quick Access
    eligibility_verified BOOLEAN DEFAULT FALSE,
    emed_chart_created BOOLEAN DEFAULT FALSE,
    documents_received BOOLEAN DEFAULT FALSE,
    prescreen_completed BOOLEAN DEFAULT FALSE,
    tv_scheduled BOOLEAN DEFAULT FALSE,
    handoff_complete BOOLEAN DEFAULT FALSE,
    -- Timestamps
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (onboarding_id) REFERENCES onboarding_patients(onboarding_id),
    FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(step_id),
    FOREIGN KEY (completed_by_user_id) REFERENCES users(user_id)
);
-- 5. Create indexes for performance
CREATE INDEX idx_onboarding_patients_workflow ON onboarding_patients(workflow_instance_id);
CREATE INDEX idx_onboarding_patients_pot_user ON onboarding_patients(assigned_pot_user_id);
CREATE INDEX idx_onboarding_patients_status ON onboarding_patients(patient_status);
CREATE INDEX idx_onboarding_tasks_onboarding ON onboarding_tasks(onboarding_id);
CREATE INDEX idx_onboarding_tasks_stage ON onboarding_tasks(task_stage);
CREATE INDEX idx_onboarding_tasks_status ON onboarding_tasks(status);
-- 6. Create view for easy onboarding status tracking
CREATE VIEW onboarding_status_view AS
SELECT op.onboarding_id,
    op.first_name || ' ' || op.last_name AS patient_name,
    op.patient_status,
    op.assigned_pot_user_id,
    u.full_name AS assigned_pot_name,
    wi.workflow_status AS workflow_status,
    op.stage1_complete,
    op.stage2_complete,
    op.stage3_complete,
    op.stage4_complete,
    op.stage5_complete,
    CASE
        WHEN op.stage5_complete = 1 THEN 'Completed'
        WHEN op.stage4_complete = 1 THEN 'Stage 5: TV Scheduling'
        WHEN op.stage3_complete = 1 THEN 'Stage 4: Intake Processing'
        WHEN op.stage2_complete = 1 THEN 'Stage 3: Chart Creation'
        WHEN op.stage1_complete = 1 THEN 'Stage 2: Eligibility Verification'
        ELSE 'Stage 1: Patient Registration'
    END AS current_stage,
    op.created_date,
    op.updated_date,
    op.completed_date
FROM onboarding_patients op
    LEFT JOIN workflow_instances wi ON op.workflow_instance_id = wi.instance_id
    LEFT JOIN users u ON op.assigned_pot_user_id = u.user_id;