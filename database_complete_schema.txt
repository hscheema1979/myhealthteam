CREATE TABLE IF NOT EXISTS "roles" (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE,
    description TEXT
);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE IF NOT EXISTS "specialties" (
    specialty_id INTEGER PRIMARY KEY AUTOINCREMENT,
    specialty_name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS "user_roles" (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL, is_primary BOOLEAN DEFAULT 0,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES "users"(user_id),
    FOREIGN KEY (role_id) REFERENCES "roles"(role_id)
);
CREATE TABLE IF NOT EXISTS "region_providers" (
    region_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL, outside_provider_regions BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (region_id, provider_id),
    FOREIGN KEY (region_id) REFERENCES "regions"(region_id),
    FOREIGN KEY (provider_id) REFERENCES "providers"(provider_id)
);
CREATE TABLE IF NOT EXISTS "provider_specialties" (
    provider_id INTEGER NOT NULL,
    specialty_id INTEGER NOT NULL,
    PRIMARY KEY (provider_id, specialty_id),
    FOREIGN KEY (provider_id) REFERENCES "providers"(provider_id),
    FOREIGN KEY (specialty_id) REFERENCES "specialties"(specialty_id)
);
CREATE TABLE IF NOT EXISTS "patient_assignments_old" (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    coordinator_id INTEGER NOT NULL,
    assignment_date TEXT,
    assignment_type TEXT,
    status TEXT,
    priority_level TEXT,
    notes TEXT,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    updated_by INTEGER, initial_tv_provider_id INTEGER, recommended_provider_id INTEGER,
    FOREIGN KEY (patient_id) REFERENCES "patients_old"(patient_id),
    FOREIGN KEY (provider_id) REFERENCES "providers"(provider_id),
    FOREIGN KEY (coordinator_id) REFERENCES "coordinators"(coordinator_id),
    FOREIGN KEY (created_by) REFERENCES "users"(user_id),
    FOREIGN KEY (updated_by) REFERENCES "users"(user_id)
);
CREATE TABLE IF NOT EXISTS "insurance_eligibility_records" (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER UNIQUE NOT NULL,
    eligibility_status TEXT NOT NULL,
    coverage_start_date TEXT,
    coverage_end_date TEXT,
    confirmation_number TEXT,
    notes TEXT,
    checked_on_date TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES "prod_tasks_backup"(task_id)
);
CREATE TABLE IF NOT EXISTS "users" (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    status TEXT NOT NULL,
    hire_date TEXT,
    termination_date TEXT,
    max_patients INTEGER,
    performance_rating REAL,
    created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
, full_name TEXT, password TEXT DEFAULT 'pass123', username TEXT, last_login TEXT, alias TEXT);
CREATE TABLE IF NOT EXISTS "SOURCE_STAFF_INFO" (
"First NAme [Required]" TEXT,
  "Last NAme [Required]" TEXT,
  "Email Address [Required]" TEXT,
  "Status [READ ONLY]" TEXT,
  "Primary ROLE" TEXT,
  "Description" TEXT,
  "Secondary Role" TEXT,
  "Description.1" TEXT
);
CREATE TABLE IF NOT EXISTS "providers" (
    provider_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    first_name TEXT,
    last_name TEXT,
    email TEXT, updated_date TEXT,
    FOREIGN KEY (user_id) REFERENCES "users"(user_id),
    FOREIGN KEY (role_id) REFERENCES "roles"(role_id)
);
CREATE TABLE IF NOT EXISTS "coordinators" (
    coordinator_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    first_name TEXT,
    last_name TEXT,
    email TEXT, updated_date TEXT,
    FOREIGN KEY (user_id) REFERENCES "users"(user_id),
    FOREIGN KEY (role_id) REFERENCES "roles"(role_id)
);
CREATE TABLE IF NOT EXISTS "facilities" (
	"facility_id"	INTEGER,
	"facility_name"	TEXT NOT NULL UNIQUE, address TEXT, phone TEXT, email TEXT, created_date TIMESTAMP,
	PRIMARY KEY("facility_id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "task_billing_codes" (
    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_description TEXT,
    service_type TEXT,
    location_type TEXT,
    patient_type TEXT,
    min_minutes INTEGER,
    max_minutes INTEGER,
    billing_code TEXT NOT NULL,
    description TEXT,
    rate DECIMAL(10,2),
    effective_date TEXT NOT NULL,
    expiration_date TEXT,
    created_date TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE staff_code_mapping (
    staff_code TEXT PRIMARY KEY,
    user_id INTEGER,
    confidence_level TEXT CHECK (confidence_level IN ('HIGH', 'MEDIUM', 'LOW', 'UNMATCHED')),
    mapping_type TEXT CHECK (mapping_type IN ('PROVIDER', 'COORDINATOR', 'SPECIAL_CASE')),
    notes TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES "users"(user_id)
);
CREATE TABLE unmatched_patient_names (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_table TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE sqlite_stat1(tbl,idx,stat);
CREATE TABLE unmatched_tasks_analysis (
    unmatched_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_table TEXT NOT NULL,
    patient_name_raw TEXT,
    patient_name_cleaned TEXT,
    staff_name TEXT,
    staff_type TEXT, -- 'coordinator' or 'provider'
    task_date TEXT,
    task_type TEXT,
    service_code TEXT,
    notes TEXT,
    reason_unmatched TEXT, -- 'missing_patient', 'missing_staff', 'invalid_data'
    provider_info TEXT, -- Additional provider details for reporting
    coordinator_info TEXT, -- Additional coordinator details for reporting
    created_date TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "patients_backup_old"(
  patient_id INT,
  region_id INT,
  first_name TEXT,
  last_name TEXT,
  date_of_birth TEXT,
  gender TEXT,
  phone_primary TEXT,
  phone_secondary TEXT,
  email TEXT,
  address_street TEXT,
  address_city TEXT,
  address_state TEXT,
  address_zip TEXT,
  emergency_contact_name TEXT,
  emergency_contact_phone TEXT,
  emergency_contact_relationship TEXT,
  insurance_primary TEXT,
  insurance_policy_number TEXT,
  insurance_secondary TEXT,
  medical_record_number TEXT,
  status TEXT,
  enrollment_date TEXT,
  discharge_date TEXT,
  notes TEXT,
  created_date TEXT,
  updated_date TEXT,
  created_by INT,
  updated_by INT,
  current_facility_id INT,
  hypertension INT,
  mental_health_concerns INT,
  dementia INT,
  last_annual_wellness_visit TEXT,
  last_first_dob TEXT
);
CREATE TABLE SOURCE_PROVIDER_REGION_COVERAGE(
  "ZEN LIST OF PROVIDERS" TEXT,
  UNASSIGNED TEXT,
  Malhotra TEXT,
  Andrew TEXT,
  Ethel TEXT,
  Albert TEXT,
  Lourdes TEXT,
  Anisha TEXT,
  Jaspreet TEXT,
  Genevieive REAL,
  "Unnamed: 10" TEXT,
  Eden REAL,
  Ugochi REAL,
  "Unnamed: 13" TEXT,
  Angela TEXT,
  "Unnamed: 15" TEXT
);
CREATE TABLE SOURCE_REGION_ZIP_CODES(
  Region TEXT,
  City TEXT,
  "ZIP Codes" TEXT,
  "Unnamed: 3" TEXT,
  "Region.1" TEXT,
  "City.1" TEXT,
  "ZIP Codes.1" TEXT,
  "Unnamed: 7" TEXT,
  "Region.2" TEXT,
  "City.2" TEXT,
  "ZIP Codes.2" TEXT,
  "Unnamed: 11" TEXT,
  "Region.3" TEXT,
  "City.3" TEXT,
  "ZIP Codes.3" TEXT,
  "SCC LIST OF PROVIDERS" TEXT,
  UNASSIGNED TEXT,
  Malhotra TEXT,
  Anisha TEXT,
  Ethel TEXT,
  "Unnamed: 14" TEXT,
  "Unnamed: 15" TEXT,
  "Region.4" TEXT,
  "City.4" TEXT,
  "ZIP Codes.4" TEXT
);
CREATE TABLE SOURCE_TASKS_AND_CODES(
  tasks TEXT,
  "Code(s)" TEXT,
  role TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_COORDINATOR_TASKS_HISTORY" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Notes" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "Current" TEXT,
  "NotZEN" TEXT,
  "Invalid Date/Time" TEXT,
  "Invalid Patient Dropdown" TEXT,
  "Start Time A" TEXT,
  "Stop Time A" TEXT
);
CREATE TABLE workflow_templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_name TEXT NOT NULL UNIQUE
);
CREATE TABLE workflow_steps (
    step_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    step_order INTEGER NOT NULL,
    task_name TEXT NOT NULL,
    owner TEXT,
    deliverable TEXT,
    cycle_time TEXT,
    FOREIGN KEY (template_id) REFERENCES workflow_templates(template_id)
);
CREATE TABLE IF NOT EXISTS "workflow_instances_old" (
    instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, patient_id TEXT, coordinator_id TEXT, current_owner_role TEXT, current_owner_user_id TEXT, current_step_id INTEGER, notes TEXT,
    FOREIGN KEY (template_id) REFERENCES workflow_templates(template_id)
);
CREATE TABLE IF NOT EXISTS "tasks"(
  task_id INT,
  patient_name TEXT,
  patient_id TEXT,
  user_id TEXT,
  full_name TEXT,
  staff_code TEXT,
  role_id INT,
  task_date TEXT,
  start_time TEXT,
  stop_time TEXT,
  task_type TEXT,
  duration_minutes INT,
  service_code TEXT,
  notes TEXT,
  task_state TEXT
, task_description TEXT);
CREATE TABLE coordinator_billing_codes (
    code_id INTEGER PRIMARY KEY AUTOINCREMENT,
    billing_code TEXT UNIQUE NOT NULL,
    description TEXT,
    min_minutes INTEGER,
    max_minutes INTEGER
);
CREATE TABLE IF NOT EXISTS "daily_tasks" (
    daily_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_description TEXT,
    service_type TEXT,
    description TEXT,
    coordinator_id INTEGER,
    patient_id INTEGER,
    task_date DATE,
    duration_minutes INTEGER,
    notes TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "user_patient_assignments_old" (user_id INTEGER NOT NULL, patient_id INTEGER NOT NULL, role_id INTEGER NOT NULL, PRIMARY KEY (user_id, patient_id, role_id), FOREIGN KEY (user_id) REFERENCES "users" (user_id), FOREIGN KEY (patient_id) REFERENCES "patients_old" (patient_id), FOREIGN KEY (role_id) REFERENCES "user_roles" (role_id));
CREATE TABLE care_plans (
                patient_name TEXT PRIMARY KEY,
                plan_details TEXT,
                updated_by TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE IF NOT EXISTS "regions" (
                region_id INTEGER PRIMARY KEY AUTOINCREMENT,
                zip_code TEXT,
                city TEXT,
                state TEXT,
                county TEXT,
                status TEXT NOT NULL DEFAULT 'active',
                created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
CREATE TABLE provider_zip_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    zip_code TEXT NOT NULL,
    city TEXT,
    state TEXT,
    patient_count INTEGER DEFAULT 0,
    region_count INTEGER DEFAULT 0,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);
CREATE TABLE dashboard_provider_monthly_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    average_task_completion_time_minutes REAL DEFAULT 0.0,
    total_patients_served INTEGER DEFAULT 0,
    max_patients_allowed INTEGER DEFAULT 60,
    patients_assigned INTEGER DEFAULT 0,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);
CREATE TABLE dashboard_coordinator_monthly_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinator_id INTEGER NOT NULL,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    total_minutes INTEGER DEFAULT 0,
    total_minutes_per_patient REAL DEFAULT 0.0,
    total_tasks_completed INTEGER DEFAULT 0,
    average_daily_tasks REAL DEFAULT 0.0,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (coordinator_id) REFERENCES coordinators(coordinator_id)
);
CREATE TABLE dashboard_patient_assignment_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    patient_name TEXT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_minutes INTEGER NOT NULL,
    billing_code_id INTEGER,
    billing_code TEXT,
    billing_code_description TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (billing_code_id) REFERENCES coordinator_billing_codes(code_id)
);
CREATE TABLE dashboard_task_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    provider_id INTEGER,
    coordinator_id INTEGER,
    patient_id INTEGER,
    task_date TEXT,
    duration_minutes INTEGER,
    billing_code TEXT,
    status TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(task_id),
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
    FOREIGN KEY (coordinator_id) REFERENCES coordinators(coordinator_id),
    FOREIGN KEY (patient_id) REFERENCES "patients_old"(patient_id)
);
CREATE TABLE dashboard_region_patient_assignment_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    patient_name TEXT,
    patient_status TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (region_id) REFERENCES regions(region_id),
    FOREIGN KEY (patient_id) REFERENCES "patients_old"(patient_id)
);
CREATE TABLE coordinator_monthly_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinator_id INTEGER NOT NULL,
    coordinator_name TEXT,
    patient_id TEXT NOT NULL,
    patient_name TEXT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_minutes INTEGER NOT NULL,
    billing_code_id INTEGER,
    billing_code TEXT,
    billing_code_description TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (billing_code_id) REFERENCES coordinator_billing_codes(code_id)
);
CREATE TABLE provider_tasks_summary (summary_id INTEGER PRIMARY KEY, provider_id INTEGER NOT NULL, provider_name TEXT NOT NULL, month INTEGER NOT NULL, year INTEGER NOT NULL, total_tasks_completed INTEGER DEFAULT 0, total_time_spent_minutes INTEGER DEFAULT 0, average_task_completion_time_minutes REAL DEFAULT 0.0, created_date DATETIME DEFAULT CURRENT_TIMESTAMP, updated_date DATETIME DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS "provider_region_summary"(
  summary_id INT,
  provider_id INT,
  region_id INT,
  zip_code TEXT,
  city TEXT,
  state TEXT,
  patient_count INT,
  created_date TEXT
);
CREATE TABLE IF NOT EXISTS "patient_region_mapping_old"(
  mapping_id INT,
  patient_id INT,
  region_id INT,
  zip_code TEXT,
  city TEXT,
  state TEXT,
  created_date TEXT
);
CREATE TABLE IF NOT EXISTS "coordinator_task_definitions" (
	"task_definition_id"	INTEGER,
	"task_category"	TEXT NOT NULL,
	"task_description"	TEXT NOT NULL,
	"created_at"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	"updated_at"	TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("task_definition_id" AUTOINCREMENT)
);
CREATE TABLE provider_tasks_backup(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT
);
CREATE TABLE provider_tasks_restored(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT
);
CREATE TABLE IF NOT EXISTS "dashboard_provider_county_map" (
        map_id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_id INTEGER NOT NULL,
        county TEXT NOT NULL,
        state TEXT NOT NULL,
        patient_count INTEGER DEFAULT 0,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES "providers"(provider_id)
    );
CREATE TABLE IF NOT EXISTS "dashboard_provider_zip_map" (
        map_id INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_id INTEGER NOT NULL,
        zip_code TEXT NOT NULL,
        city TEXT,
        state TEXT,
        patient_count INTEGER DEFAULT 0,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (provider_id) REFERENCES "providers"(provider_id)
    );
CREATE TABLE IF NOT EXISTS "provider_monthly_summary" (
	"summary_id"	INTEGER,
	"provider_id"	INTEGER NOT NULL,
	"provider_name"	TEXT NOT NULL,
	"month"	INTEGER NOT NULL,
	"year"	INTEGER NOT NULL,
	"total_tasks_completed"	INTEGER DEFAULT 0,
	"total_time_spent_minutes"	INTEGER DEFAULT 0,
	"created_date"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	"updated_date"	DATETIME DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("summary_id" AUTOINCREMENT),
	FOREIGN KEY("provider_id") REFERENCES "providers"("provider_id")
);
CREATE TABLE patient_status_types (status_id INTEGER PRIMARY KEY AUTOINCREMENT, status_name TEXT NOT NULL UNIQUE, description TEXT, created_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_date TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS "patients_old" (
	"patient_id"	INT,
	"region_id"	INT,
	"first_name"	TEXT,
	"last_name"	TEXT,
	"date_of_birth"	TEXT,
	"gender"	TEXT,
	"phone_primary"	TEXT,
	"phone_secondary"	TEXT,
	"email"	TEXT,
	"address_street"	TEXT,
	"address_city"	TEXT,
	"address_state"	TEXT,
	"address_zip"	TEXT,
	"emergency_contact_name"	TEXT,
	"emergency_contact_phone"	TEXT,
	"emergency_contact_relationship"	TEXT,
	"insurance_primary"	TEXT,
	"insurance_policy_number"	TEXT,
	"insurance_secondary"	TEXT,
	"medical_record_number"	TEXT,
	"enrollment_date"	TEXT,
	"discharge_date"	TEXT,
	"notes"	TEXT,
	"created_date"	TEXT,
	"updated_date"	TEXT,
	"created_by"	INT,
	"updated_by"	INT,
	"current_facility_id"	INT,
	"hypertension"	INT,
	"mental_health_concerns"	INT,
	"dementia"	INT,
	"last_annual_wellness_visit"	TEXT,
	"last_first_dob"	TEXT,
	"status"	TEXT
, medical_records_requested BOOLEAN DEFAULT FALSE, referral_documents_received BOOLEAN DEFAULT FALSE, insurance_cards_received BOOLEAN DEFAULT FALSE, emed_signature_received BOOLEAN DEFAULT FALSE, last_visit_date DATE, facility TEXT, er_count_1yr INTEGER, hospitalization_count_1yr INTEGER, clinical_biometric TEXT, chronic_conditions_provider TEXT, cancer_history TEXT, subjective_risk_level INTEGER, provider_mh_schizophrenia BOOLEAN DEFAULT FALSE, provider_mh_depression BOOLEAN DEFAULT FALSE, provider_mh_anxiety BOOLEAN DEFAULT FALSE, provider_mh_stress BOOLEAN DEFAULT FALSE, provider_mh_adhd BOOLEAN DEFAULT FALSE, provider_mh_bipolar BOOLEAN DEFAULT FALSE, provider_mh_suicidal BOOLEAN DEFAULT FALSE, active_specialists TEXT, code_status TEXT, cognitive_function TEXT, functional_status TEXT, goals_of_care TEXT, active_concerns TEXT, initial_tv_completed_date TEXT, initial_tv_notes TEXT, initial_tv_provider TEXT);
CREATE TABLE IF NOT EXISTS "onboarding_patients_old" (
    onboarding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,  -- Links to patients table when created
    workflow_instance_id INTEGER, -- Links to workflow_instances
    
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
    completed_date TIMESTAMP, medical_records_requested BOOLEAN DEFAULT FALSE, referral_documents_received BOOLEAN DEFAULT FALSE, insurance_cards_received BOOLEAN DEFAULT FALSE, emed_signature_received BOOLEAN DEFAULT FALSE, appointment_contact_name TEXT, appointment_contact_phone TEXT, appointment_contact_email TEXT, medical_contact_name TEXT, medical_contact_phone TEXT, medical_contact_email TEXT, primary_care_provider TEXT, pcp_last_seen DATE, active_specialist TEXT, specialist_last_seen DATE, chronic_conditions_onboarding TEXT, mh_schizophrenia BOOLEAN DEFAULT FALSE, mh_depression BOOLEAN DEFAULT FALSE, mh_anxiety BOOLEAN DEFAULT FALSE, mh_stress BOOLEAN DEFAULT FALSE, mh_adhd BOOLEAN DEFAULT FALSE, mh_bipolar BOOLEAN DEFAULT FALSE, mh_suicidal BOOLEAN DEFAULT FALSE, assigned_provider_user_id INTEGER, tv_date DATE, tv_time TIME, tv_scheduled BOOLEAN DEFAULT FALSE, patient_notified BOOLEAN DEFAULT FALSE, hypertension BOOLEAN DEFAULT FALSE, mental_health_concerns BOOLEAN DEFAULT FALSE, dementia BOOLEAN DEFAULT FALSE, annual_well_visit BOOLEAN DEFAULT FALSE, initial_tv_completed BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (workflow_instance_id) REFERENCES "workflow_instances_old"(instance_id),
    FOREIGN KEY (assigned_pot_user_id) REFERENCES users(user_id)
);
CREATE TABLE onboarding_tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    onboarding_id INTEGER NOT NULL,
    workflow_step_id INTEGER NOT NULL,
    
    -- Task Details
    task_name TEXT NOT NULL,
    task_stage INTEGER NOT NULL, -- 1-5 for the 5 stages
    task_order INTEGER NOT NULL,
    
    -- Completion Status
    status TEXT DEFAULT 'Pending', -- Pending, In Progress, Complete, Skipped
    completed_by_user_id INTEGER,
    completed_date TIMESTAMP,
    
    -- Task-Specific Data
    task_data TEXT, -- JSON for flexible data storage
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
    
    FOREIGN KEY (onboarding_id) REFERENCES "onboarding_patients_old"(onboarding_id),
    FOREIGN KEY (workflow_step_id) REFERENCES workflow_steps(step_id),
    FOREIGN KEY (completed_by_user_id) REFERENCES users(user_id)
);
CREATE TABLE coordinator_tasks_archive (
    coordinator_task_id INTEGER PRIMARY KEY,
    patient_id TEXT,
    patient_name TEXT,
    coordinator_id TEXT,
    user_id INTEGER,
    coordinator_name TEXT,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    source_hash TEXT,
    archived_date TEXT DEFAULT CURRENT_TIMESTAMP,
    archive_reason TEXT
);
CREATE TABLE coordinator_tasks_yr_mo (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    coordinator_id INTEGER,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES "patients_old"(patient_id),
    FOREIGN KEY (coordinator_id) REFERENCES users(user_id)
);
CREATE TABLE workflow_instances (
    instance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Basic workflow info
    template_id INTEGER NOT NULL,
    template_name TEXT NOT NULL,
    patient_id TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    coordinator_id TEXT NOT NULL,
    coordinator_name TEXT,
    priority TEXT DEFAULT 'Normal',
    workflow_status TEXT DEFAULT 'Active',
    
    -- Current state tracking
    current_step INTEGER DEFAULT 1,
    current_owner_role TEXT,
    current_owner_user_id TEXT,
    current_owner_name TEXT,
    
    -- Step 1 tracking
    step1_complete BOOLEAN DEFAULT FALSE,
    step1_date DATE,
    step1_completed_by TEXT,
    step1_completed_by_name TEXT,
    step1_duration_minutes INTEGER,
    step1_notes TEXT,
    
    -- Step 2 tracking  
    step2_complete BOOLEAN DEFAULT FALSE,
    step2_date DATE,
    step2_completed_by TEXT,
    step2_completed_by_name TEXT,
    step2_duration_minutes INTEGER,
    step2_notes TEXT,
    
    -- Step 3 tracking
    step3_complete BOOLEAN DEFAULT FALSE,
    step3_date DATE,
    step3_completed_by TEXT,
    step3_completed_by_name TEXT,
    step3_duration_minutes INTEGER,
    step3_notes TEXT,
    
    -- Step 4 tracking
    step4_complete BOOLEAN DEFAULT FALSE,
    step4_date DATE,
    step4_completed_by TEXT,
    step4_completed_by_name TEXT,
    step4_duration_minutes INTEGER,
    step4_notes TEXT,
    
    -- Step 5 tracking
    step5_complete BOOLEAN DEFAULT FALSE,
    step5_date DATE,
    step5_completed_by TEXT,
    step5_completed_by_name TEXT,
    step5_duration_minutes INTEGER,
    step5_notes TEXT,
    
    -- Step 6 tracking (some workflows have more steps)
    step6_complete BOOLEAN DEFAULT FALSE,
    step6_date DATE,
    step6_completed_by TEXT,
    step6_completed_by_name TEXT,
    step6_duration_minutes INTEGER,
    step6_notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    FOREIGN KEY (template_id) REFERENCES workflow_templates(template_id)
);
CREATE TABLE coordinator_tasks_2024_01(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_01(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_02(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_02(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_03(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_03(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_04(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_04(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_05(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_05(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_06(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_06(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_07(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_07(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_08(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_08(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_09(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_09(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_10(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_10(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_11(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_11(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2024_12(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2024_12(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2025_10(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2025_10(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2025_11(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2025_11(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE coordinator_tasks_2025_12(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE provider_tasks_2025_12(
  provider_task_id INT,
  task_id INT,
  provider_id INT,
  provider_name TEXT,
  patient_name TEXT,
  user_id INT,
  patient_id INT,
  status TEXT,
  notes TEXT,
  minutes_of_service INT,
  billing_code_id INT,
  created_date NUM,
  updated_date NUM,
  task_date NUM,
  month INT,
  year INT,
  billing_code TEXT,
  billing_code_description TEXT,
  task_description TEXT
);
CREATE TABLE staging_coordinator_tasks(
  src_rowid INT,
  staff_code TEXT,
  patient_name_raw TEXT,
  task_type,
  notes,
  minutes_raw REAL,
  activity_date,
  year_month
);
CREATE TABLE staging_provider_tasks(
  src_rowid INT,
  provider_code TEXT,
  patient_name_raw TEXT,
  service,
  billing_code,
  minutes_raw TEXT,
  activity_date,
  year_month
);
CREATE TABLE coordinator_monthly_billing_2025_09 (coordinator_id INT, patient_id INT, billing_code TEXT, total_minutes INT, month INT, year INT);
CREATE TABLE provider_monthly_billing_2025_09 (provider_id INT, patient_id INT, billing_code TEXT, total_tasks INT, month INT, year INT);
CREATE TABLE provider_weekly_summary_2025_09 (provider_id INT, week INT, year INT, total_tasks INT);
CREATE TABLE IF NOT EXISTS "TEST_HEADER_SCHEMA_MAP" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" TEXT,
  "Notes" TEXT,
  "Stop Time" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Start Time A" TEXT,
  "Stop Time A" TEXT
);
CREATE TABLE TEST_PROVIDER_HEADER_SCHEMA_MAP (id INTEGER, Prov TEXT, Coding TEXT, [Patient Last, First DOB] TEXT, DOS TEXT, Service TEXT, Minutes TEXT, Hospice TEXT, Notes TEXT, [WC Size  (sqcm)] TEXT, [WC Diagnosis (HH-OK to free type)] TEXT, [Graft Info] TEXT, [Wound#] TEXT, [Session#] TEXT, [Multiple Grafts] TEXT, [Billed Date  Notes] TEXT, [Paid by Patient] TEXT);
CREATE TABLE coordinator_monthly_summary_2025_09 (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinator_id INTEGER NOT NULL,
    coordinator_name TEXT,
    patient_id TEXT NOT NULL,
    patient_name TEXT,
    year INTEGER NOT NULL DEFAULT 2025,
    month INTEGER NOT NULL DEFAULT 9,
    total_minutes INTEGER NOT NULL,
    billing_code TEXT,
    billing_code_description TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE coordinator_minutes_2025_09 (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    coordinator_id INTEGER NOT NULL,
    coordinator_name TEXT,
    year INTEGER NOT NULL DEFAULT 2025,
    month INTEGER NOT NULL DEFAULT 9,
    total_minutes INTEGER NOT NULL,
    billing_code TEXT,
    billing_code_description TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE provider_weekly_summary_2025_35 (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    year INTEGER NOT NULL DEFAULT 2025,
    week_number INTEGER NOT NULL DEFAULT 35,
    total_tasks_completed INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "patient_panel_old" (patient_id TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, date_of_birth TEXT, gender TEXT, phone_primary TEXT, email TEXT, address_street TEXT, address_city TEXT, address_state TEXT, address_zip TEXT, emergency_contact_name TEXT, emergency_contact_phone TEXT, insurance_primary TEXT, insurance_policy_number TEXT, status TEXT, enrollment_date TEXT, discharge_date TEXT, notes TEXT, created_date TEXT, updated_date TEXT, current_facility_id INT, hypertension INT, mental_health_concerns INT, dementia INT, last_annual_wellness_visit TEXT, provider_id INTEGER, provider_name TEXT, coordinator_id INTEGER, coordinator_name TEXT, stage1_complete INTEGER, stage2_complete INTEGER, initial_tv_completed INTEGER, initial_tv_completed_date TEXT, initial_tv_notes TEXT, source_table TEXT, source_column TEXT, last_visit_date TEXT, last_visit_provider_id INT, last_visit_provider_name TEXT, facility TEXT, goals_of_care TEXT, code_status TEXT, service_type TEXT);
CREATE TABLE IF NOT EXISTS "patient_assignments_backup_20250929" (assignment_id INTEGER PRIMARY KEY, patient_id TEXT, provider_id INTEGER, coordinator_id INTEGER, assignment_date TEXT, assignment_type TEXT, status TEXT, priority_level TEXT, notes TEXT, created_date TEXT DEFAULT CURRENT_TIMESTAMP, updated_date TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER, updated_by INTEGER, initial_tv_provider_id INTEGER);
CREATE TABLE user_patient_assignments (user_id INTEGER, patient_id TEXT, role_id INTEGER);
CREATE TABLE patient_region_mapping (mapping_id INT, patient_id TEXT, region_id INT, zip_code TEXT, city TEXT, state TEXT);
CREATE TABLE onboarding_patients (onboarding_id INTEGER PRIMARY KEY, patient_id TEXT, workflow_instance_id INTEGER, first_name TEXT, last_name TEXT, date_of_birth DATE, phone_primary TEXT, email TEXT, gender TEXT, emergency_contact_name TEXT, emergency_contact_phone TEXT, address_street TEXT, address_city TEXT, address_state TEXT, address_zip TEXT, insurance_provider TEXT, policy_number TEXT, group_number TEXT, referral_source TEXT, referring_provider TEXT, referral_date DATE, patient_status TEXT DEFAULT 'Active', facility_assignment TEXT, assigned_pot_user_id INTEGER, stage1_complete BOOLEAN DEFAULT FALSE, stage2_complete BOOLEAN DEFAULT FALSE, stage3_complete BOOLEAN DEFAULT FALSE, stage4_complete BOOLEAN DEFAULT FALSE, stage5_complete BOOLEAN DEFAULT FALSE, created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, completed_date TIMESTAMP, medical_records_requested BOOLEAN DEFAULT FALSE, referral_documents_received BOOLEAN DEFAULT FALSE, insurance_cards_received BOOLEAN DEFAULT FALSE, emed_signature_received BOOLEAN DEFAULT FALSE, appointment_contact_name TEXT, appointment_contact_phone TEXT, appointment_contact_email TEXT, medical_contact_name TEXT, medical_contact_phone TEXT, medical_contact_email TEXT, primary_care_provider TEXT, pcp_last_seen DATE, active_specialist TEXT, specialist_last_seen DATE, chronic_conditions_onboarding TEXT, mh_schizophrenia BOOLEAN DEFAULT FALSE, mh_depression BOOLEAN DEFAULT FALSE, mh_anxiety BOOLEAN DEFAULT FALSE, mh_stress BOOLEAN DEFAULT FALSE, mh_adhd BOOLEAN DEFAULT FALSE, mh_bipolar BOOLEAN DEFAULT FALSE, mh_suicidal BOOLEAN DEFAULT FALSE, assigned_provider_user_id INTEGER, tv_date DATE, tv_time TIME, tv_scheduled BOOLEAN DEFAULT FALSE, patient_notified BOOLEAN DEFAULT FALSE, hypertension BOOLEAN DEFAULT FALSE, mental_health_concerns BOOLEAN DEFAULT FALSE, dementia BOOLEAN DEFAULT FALSE, annual_well_visit BOOLEAN DEFAULT FALSE, eligibility_status TEXT, eligibility_notes TEXT, eligibility_verified BOOLEAN DEFAULT FALSE, emed_chart_created BOOLEAN DEFAULT FALSE, chart_id TEXT, facility_confirmed BOOLEAN DEFAULT FALSE, chart_notes TEXT, intake_call_completed BOOLEAN DEFAULT FALSE, intake_notes TEXT, initial_tv_completed BOOLEAN DEFAULT FALSE, assigned_coordinator_user_id INTEGER, initial_tv_completed_date TEXT, initial_tv_notes TEXT, initial_tv_provider TEXT);
CREATE TABLE patients_backup (patient_id TEXT, region_id INT, first_name TEXT, last_name TEXT, date_of_birth TEXT, gender TEXT, phone_primary TEXT, phone_secondary TEXT, email TEXT, address_street TEXT, address_city TEXT, address_state TEXT, address_zip TEXT, emergency_contact_name TEXT, emergency_contact_phone TEXT, emergency_contact_relationship TEXT, insurance_primary TEXT, insurance_policy_number TEXT, insurance_secondary TEXT, medical_record_number TEXT, status TEXT, enrollment_date TEXT, discharge_date TEXT, notes TEXT, created_date TEXT, updated_date TEXT, created_by INT, updated_by INT, current_facility_id INT, hypertension INT, mental_health_concerns INT, dementia INT, last_annual_wellness_visit TEXT);
CREATE TABLE IF NOT EXISTS "combined_data" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "WC Size  (sqcm)" TEXT,
  "WC Diagnosis (HH-OK to free type)" TEXT,
  "Graft Info" TEXT,
  "Wound#" REAL,
  "Session#" REAL,
  "Multiple Grafts" TEXT
);
CREATE TABLE IF NOT EXISTS "source_provider_tasks_2025_07" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "source_provider_tasks_2025_08" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "source_coordinator_tasks_2025_07" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" TEXT,
  "Notes" TEXT,
  "Stop Time" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "Start Time A" TEXT,
  "Stop Time A" TEXT
);
CREATE TABLE IF NOT EXISTS "source_coordinator_tasks_2025_08" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" TEXT,
  "Notes" TEXT,
  "Stop Time" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "NotZEN" TEXT,
  "Start Time A" TEXT,
  "Stop Time A" TEXT
);
CREATE TABLE current_month_coordinator_summary (coordinator_id TEXT, patient_id TEXT, total_minutes INT, year INT, month INT);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_1999_12" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Notes" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2001_01" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "WC Size  (sqcm)" TEXT,
  "WC Diagnosis (HH-OK to free type)" TEXT,
  "Graft Info" TEXT,
  "Wound#" REAL,
  "Session#" REAL,
  "Multiple Grafts" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2022_01" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" TEXT,
  "Notes" TEXT,
  "Stop Time" TEXT,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "NotZEN" TEXT,
  "Start Time A" TEXT,
  "Stop Time A" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2023_05" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" INTEGER,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "WC Size  (sqcm)" TEXT,
  "WC Diagnosis (HH-OK to free type)" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2023_06" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" INTEGER,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2023_07" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" INTEGER,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2023_12" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" INTEGER,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_01" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" INTEGER,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_02" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_03" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Billed Date  Notes" TEXT,
  "Paid by Patient" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_04" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_05" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT,
  "Paid by Patient" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_06" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_07" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_08" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_09" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_10" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_11" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" INTEGER,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2024_12" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_01" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_02" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_03" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_04" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_05" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_06" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_07" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" TEXT,
  "Notes" TEXT,
  "Stop Time" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "Start Time A" TEXT,
  "Stop Time A" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_07" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_08" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" TEXT,
  "Notes" TEXT,
  "Stop Time" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "NotZEN" TEXT,
  "Start Time A" TEXT,
  "Stop Time A" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_08" (
"1" INTEGER,
  "Prov" TEXT,
  "Coding" REAL,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Billed Date  Notes" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_09" (
"Staff" TEXT,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" TEXT,
  "Notes" TEXT,
  "Stop Time" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Start Time A" TEXT,
  "Stop Time A" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PATIENT_DATA" (
"Pt Status" TEXT,
  "Pt Name" TEXT,
  "LAST FIRST DOB" TEXT,
  "Last" TEXT,
  "First" TEXT,
  "DOB" TEXT,
  "Contact Name" TEXT,
  "Phone" TEXT,
  "Street" TEXT,
  "City" TEXT,
  "State" TEXT,
  "Zip" TEXT,
  "Fac" TEXT,
  "Rep(s)" TEXT,
  "Add to Map" TEXT,
  "Ins1" TEXT,
  "Policy" TEXT,
  "Region" TEXT,
  "Initial TV Prov" TEXT,
  "Recommended  Reg Prov" TEXT,
  "Assigned  Reg Prov" TEXT,
  "Assigned CM" TEXT,
  "BCD Correct Name" TEXT,
  "Row" REAL,
  "Trigger" INTEGER,
  "Status" TEXT,
  "List" TEXT,
  "eMed Chart Created Y/N" TEXT,
  "Trigger.1" INTEGER,
  "Status.1" TEXT,
  "List.1" TEXT,
  "Prescreen Call Notes" TEXT,
  "eMed Intake Form Y/N" TEXT,
  "Initial TV Date" TEXT,
  "Trigger.2" INTEGER,
  "Status.2" TEXT,
  "List.2" TEXT,
  "eMed Records Routing Notes" TEXT,
  "Trigger.3" INTEGER,
  "Status.3" TEXT,
  "List.3" TEXT,
  "Initial TV Notes" TEXT,
  "TV Note" TEXT,
  "CM Notified" TEXT,
  "Trigger.4" INTEGER,
  "Status.4" TEXT,
  "List.4" TEXT,
  "Schedule HV 2w Notes" TEXT,
  "Initial HV Date" TEXT,
  "Trigger.5" INTEGER,
  "List.5" TEXT,
  "List6 Notes" TEXT,
  "Labs" TEXT
);
CREATE TABLE provider_weekly_summary (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    average_daily_minutes REAL DEFAULT 0.0,
    days_active INTEGER DEFAULT 0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_01" (
"Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Notes" TEXT,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "Start Time A" TEXT,
  "Stop Time A" TEXT,
  "Provider" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_02" (
"Staff" REAL,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" REAL,
  "Notes" TEXT,
  "Stop Time" REAL,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "NotZEN" TEXT,
  "Year" REAL,
  "Month" REAL,
  "Start Time A" TEXT,
  "Stop Time A" TEXT,
  "Provider" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_03" (
"Staff" REAL,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" REAL,
  "Notes" TEXT,
  "Stop Time" REAL,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "NotZEN" TEXT,
  "Year" REAL,
  "Month" REAL,
  "Start Time A" TEXT,
  "Stop Time A" TEXT,
  "Provider" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_04" (
"Staff" REAL,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" REAL,
  "Notes" TEXT,
  "Stop Time" REAL,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "NotZEN" REAL,
  "Year" REAL,
  "Month" REAL,
  "Start Time A" TEXT,
  "Stop Time A" TEXT,
  "Provider" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_05" (
"Staff" REAL,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" REAL,
  "Notes" TEXT,
  "Stop Time" REAL,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "NotZEN" REAL,
  "Year" REAL,
  "Month" REAL,
  "Start Time A" TEXT,
  "Stop Time A" TEXT,
  "Provider" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_CM_TASKS_2025_06" (
"Staff" REAL,
  "Pt Name" TEXT,
  "Type" TEXT,
  "Date Only" TEXT,
  "Start Time" REAL,
  "Notes" TEXT,
  "Stop Time" REAL,
  "Start Time B" TEXT,
  "Stop Time B" TEXT,
  "Mins B" REAL,
  "ZEN" REAL,
  "Total Mins" REAL,
  "Current" REAL,
  "Last, First DOB" TEXT,
  "NotZEN" TEXT,
  "Year" REAL,
  "Month" REAL,
  "Start Time A" TEXT,
  "Stop Time A" TEXT,
  "Provider" TEXT
);
CREATE TABLE provider_weekly_summary_with_billing (
    summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL,
    provider_name TEXT NOT NULL,
    week_start_date TEXT NOT NULL,
    week_end_date TEXT NOT NULL,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    total_tasks_completed INTEGER DEFAULT 0,
    total_time_spent_minutes INTEGER DEFAULT 0,
    billing_code TEXT,
    billing_code_description TEXT,
    status TEXT,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    paid BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);
CREATE TABLE patient_assignments (assignment_id INTEGER PRIMARY KEY, patient_id TEXT, provider_id INTEGER, coordinator_id INTEGER, assignment_date TEXT, assignment_type TEXT, status TEXT, priority_level TEXT, notes TEXT, created_date TEXT DEFAULT CURRENT_TIMESTAMP, updated_date TEXT DEFAULT CURRENT_TIMESTAMP, created_by INTEGER, updated_by INTEGER, initial_tv_provider_id INTEGER);
CREATE INDEX idx_users_email ON "users"(email);
CREATE INDEX idx_providers_user ON "providers"(user_id);
CREATE INDEX idx_coordinators_user ON "coordinators"(user_id);
CREATE INDEX idx_staff_code_mapping_code ON staff_code_mapping(staff_code);
CREATE INDEX idx_staff_code_mapping_user_id ON staff_code_mapping(user_id);
CREATE INDEX idx_prod_patient_assignments_patient_id ON "patient_assignments_old"(patient_id);
CREATE INDEX idx_prod_coordinators_coordinator_id ON "coordinators"(coordinator_id);
CREATE INDEX idx_unmatched_patient_names_source ON unmatched_patient_names(source_table);
CREATE INDEX idx_unmatched_patient_names_name ON unmatched_patient_names(patient_name);
CREATE INDEX idx_unmatched_source ON unmatched_patient_names(source_table);
CREATE INDEX idx_unmatched_name ON unmatched_patient_names(patient_name);
CREATE INDEX idx_prod_task_billing_codes_lookup 
ON "task_billing_codes" (billing_code, rate);
CREATE INDEX idx_provider_zip_summary_provider ON provider_zip_summary(provider_id);
CREATE INDEX idx_provider_zip_summary_zip ON provider_zip_summary(zip_code);
CREATE INDEX idx_dashboard_provider_monthly_summary_provider ON dashboard_provider_monthly_summary(provider_id, year, month);
CREATE INDEX idx_dashboard_coordinator_monthly_summary_coordinator ON dashboard_coordinator_monthly_summary(coordinator_id, year, month);
CREATE INDEX idx_dashboard_patient_assignment_summary_user ON dashboard_patient_assignment_summary(user_id);
CREATE INDEX idx_dashboard_task_summary_task ON dashboard_task_summary(task_id);
CREATE INDEX idx_dashboard_task_summary_provider ON dashboard_task_summary(provider_id);
CREATE INDEX idx_dashboard_task_summary_coordinator ON dashboard_task_summary(coordinator_id);
CREATE INDEX idx_dashboard_task_summary_patient ON dashboard_task_summary(patient_id);
CREATE INDEX idx_dashboard_region_patient_assignment_summary_region ON dashboard_region_patient_assignment_summary(region_id);
CREATE INDEX idx_dashboard_region_patient_assignment_summary_patient ON dashboard_region_patient_assignment_summary(patient_id);
CREATE INDEX idx_coordinator_monthly_summary_coordinator ON coordinator_monthly_summary(coordinator_id, year, month);
CREATE INDEX idx_provider_county_map_provider ON dashboard_provider_county_map(provider_id);
CREATE INDEX idx_provider_county_map_county ON dashboard_provider_county_map(county, state);
CREATE INDEX idx_provider_zip_map_provider ON dashboard_provider_zip_map(provider_id);
CREATE INDEX idx_provider_zip_map_zip ON dashboard_provider_zip_map(zip_code);
CREATE INDEX idx_onboarding_patients_workflow ON "onboarding_patients_old"(workflow_instance_id);
CREATE INDEX idx_onboarding_patients_pot_user ON "onboarding_patients_old"(assigned_pot_user_id);
CREATE INDEX idx_onboarding_patients_status ON "onboarding_patients_old"(patient_status);
CREATE INDEX idx_onboarding_tasks_onboarding ON onboarding_tasks(onboarding_id);
CREATE INDEX idx_onboarding_tasks_stage ON onboarding_tasks(task_stage);
CREATE INDEX idx_onboarding_tasks_status ON onboarding_tasks(status);
CREATE INDEX idx_patients_last_visit_date ON "patients_old"(last_visit_date);
CREATE INDEX idx_patients_risk_level ON "patients_old"(subjective_risk_level);
CREATE INDEX idx_onboarding_stage1 ON "onboarding_patients_old"(stage1_complete);
CREATE INDEX idx_onboarding_stage2 ON "onboarding_patients_old"(stage2_complete);
CREATE INDEX idx_onboarding_provider_assignment ON "onboarding_patients_old"(assigned_provider_user_id);
CREATE INDEX idx_workflow_instances_template ON workflow_instances(template_id);
CREATE INDEX idx_workflow_instances_patient ON workflow_instances(patient_id);
CREATE INDEX idx_workflow_instances_coordinator ON workflow_instances(coordinator_id);
CREATE INDEX idx_workflow_instances_current_owner ON workflow_instances(current_owner_user_id);
CREATE INDEX idx_workflow_instances_status ON workflow_instances(workflow_status);
CREATE INDEX idx_workflow_instances_step1 ON workflow_instances(step1_complete);
CREATE INDEX idx_workflow_instances_step2 ON workflow_instances(step2_complete);
CREATE INDEX idx_workflow_instances_step3 ON workflow_instances(step3_complete);
CREATE INDEX idx_workflow_instances_step4 ON workflow_instances(step4_complete);
CREATE INDEX idx_workflow_instances_step5 ON workflow_instances(step5_complete);
CREATE INDEX idx_staging_coordinator_year_month ON staging_coordinator_tasks(year_month);
CREATE INDEX idx_staging_coordinator_activity_date ON staging_coordinator_tasks(activity_date);
CREATE INDEX idx_staging_provider_year_month ON staging_provider_tasks(year_month);
CREATE INDEX idx_staging_provider_activity_date ON staging_provider_tasks(activity_date);
CREATE INDEX idx_patients_patient_id ON "patients_old"(patient_id);
CREATE INDEX idx_patient_assignments_patient_id ON "patient_assignments_old"(patient_id);
CREATE TRIGGER update_users_timestamp 
    AFTER UPDATE ON "users"
    BEGIN
        UPDATE "users" SET updated_date = datetime('now') WHERE user_id = NEW.user_id;
    END;
CREATE TRIGGER update_providers_timestamp 
    AFTER UPDATE ON "providers"
    BEGIN
        UPDATE "providers" SET updated_date = datetime('now') WHERE provider_id = NEW.provider_id;
    END;
CREATE TRIGGER update_coordinators_timestamp 
    AFTER UPDATE ON "coordinators"
    BEGIN
        UPDATE "coordinators" SET updated_date = datetime('now') WHERE coordinator_id = NEW.coordinator_id;
    END;
CREATE TRIGGER trigger_prod_task_definitions_updated_at
AFTER UPDATE ON "coordinator_task_definitions"
FOR EACH ROW
BEGIN
    UPDATE "coordinator_task_definitions"
    SET updated_at = CURRENT_TIMESTAMP
    WHERE task_definition_id = OLD.task_definition_id;
END;
CREATE TRIGGER trigger_workflow_instances_updated_at
AFTER UPDATE ON workflow_instances
FOR EACH ROW
BEGIN
    UPDATE workflow_instances
    SET updated_at = CURRENT_TIMESTAMP
    WHERE instance_id = OLD.instance_id;
END;
CREATE TRIGGER trigger_advance_workflow_onboarding_style
AFTER UPDATE ON workflow_instances
FOR EACH ROW
WHEN (
    -- Step 1 just completed
    (NEW.step1_complete = 1 AND OLD.step1_complete = 0) OR
    -- Step 2 just completed  
    (NEW.step2_complete = 1 AND OLD.step2_complete = 0) OR
    -- Step 3 just completed
    (NEW.step3_complete = 1 AND OLD.step3_complete = 0) OR
    -- Step 4 just completed
    (NEW.step4_complete = 1 AND OLD.step4_complete = 0) OR
    -- Step 5 just completed
    (NEW.step5_complete = 1 AND OLD.step5_complete = 0)
)
BEGIN
    UPDATE workflow_instances
    SET 
        current_step = CASE
            WHEN step1_complete = 0 THEN 1
            WHEN step2_complete = 0 THEN 2  
            WHEN step3_complete = 0 THEN 3
            WHEN step4_complete = 0 THEN 4
            WHEN step5_complete = 0 THEN 5
            WHEN step6_complete = 0 THEN 6
            ELSE 999  -- All steps complete
        END,
        current_owner_role = CASE
            WHEN step1_complete = 0 THEN (SELECT owner FROM workflow_steps WHERE template_id = NEW.template_id AND step_order = 1)
            WHEN step2_complete = 0 THEN (SELECT owner FROM workflow_steps WHERE template_id = NEW.template_id AND step_order = 2)
            WHEN step3_complete = 0 THEN (SELECT owner FROM workflow_steps WHERE template_id = NEW.template_id AND step_order = 3)
            WHEN step4_complete = 0 THEN (SELECT owner FROM workflow_steps WHERE template_id = NEW.template_id AND step_order = 4)
            WHEN step5_complete = 0 THEN (SELECT owner FROM workflow_steps WHERE template_id = NEW.template_id AND step_order = 5)
            WHEN step6_complete = 0 THEN (SELECT owner FROM workflow_steps WHERE template_id = NEW.template_id AND step_order = 6)
            ELSE NULL
        END,
        workflow_status = CASE
            WHEN step1_complete = 1 AND step2_complete = 1 AND step3_complete = 1 AND step4_complete = 1 AND step5_complete = 1 THEN 'Completed'
            ELSE 'Active'
        END,
        completed_at = CASE
            WHEN step1_complete = 1 AND step2_complete = 1 AND step3_complete = 1 AND step4_complete = 1 AND step5_complete = 1 THEN CURRENT_TIMESTAMP
            ELSE NULL
        END,
        updated_at = CURRENT_TIMESTAMP
    WHERE instance_id = NEW.instance_id;
END;
CREATE TABLE patient_panel (
    patient_id TEXT,
    first_name TEXT,
    last_name TEXT,
    date_of_birth TEXT,
    gender TEXT,
    phone_primary TEXT,
    phone_secondary TEXT,
    email TEXT,
    address_street TEXT,
    address_city TEXT,
    address_state TEXT,
    address_zip TEXT,
    emergency_contact_name TEXT,
    emergency_contact_phone TEXT,
    emergency_contact_relationship TEXT,
    insurance_primary TEXT,
    insurance_policy_number TEXT,
    insurance_secondary TEXT,
    medical_record_number TEXT,
    enrollment_date TEXT,
    discharge_date TEXT,
    notes TEXT,
    created_date TEXT,
    updated_date TEXT,
    created_by TEXT,
    updated_by TEXT,
    current_facility_id INT,
    hypertension INT,
    mental_health_concerns INT,
    dementia INT,
    last_annual_wellness_visit TEXT,
    last_first_dob TEXT,
    status TEXT,
    medical_records_requested INTEGER,
    referral_documents_received INTEGER,
    insurance_cards_received INTEGER,
    emed_signature_received INTEGER,
    last_visit_date TEXT,
    facility TEXT,
    assigned_coordinator_id INT,
    er_count_1yr INT,
    hospitalization_count_1yr INT,
    clinical_biometric TEXT,
    chronic_conditions_provider TEXT,
    cancer_history TEXT,
    subjective_risk_level TEXT,
    provider_mh_schizophrenia INTEGER,
    provider_mh_depression INTEGER,
    provider_mh_anxiety INTEGER,
    provider_mh_stress INTEGER,
    provider_mh_adhd INTEGER,
    provider_mh_bipolar INTEGER,
    provider_mh_suicidal INTEGER,
    active_specialists TEXT,
    code_status TEXT,
    cognitive_function TEXT,
    functional_status TEXT,
    goals_of_care TEXT,
    active_concerns TEXT,
    initial_tv_completed_date TEXT,
    initial_tv_notes TEXT,
    initial_tv_provider TEXT,
    provider_id INTEGER,
    provider_name TEXT,
    coordinator_id INTEGER,
    coordinator_name TEXT,
    stage1_complete INTEGER,
    stage2_complete INTEGER,
    initial_tv_completed INTEGER,
    source_table TEXT,
    source_column TEXT,
    last_visit_provider_id INT,
    last_visit_provider_name TEXT,
    last_visit_service_type TEXT,
    region_id TEXT
, eligibility_status TEXT DEFAULT NULL, eligibility_notes TEXT DEFAULT NULL, eligibility_verified INTEGER DEFAULT 0, emed_chart_created INTEGER DEFAULT 0, chart_id TEXT DEFAULT NULL, facility_confirmed INTEGER DEFAULT 0, chart_notes TEXT DEFAULT NULL, intake_call_completed INTEGER DEFAULT 0, intake_notes TEXT DEFAULT NULL, task_date DATE DEFAULT NULL, goc_value TEXT DEFAULT NULL);
CREATE TABLE IF NOT EXISTS "SOURCE_PSL_TASKS_2025_09" (
"1" REAL,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "Year" REAL,
  "Month" REAL,
  "Billed Date  Notes" TEXT,
  "Paid by Patient" TEXT
);
CREATE TABLE IF NOT EXISTS "SOURCE_PROVIDER_TASKS_HISTORY" (
"1" TEXT,
  "Prov" TEXT,
  "Coding" TEXT,
  "Patient Last, First DOB" TEXT,
  "DOS" TEXT,
  "Service" TEXT,
  "Minutes" TEXT,
  "Hospice" TEXT,
  "Notes" TEXT,
  "WC Size  (sqcm)" TEXT,
  "WC Diagnosis (HH-OK to free type)" TEXT,
  "Graft Info" TEXT,
  "Wound#" REAL,
  "Session#" REAL,
  "Multiple Grafts" TEXT,
  "Year" TEXT,
  "Month" TEXT,
  "Billed Date  Notes" TEXT,
  "Paid by Patient" TEXT
);
CREATE TABLE IF NOT EXISTS "old_coordinator_tasks" (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    patient_id TEXT,
    coordinator_id TEXT,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT
);
CREATE TABLE provider_tasks (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_01 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_01 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_02 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_02 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_03 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_03 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_04 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_04 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_05 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_05 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_06 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_06 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_07 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_07 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_08 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_08 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE provider_tasks_2025_09 (
    provider_task_id INT,
    task_id INT,
    provider_id INT,
    provider_name TEXT,
    patient_name TEXT,
    user_id INT,
    patient_id TEXT,
    status TEXT,
    notes TEXT,
    minutes_of_service INT,
    billing_code_id INT,
    created_date NUM,
    updated_date NUM,
    task_date NUM,
    month INT,
    year INT,
    billing_code TEXT,
    billing_code_description TEXT,
    task_description TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE TABLE coordinator_tasks_2025_09 (
    coordinator_id TEXT,
    patient_id TEXT,
    task_date TEXT,
    duration_minutes INT,
    task_type TEXT,
    notes TEXT,
    source_system TEXT,
    imported_at TEXT
);
CREATE INDEX idx_patient_panel_task_date ON patient_panel(task_date);
CREATE TABLE IF NOT EXISTS "patients" (
	"patient_id"	TEXT,
	"region_id"	INT,
	"first_name"	TEXT,
	"last_name"	NUMERIC,
	"date_of_birth"	TEXT,
	"gender"	TEXT,
	"phone_primary"	TEXT,
	"phone_secondary"	TEXT,
	"email"	TEXT,
	"address_street"	TEXT,
	"address_city"	TEXT,
	"address_state"	TEXT,
	"address_zip"	TEXT,
	"emergency_contact_name"	TEXT,
	"emergency_contact_phone"	TEXT,
	"emergency_contact_relationship"	TEXT,
	"insurance_primary"	TEXT,
	"insurance_policy_number"	TEXT,
	"insurance_secondary"	TEXT,
	"medical_record_number"	TEXT,
	"enrollment_date"	TEXT,
	"discharge_date"	TEXT,
	"notes"	TEXT,
	"created_date"	TEXT,
	"updated_date"	TEXT,
	"created_by"	INT,
	"updated_by"	INT,
	"current_facility_id"	INT,
	"hypertension"	INT,
	"mental_health_concerns"	INT,
	"dementia"	INT,
	"last_annual_wellness_visit"	TEXT,
	"last_first_dob"	TEXT,
	"status"	TEXT,
	"medical_records_requested"	BOOLEAN DEFAULT FALSE,
	"referral_documents_received"	BOOLEAN DEFAULT FALSE,
	"insurance_cards_received"	BOOLEAN DEFAULT FALSE,
	"emed_signature_received"	BOOLEAN DEFAULT FALSE,
	"last_visit_date"	DATE,
	"facility"	TEXT,
	"er_count_1yr"	INTEGER,
	"hospitalization_count_1yr"	INTEGER,
	"clinical_biometric"	TEXT,
	"chronic_conditions_provider"	TEXT,
	"cancer_history"	TEXT,
	"subjective_risk_level"	TEXT,
	"provider_mh_schizophrenia"	BOOLEAN DEFAULT FALSE,
	"provider_mh_depression"	BOOLEAN DEFAULT FALSE,
	"provider_mh_anxiety"	BOOLEAN DEFAULT FALSE,
	"provider_mh_stress"	BOOLEAN DEFAULT FALSE,
	"provider_mh_adhd"	BOOLEAN DEFAULT FALSE,
	"provider_mh_bipolar"	BOOLEAN DEFAULT FALSE,
	"provider_mh_suicidal"	BOOLEAN DEFAULT FALSE,
	"active_specialists"	TEXT,
	"code_status"	TEXT,
	"cognitive_function"	TEXT,
	"functional_status"	TEXT,
	"goals_of_care"	TEXT,
	"active_concerns"	TEXT,
	"initial_tv_completed_date"	TEXT,
	"initial_tv_notes"	TEXT,
	"service_type"	TEXT,
	"appointment_contact_name"	TEXT,
	"appointment_contact_phone"	TEXT,
	"appointment_contact_email"	TEXT,
	"medical_contact_name"	TEXT,
	"medical_contact_phone"	TEXT,
	"medical_contact_email"	TEXT,
	"primary_care_provider"	TEXT,
	"pcp_last_seen"	DATE,
	"active_specialist"	TEXT,
	"specialist_last_seen"	DATE,
	"chronic_conditions_onboarding"	TEXT,
	"mh_schizophrenia"	BOOLEAN DEFAULT FALSE,
	"mh_depression"	BOOLEAN DEFAULT FALSE,
	"mh_anxiety"	BOOLEAN DEFAULT FALSE,
	"mh_stress"	BOOLEAN DEFAULT FALSE,
	"mh_adhd"	BOOLEAN DEFAULT FALSE,
	"mh_bipolar"	BOOLEAN DEFAULT FALSE,
	"mh_suicidal"	BOOLEAN DEFAULT FALSE,
	"tv_date"	DATE,
	"tv_time"	TIME,
	"tv_scheduled"	BOOLEAN DEFAULT FALSE,
	"patient_notified"	BOOLEAN DEFAULT FALSE,
	"initial_tv_provider"	TEXT,
	"assigned_coordinator_id"	INTEGER,
	"eligibility_status"	TEXT DEFAULT NULL,
	"eligibility_notes"	TEXT DEFAULT NULL,
	"eligibility_verified"	BOOLEAN DEFAULT FALSE,
	"emed_chart_created"	BOOLEAN DEFAULT FALSE,
	"chart_id"	TEXT DEFAULT NULL,
	"facility_confirmed"	BOOLEAN DEFAULT FALSE,
	"chart_notes"	TEXT DEFAULT NULL,
	"intake_call_completed"	BOOLEAN DEFAULT FALSE,
	"intake_notes"	TEXT DEFAULT NULL,
	"goc_value"	TEXT DEFAULT NULL);
CREATE TABLE dashboard_patient_county_map (
    map_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    county TEXT NOT NULL,
    state TEXT NOT NULL,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
CREATE INDEX idx_patient_county_map_patient ON dashboard_patient_county_map(patient_id);
CREATE INDEX idx_patient_county_map_county ON dashboard_patient_county_map(county, state);
CREATE TABLE dashboard_patient_zip_map (
    map_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    zip_code TEXT NOT NULL,
    city TEXT,
    state TEXT,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_date TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);
CREATE INDEX idx_patient_zip_map_patient ON dashboard_patient_zip_map(patient_id);
CREATE INDEX idx_patient_zip_map_zip ON dashboard_patient_zip_map(zip_code);
CREATE TABLE test_coordinator_fk(
  coordinator_task_id INT,
  task_id INT,
  patient_id TEXT,
  coordinator_id TEXT,
  task_date TEXT,
  duration_minutes INT,
  task_type TEXT,
  notes TEXT
);
CREATE TABLE coordinator_tasks (
    coordinator_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER,
    patient_id TEXT,
    coordinator_id TEXT,
    task_date TEXT,
    duration_minutes INTEGER,
    task_type TEXT,
    notes TEXT
);
CREATE TABLE patient_visits (
    patient_id TEXT PRIMARY KEY,
    last_visit_date TEXT,
    service_type TEXT
);
