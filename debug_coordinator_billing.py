#!/usr/bin/env python3
"""
Debug script to investigate the coordinator billing names issue
for October and November 2025
"""

import sqlite3
import pandas as pd

def main():
    conn = sqlite3.connect('production.db')
    
    print("=== COORDINATOR BILLING ISSUE INVESTIGATION ===")
    print("Checking why staff names show as numbers instead of names in Oct/Nov 2025\n")
    
    # Check coordinator_tasks_2025_10 data
    print("1. Checking coordinator_tasks_2025_10 data:")
    try:
        query = """
        SELECT coordinator_id, COUNT(*) as task_count, SUM(duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_10 
        GROUP BY coordinator_id
        ORDER BY task_count DESC
        """
        df = pd.read_sql_query(query, conn)
        print(df)
        print(f"Total tasks in Oct 2025: {df['task_count'].sum()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check coordinator_tasks_2025_11 data
    print("\n2. Checking coordinator_tasks_2025_11 data:")
    try:
        query = """
        SELECT coordinator_id, COUNT(*) as task_count, SUM(duration_minutes) as total_minutes
        FROM coordinator_tasks_2025_11 
        GROUP BY coordinator_id
        ORDER BY task_count DESC
        """
        df = pd.read_sql_query(query, conn)
        print(df)
        print(f"Total tasks in Nov 2025: {df['task_count'].sum()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check users table for coordinator IDs
    print("\n3. Checking users table for coordinator IDs (14, 17, 20, 5):")
    try:
        query = """
        SELECT user_id, first_name, last_name, email, role_id
        FROM users 
        WHERE user_id IN (5, 14, 17, 20)
        ORDER BY user_id
        """
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error: {e}")
    
    # Check staff_codes table
    print("\n4. All coordinator codes in staff_codes:")
    try:
        query = """
        SELECT coordinator_code, full_name
        FROM staff_codes
        ORDER BY coordinator_code
        """
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error: {e}")
    
    # Check if there are coordinator monthly billing tables
    print("\n5. Checking coordinator monthly billing tables:")
    try:
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'coordinator_monthly_billing%'
        ORDER BY name
        """
        tables = conn.execute(query).fetchall()
        print("Available coordinator_monthly_billing tables:")
        for table in tables:
            print(f"  {table[0]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Check if there are patient monthly billing tables for Oct/Nov
    print("\n6. Checking patient monthly billing tables for 2025:")
    try:
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'patient_monthly_billing_2025_%'
        ORDER BY name
        """
        tables = conn.execute(query).fetchall()
        print("Available patient_monthly_billing_2025 tables:")
        for table in tables:
            print(f"  {table[0]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Let's also check what's in a sample of coordinator_tasks_2025_10
    print("\n7. Sample data from coordinator_tasks_2025_10:")
    try:
        query = """
        SELECT coordinator_id, patient_id, task_date, duration_minutes, task_type, notes
        FROM coordinator_tasks_2025_10 
        LIMIT 10
        """
        df = pd.read_sql_query(query, conn)
        print(df)
    except Exception as e:
        print(f"Error: {e}")
    
    # Check the billing dashboard view/query logic
    print("\n8. Testing billing dashboard query logic:")
    try:
        # Try the monthly coordinator billing dashboard logic
        table_name = "patient_monthly_billing_2025_10"
        
        # Check if table exists
        check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name = ?
        """
        table_exists = conn.execute(check_query, (table_name,)).fetchone()
        
        if table_exists:
            print(f"Table {table_name} exists")
            
            # Get billing summary from pre-aggregated patient billing table
            query = f"""
            SELECT 
                billing_code,
                billing_code_description,
                COUNT(*) as patient_count,
                SUM(total_minutes) as total_minutes,
                ROUND(AVG(total_minutes), 1) as avg_minutes_per_patient
            FROM {table_name}
            GROUP BY billing_code, billing_code_description
            ORDER BY patient_count DESC, total_minutes DESC
            LIMIT 10
            """
            
            df = pd.read_sql_query(query, conn)
            print("Sample billing data:")
            print(df)
        else:
            print(f"Table {table_name} does not exist")
            
    except Exception as e:
        print(f"Error: {e}")
    
    conn.close()
    print("\n=== INVESTIGATION COMPLETE ===")

if __name__ == "__main__":
    main()