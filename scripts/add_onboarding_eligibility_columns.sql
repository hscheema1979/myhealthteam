-- Migration: Add eligibility_status, eligibility_notes, eligibility_verified to onboarding_patients
ALTER TABLE onboarding_patients
ADD COLUMN eligibility_status TEXT;
ALTER TABLE onboarding_patients
ADD COLUMN eligibility_notes TEXT;
ALTER TABLE onboarding_patients
ADD COLUMN eligibility_verified BOOLEAN DEFAULT FALSE;