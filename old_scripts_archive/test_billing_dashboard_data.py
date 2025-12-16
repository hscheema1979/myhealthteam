#!/usr/bin/env python3
"""
Test script to verify the billing dashboard data shows individual tasks with billing status
"""

import sqlite3
import pandas as pd

def test_billing_dashboard_data():
    """Test the billing dashboard data structure"""
    conn = sqlite3.connect('production.db')
    
    # Test the query that the dashboard uses
    query = """
    SELECT 
        provider_name,
        patient_name,
        task_date,
        task_description,
        minutes_of_service,
        billing_code,
        billing_status,
        is_billed,
        is_paid,
        billing_week,
        original_billing_week
    FROM provider_tasks
    WHERE billing_week = '2025-38'  -- Recent week
    AND task_date IS NOT NULL
    ORDER BY provider_name, task_date
    LIMIT 10
    """
    
    print("=== Testing Weekly Billing Dashboard Data ===")
    print(f"Query: {query}")
    print()
    
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        print("No data found for week 2025-38, trying 2025-37...")
        query = query.replace("2025-38", "2025-37")
        df = pd.read_sql_query(query, conn)
    
    if not df.empty:
        print(f"Found {len(df)} tasks for the selected week")
        print("\nSample tasks with billing status:")
        print(df.to_string(index=False))
        
        print(f"\nBilling Status Summary:")
        status_summary = df['billing_status'].value_counts()
        print(status_summary)
        
        print(f"\nBilled Status Summary:")
        billed_summary = df['is_billed'].value_counts()
        print(f"Not Billed (0): {billed_summary.get(0, 0)}")
        print(f"Billed (1): {billed_summary.get(1, 0)}")
        
    else:
        print("No data found. Let's check available weeks...")
        weeks_query = """
        SELECT billing_week, COUNT(*) as task_count
        FROM provider_tasks 
        WHERE billing_week IS NOT NULL
        GROUP BY billing_week 
        ORDER BY billing_week DESC 
        LIMIT 5
        """
        weeks_df = pd.read_sql_query(weeks_query, conn)
        print("Available weeks:")
        print(weeks_df.to_string(index=False))
    
    # Check schema
    print(f"\n=== Provider Tasks Table Schema ===")
    schema_query = "PRAGMA table_info(provider_tasks)"
    schema_df = pd.read_sql_query(schema_query, conn)
    billing_columns = schema_df[schema_df['name'].str.contains('billing|billed|paid', case=False, na=False)]
    print("Billing-related columns:")
    print(billing_columns[['name', 'type', 'dflt_value']].to_string(index=False))
    
    conn.close()

if __name__ == "__main__":
    test_billing_dashboard_data()