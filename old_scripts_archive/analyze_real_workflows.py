#!/usr/bin/env python3

import sqlite3
import pandas as pd

conn = sqlite3.connect('production.db')

# Get real workflow data structure and content
print("=== REAL WORKFLOW DATA ANALYSIS ===")

# Check workflow instances
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM workflow_instances WHERE workflow_status IN ('Active', 'Pending')")
active_count = cursor.fetchone()[0]
print(f"Active/Pending workflows: {active_count}")

# Get sample of real workflows
cursor.execute("""
    SELECT 
        instance_id,
        template_name,
        patient_id,
        patient_name,
        coordinator_id,
        coordinator_name,
        workflow_status,
        current_step,
        current_owner_name,
        created_at,
        updated_at
    FROM workflow_instances 
    WHERE workflow_status IN ('Active', 'Pending')
    ORDER BY updated_at DESC
    LIMIT 10
""")
workflows = cursor.fetchall()

print("\nSample real workflows:")
for wf in workflows:
    print(f"  ID: {wf[0]} | Template: {wf[1]} | Patient: {wf[3]} | Coordinator: {wf[5]} | Status: {wf[6]} | Step: {wf[7]}")

# Get coordinator list for reassignment options
cursor.execute("""
    SELECT u.user_id, u.full_name, u.email 
    FROM users u 
    JOIN user_roles ur ON u.user_id = ur.user_id 
    WHERE ur.role_id = 36 
    AND u.status = 'active'
    ORDER BY u.full_name
""")
coordinators = cursor.fetchall()

print(f"\nAvailable coordinators for reassignment: {len(coordinators)}")
for coord in coordinators:
    print(f"  ID: {coord[0]} | Name: {coord[1]} | Email: {coord[2]}")

# Check workflow templates
cursor.execute("SELECT template_id, template_name FROM workflow_templates ORDER BY template_name")
templates = cursor.fetchall()
print(f"\nWorkflow templates: {len(templates)}")
for template in templates:
    print(f"  ID: {template[0]} | Name: {template[1]}")

conn.close()

print("\n=== RECOMMENDATIONS FOR REASSIGNMENT INTERFACE ===")
print("1. Show real workflows with: ID, Template, Patient, Current Coordinator, Status, Step, Last Updated")
print("2. Allow multi-select for bulk reassignment")
print("3. Provide coordinator dropdown for target assignment")
print("4. Show confirmation of what will be changed")
print("5. Include audit logging for all reassignments")