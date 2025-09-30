-- Create onboarding tables
-- Create onboarding_patients table
CREATE TABLE IF NOT EXISTS onboarding_patients (
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
-- Create onboarding_tasks table
CREATE TABLE IF NOT EXISTS onboarding_tasks (
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
-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_onboarding_patients_workflow ON onboarding_patients(workflow_instance_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_patients_pot_user ON onboarding_patients(assigned_pot_user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_patients_status ON onboarding_patients(patient_status);
CREATE INDEX IF NOT EXISTS idx_onboarding_tasks_onboarding ON onboarding_tasks(onboarding_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_tasks_stage ON onboarding_tasks(task_stage);
CREATE INDEX IF NOT EXISTS idx_onboarding_tasks_status ON onboarding_tasks(status);