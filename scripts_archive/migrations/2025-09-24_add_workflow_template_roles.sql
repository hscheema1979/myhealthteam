-- Migration: Add workflow_template_roles join table for role-based workflow access
CREATE TABLE IF NOT EXISTS workflow_template_roles (
    workflow_template_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (workflow_template_id, role_id),
    FOREIGN KEY (workflow_template_id) REFERENCES workflow_templates(id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);
-- Example data migration (to be customized):
-- For each workflow, insert the correct role assignments. Example:
-- INSERT INTO workflow_template_roles (workflow_template_id, role_id)
-- SELECT id, 36 FROM workflow_templates WHERE template_name LIKE '%Care Management%';
-- INSERT INTO workflow_template_roles (workflow_template_id, role_id)
-- SELECT id, 35 FROM workflow_templates WHERE template_name LIKE '%Onboard%';
-- You must review and adjust these inserts to match your actual workflow/role mapping.