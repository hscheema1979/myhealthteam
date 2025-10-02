#!/usr/bin/env python3
"""
Test script to validate billing dashboard SQL queries work with actual schema
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import get_db_connection

def test_weekly_billing_summary():
    """Test the weekly billing summary query"""
    print("Testing weekly billing summary query...")
    
    conn = get_db_connection()
    
    query = """
    SELECT 
        report_id,
        billing_week,
        week_start_date,
        week_end_date,
        total_tasks,
        total_billed_tasks,
        (total_tasks - total_billed_tasks) as total_unbilled_tasks,
        ROUND((total_billed_tasks * 100.0 / total_tasks), 2) as billing_percentage,
        report_status
    FROM weekly_billing_reports
    ORDER BY billing_week DESC
    LIMIT 10
    """
    
    try:
        result = conn.execute(query).fetchall()
        print(f"✓ Weekly billing summary query successful - {len(result)} rows returned")
        if result:
            print(f"  Sample row: {dict(result[0])}")
    except Exception as e:
        print(f"✗ Weekly billing summary query failed: {e}")
    finally:
        conn.close()

def test_current_week_summary():
    """Test the current week summary query"""
    print("\nTesting current week summary query...")
    
    conn = get_db_connection()
    
    query = """
    SELECT 
        COUNT(*) as total_tasks,
        SUM(CASE WHEN is_billed = 1 THEN 1 ELSE 0 END) as billed_tasks,
        SUM(CASE WHEN billing_status = 'Not Billable' THEN 1 ELSE 0 END) as not_billable_tasks,
        SUM(CASE WHEN billing_status = 'Requires Attention' THEN 1 ELSE 0 END) as attention_tasks,
        SUM(CASE WHEN is_carried_over = 1 THEN 1 ELSE 0 END) as carryover_tasks
    FROM provider_task_billing_status
    WHERE billing_week = (
        SELECT MAX(billing_week) FROM provider_task_billing_status
    )
    """
    
    try:
        result = conn.execute(query).fetchone()
        print(f"✓ Current week summary query successful")
        if result:
            print(f"  Result: {dict(result)}")
    except Exception as e:
        print(f"✗ Current week summary query failed: {e}")
    finally:
        conn.close()

def test_provider_billing_status():
    """Test the provider billing status query"""
    print("\nTesting provider billing status query...")
    
    conn = get_db_connection()
    
    # Test with a simple version first
    query = """
    SELECT 
        ptbs.provider_task_id,
        ptbs.billing_week,
        ptbs.is_billed,
        ptbs.billing_status,
        ptbs.is_carried_over,
        ptbs.original_billing_week
    FROM provider_task_billing_status ptbs
    LIMIT 5
    """
    
    try:
        result = conn.execute(query).fetchall()
        print(f"✓ Provider billing status query successful - {len(result)} rows returned")
        if result:
            print(f"  Sample row: {dict(result[0])}")
    except Exception as e:
        print(f"✗ Provider billing status query failed: {e}")
    finally:
        conn.close()

def test_table_existence():
    """Test that required tables exist"""
    print("\nTesting table existence...")
    
    conn = get_db_connection()
    
    tables_to_check = [
        'weekly_billing_reports',
        'provider_task_billing_status',
        'provider_tasks_2024_01',
        'provider_tasks_2024_02',
        'provider_tasks_2024_03'
    ]
    
    for table in tables_to_check:
        try:
            result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            count = result[0] if result else 0
            print(f"✓ Table {table} exists with {count} rows")
        except Exception as e:
            print(f"✗ Table {table} check failed: {e}")
    
    conn.close()

if __name__ == "__main__":
    print("=== Billing Dashboard SQL Validation ===")
    test_table_existence()
    test_weekly_billing_summary()
    test_current_week_summary()
    test_provider_billing_status()
    print("\n=== Validation Complete ===")