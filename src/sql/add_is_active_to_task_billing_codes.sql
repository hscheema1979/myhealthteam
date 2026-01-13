-- Add is_active column to task_billing_codes table
-- Migration for VPS2 production database
-- Date: 2026-01-13

ALTER TABLE task_billing_codes ADD COLUMN is_active INTEGER DEFAULT 1;
