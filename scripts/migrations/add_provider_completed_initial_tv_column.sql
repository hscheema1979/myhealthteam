-- Migration: Add provider_completed_initial_tv column to onboarding_patients table
-- Date: 2025-01-27
-- Purpose: Track when provider has completed the initial TV visit automatically

-- Add provider completion tracking column
ALTER TABLE onboarding_patients ADD COLUMN provider_completed_initial_tv BOOLEAN DEFAULT FALSE;

-- Verify the column was added successfully
.schema onboarding_patients