-- Data migration for workflow_template_roles
-- Maps workflow templates to authorized roles
-- Care Management workflows (CC=36, CM=40, LC=37, CPM=38, ADMIN=34, DATA ENTRY=39)
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (1, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (2, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (3, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (4, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (5, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (6, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (7, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (8, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (9, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (10, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (11, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (12, 36);
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (13, 36);
-- Onboarding workflow (OT=35)
INSERT INTO workflow_template_roles (workflow_template_id, role_id)
VALUES (14, 35);
-- Add additional role mappings as needed for management roles, e.g.:
-- INSERT INTO workflow_template_roles (workflow_template_id, role_id) VALUES (1,40); -- CM
-- INSERT INTO workflow_template_roles (workflow_template_id, role_id) VALUES (1,37); -- LC
-- etc.