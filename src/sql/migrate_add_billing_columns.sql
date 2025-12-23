-- Migration: Add missing billing_company and billed_by columns to provider_task_billing_status
-- This script adds columns that were defined in the schema but not yet in the production database
-- Check and add billing_company column if it doesn't exist
-- Note: SQLite doesn't have direct IF NOT EXISTS for ALTER TABLE,
-- so we'll attempt the addition and continue on error
ALTER TABLE provider_task_billing_status
ADD COLUMN billing_company TEXT;
ALTER TABLE provider_task_billing_status
ADD COLUMN billed_by INTEGER;
-- Create index for billing_company for faster queries
CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_billing_company ON provider_task_billing_status(billing_company);
-- Create index for billed_by for audit trail queries
CREATE INDEX IF NOT EXISTS idx_provider_task_billing_status_billed_by ON provider_task_billing_status(billed_by);
-- Verify the columns were added
PRAGMA table_info(provider_task_billing_status);