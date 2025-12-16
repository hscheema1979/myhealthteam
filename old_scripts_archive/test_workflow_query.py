#!/usr/bin/env python3

import sqlite3
import pandas as pd

# Test the SQL query directly
conn = sqlite3.connect('production.db')

# Test the corrected query
query = """
SELECT
    wi.instance_id,
    wi.template_id as workflow_id,
    wi.template_name as workflow_name,
    wi.patient_id,
    wi.patient_name,
    wi.coordinator_id as assigned_user_id,
    wi.coordinator_name as assigned_to,
    wi.workflow_status as status,
    wi.current_step,
    wi.current_owner_name as current_owner,
    wi.created_at as created_date,
    wi.updated_at as updated_date,
    CASE 
        WHEN wi.workflow_status = 'Active' THEN 'active'
        WHEN wi.workflow_status = 'Pending' THEN 'pending'
        WHEN wi.workflow_status = 'Complete' THEN 'completed'
        ELSE 'unknown'
    END as status_normalized
FROM workflow_instances wi
WHERE wi.workflow_status IN ('Active', 'Pending')
ORDER BY wi.updated_at DESC
"""

try:
    workflows_df = pd.read_sql_query(query, conn)
    print(f"Query successful! Found {len(workflows_df)} workflows")
    print("\nSample data:")
    print(workflows_df.head())
except Exception as e:
    print(f"Query failed: {e}")
finally:
    conn.close()