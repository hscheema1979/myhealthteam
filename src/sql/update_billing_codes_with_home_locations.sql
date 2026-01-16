-- Update billing codes with min/max minutes and add Home location for TCM and Cognitive
-- Run this on production.db

-- 1. Update min/max minutes for existing billing codes from reference data
UPDATE task_billing_codes SET min_minutes = 60, max_minutes = 80 WHERE billing_code = '99350';  -- Follow Up Home (60-70, 70-80)
UPDATE task_billing_codes SET min_minutes = 40, max_minutes = 60 WHERE billing_code = '99349';  -- Follow Up Home (40-50, 50-60)
UPDATE task_billing_codes SET min_minutes = 30, max_minutes = 40 WHERE billing_code = '99214';  -- Follow Up Office/Tele (30-40)
UPDATE task_billing_codes SET min_minutes = 40, max_minutes = 70 WHERE billing_code = '99215';  -- Follow Up Office (40-70)
UPDATE task_billing_codes SET min_minutes = 70, max_minutes = 90 WHERE billing_code = '99345';  -- New Home (70-90)
UPDATE task_billing_codes SET min_minutes = 40, max_minutes = 60 WHERE billing_code = '99204';  -- New Office/Tele (40-60)
UPDATE task_billing_codes SET min_minutes = 60, max_minutes = 80 WHERE billing_code = '99205';  -- New Office (60-80)

-- 2. Add Home location for TCM-7 (using same billing code 99496)
INSERT INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, effective_date, is_active)
VALUES
('TCM-7d Home', 'TCM-7', 'Home', 'TCM-7', NULL, NULL, '99496', 'Transitional Care Management 7-day - Home Visit', 100, '2026-01-01', 1);

-- 3. Add Home location for TCM-14 (using same billing code 99495)
INSERT INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, effective_date, is_active)
VALUES
('TCM-14d Home', 'TCM-14', 'Home', 'TCM-14', NULL, NULL, '99495', 'Transitional Care Management 14-day - Home Visit', 100, '2026-01-01', 1);

-- 4. Add Home location for Cognitive (using same billing code 96138+96132)
INSERT INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, effective_date, is_active)
VALUES
('Cog A+B Home', 'Cognitive', 'Home', 'Cognitive', NULL, NULL, '96138+96132', 'Cognitive assessment and testing - Home Visit', 100, '2026-01-01', 1);

-- 5. Add Telehealth location for Cognitive (if not exists - usually same as Office)
INSERT OR IGNORE INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, effective_date, is_active)
VALUES
('Cog A+B Tele', 'Cognitive', 'Telehealth', 'Cognitive', NULL, NULL, '96138+96132', 'Cognitive assessment and testing - Telehealth', 100, '2026-01-01', 1);

-- 6. Add Telehealth location for TCM-7 (if not exists)
INSERT OR IGNORE INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, effective_date, is_active)
VALUES
('TCM-7d Tele', 'TCM-7', 'Telehealth', 'TCM-7', NULL, NULL, '99496', 'Transitional Care Management 7-day - Telehealth', 100, '2026-01-01', 1);

-- 7. Add Telehealth location for TCM-14 (if not exists)
INSERT OR IGNORE INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, effective_date, is_active)
VALUES
('TCM-14d Tele', 'TCM-14', 'Telehealth', 'TCM-14', NULL, NULL, '99495', 'Transitional Care Management 14-day - Telehealth', 100, '2026-01-01', 1);
