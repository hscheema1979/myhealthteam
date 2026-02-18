-- Add Telehealth visit billing codes
-- These codes support Telehealth-Video and Telehealth-Audio location types

-- Telehealth-Video codes
INSERT INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, effective_date, is_active, note)
VALUES
('NEW TELEVISIT VISIT', 'Telehealth', 'Telehealth-Video', 'New', 40, 60, '99204', 'New patient telehealth visit - 45 min', '2026-01-01', 1, NULL),
('FOLLOW UP TELE VISIT', 'Telehealth', 'Telehealth-Video', 'Follow Up', 30, 40, '99214', 'Established patient telehealth visit - 30 min', '2026-01-01', 1, NULL),
('ACUTE TELE VISIT', 'Telehealth', 'Telehealth-Video', 'Acute', 15, 30, '99213', 'Acute telehealth visit - 15 min', '2026-01-01', 1, NULL),
('Cog A+B Tele', 'Telehealth', 'Telehealth-Video', 'Cognitive', 60, 100, '96138+96132', 'Cognitive assessment and testing - Telehealth', '2026-01-01', 1, NULL),
('TCM-7d Tele', 'Telehealth', 'Telehealth-Video', 'TCM-7', 30, 60, '99496', 'Transitional Care Management 7-day - Telehealth', '2026-01-01', 1, NULL),
('TCM-14d Tele', 'Telehealth', 'Telehealth-Video', 'TCM-14', 60, 120, '99495', 'Transitional Care Management 14-day - Telehealth', '2026-01-01', 1, NULL);

-- Telehealth-Audio codes (Phone-only visits)
INSERT INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, effective_date, is_active, note)
VALUES
('NEW TELEVISIT VISIT', 'Telehealth', 'Telehealth-Audio', 'New', 40, 60, '99204', 'New patient telehealth visit - 45 min', '2026-01-01', 1, NULL),
('FOLLOW UP TELE VISIT', 'Telehealth', 'Telehealth-Audio', 'Follow Up', 30, 40, '99214', 'Established patient telehealth visit - 30 min', '2026-01-01', 1, NULL);
