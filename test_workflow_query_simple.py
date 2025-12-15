#!/usr/bin/env python3

import sqlite3
import pandas as pd

print("=== Testing Workflow Reassignment Query ===")

conn = sqlite3.connect('production.db')

# Test the exact query from the component
query = """
SELECT 
    wi.instance_id,
    wi.template_name as workflow_type,
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
        WHEN wi.workflow_status = 'Active' THEN 'Active'
        WHEN wi.workflow_status = 'Pending' THEN 'Pending'
        ELSE wi.workflow_status
    END as display_status
FROM workflow_instances wi
WHERE wi.workflow_status IN ('Active', 'Pending')
ORDER BY wi.updated_at DESC
"""

try:
    df = pd.read_sql_query(query, conn)
    print(f"Query successful! Found {len(df)} workflows")
    print("\nFirst 5 workflows:")
    print(df[['instance_id', 'workflow_type', 'patient_name', 'assigned_to', 'display_status']].head())
    
    # Test coordinator lookup
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.user_id, u.full_name 
        FROM users u 
        JOIN user_roles ur ON u.user_id = ur.user_id 
        WHERE ur.role_id = 36 
        AND u.status = 'active'
        ORDER BY u.full_name
    """)
    coordinators = cursor.fetchall()
    print(f"\nFound {len(coordinators)} active coordinators")
    for coord in coordinators[:5]:
        print(f"  ID: {coord[0]} | Name: {coord[1]}")
        
except Exception as e:
    print(f"Query failed: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    conn.close()