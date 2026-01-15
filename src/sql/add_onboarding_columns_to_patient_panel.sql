-- Add missing onboarding columns to patient_panel table for ZMO
-- These columns exist in onboarding_patients but were missing from patient_panel

ALTER TABLE patient_panel ADD COLUMN tv_date DATE;
ALTER TABLE patient_panel ADD COLUMN tv_time TIME;
ALTER TABLE patient_panel ADD COLUMN tv_scheduled BOOLEAN DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN patient_notified BOOLEAN DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN initial_tv_completed BOOLEAN DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN initial_tv_completed_date TEXT;
ALTER TABLE patient_panel ADD COLUMN initial_tv_provider TEXT;
ALTER TABLE patient_panel ADD COLUMN initial_tv_notes TEXT;
ALTER TABLE patient_panel ADD COLUMN provider_completed_initial_tv BOOLEAN DEFAULT 0;

ALTER TABLE patient_panel ADD COLUMN eligibility_status TEXT;
ALTER TABLE patient_panel ADD COLUMN eligibility_notes TEXT;
ALTER TABLE patient_panel ADD COLUMN eligibility_verified BOOLEAN DEFAULT 0;

ALTER TABLE patient_panel ADD COLUMN emed_chart_created BOOLEAN DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN chart_id TEXT;
ALTER TABLE patient_panel ADD COLUMN facility_confirmed BOOLEAN DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN chart_notes TEXT;

ALTER TABLE patient_panel ADD COLUMN intake_call_completed BOOLEAN DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN intake_notes TEXT;

ALTER TABLE patient_panel ADD COLUMN facility_assignment TEXT;
ALTER TABLE patient_panel ADD COLUMN medical_records_requested BOOLEAN DEFAULT 0;
ALTER TABLE patient_panel ADD COLUMN emed_signature_received BOOLEAN DEFAULT 0;

ALTER TABLE patient_panel ADD COLUMN appointment_contact_email TEXT;
ALTER TABLE patient_panel ADD COLUMN medical_contact_email TEXT;

ALTER TABLE patient_panel ADD COLUMN facility_nurse_name TEXT;
ALTER TABLE patient_panel ADD COLUMN facility_nurse_phone TEXT;
ALTER TABLE patient_panel ADD COLUMN facility_nurse_email TEXT;

ALTER TABLE patient_panel ADD COLUMN active_specialist TEXT;
ALTER TABLE patient_panel ADD COLUMN specialist_last_seen TEXT;
ALTER TABLE patient_panel ADD COLUMN chronic_conditions_onboarding TEXT;
ALTER TABLE patient_panel ADD COLUMN primary_care_provider TEXT;
ALTER TABLE patient_panel ADD COLUMN pcp_last_seen TEXT;
