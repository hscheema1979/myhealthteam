#!/usr/bin/env python3
"""
Test script for billing dashboard functions
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.dashboards.weekly_billing_dashboard import (
    get_provider_billing_details,
    update_task_billing_status,
    bulk_update_billing_status,
    get_tasks_requiring_attention,
    get_weekly_billing_summary,
    get_billing_weeks_list
)
from src.database import get_db_connection
import pandas as pd

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM provider_tasks")
        count = cursor.fetchone()[0]
        print(f"✓ Database connection successful. Total tasks: {count}")
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_get_billing_weeks():
    """Test getting billing weeks"""
    print("\nTesting get_billing_weeks_list...")
    try:
        weeks_df = get_billing_weeks_list()
        print(f"✓ Retrieved {len(weeks_df)} billing weeks")
        if not weeks_df.empty:
            print(f"  Sample weeks: {weeks_df['billing_week'].head(3).tolist()}")
        return True
    except Exception as e:
        print(f"✗ get_billing_weeks_list failed: {e}")
        return False

def test_get_provider_billing_details():
    """Test getting provider billing details"""
    print("\nTesting get_provider_billing_details...")
    try:
        # Get a sample week
        weeks_df = get_billing_weeks_list()
        if weeks_df.empty:
            print("✗ No billing weeks available for testing")
            return False
        
        sample_week = weeks_df.iloc[0]['billing_week']
        details_df = get_provider_billing_details(sample_week)
        
        print(f"✓ Retrieved {len(details_df)} tasks for week {sample_week}")
        
        # Check if provider_paid column exists
        if 'provider_paid' in details_df.columns:
            print("✓ provider_paid column is present")
        else:
            print("✗ provider_paid column is missing")
            return False
        
        # Check other required columns
        required_columns = ['provider_task_id', 'provider_name', 'patient_name', 
                          'billing_status', 'is_billed', 'is_paid']
        missing_columns = [col for col in required_columns if col not in details_df.columns]
        
        if missing_columns:
            print(f"✗ Missing columns: {missing_columns}")
            return False
        else:
            print("✓ All required columns are present")
        
        return True
    except Exception as e:
        print(f"✗ get_provider_billing_details failed: {e}")
        return False

def test_update_task_billing_status():
    """Test updating task billing status"""
    print("\nTesting update_task_billing_status...")
    try:
        # Get a sample task
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT provider_task_id, billing_status, is_billed 
            FROM provider_tasks 
            WHERE provider_task_id IS NOT NULL 
            LIMIT 1
        """)
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print("✗ No tasks available for testing")
            return False
        
        task_id, current_status, current_billed = result
        print(f"  Testing with task_id: {task_id}")
        print(f"  Current status: {current_status}, is_billed: {current_billed}")
        
        # Test updating provider_paid status
        success, message = update_task_billing_status(task_id, 'provider_paid', 1, 'Test update')
        
        if success:
            print(f"✓ Status update successful: {message}")
            
            # Verify the update
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT provider_paid, billing_notes 
                FROM provider_tasks 
                WHERE provider_task_id = ?
            """, (task_id,))
            updated_result = cursor.fetchone()
            conn.close()
            
            if updated_result and updated_result[0] == 1:
                print("✓ Update verified in database")
                
                # Reset the value
                update_task_billing_status(task_id, 'provider_paid', 0, 'Reset after test')
                print("✓ Test value reset")
                return True
            else:
                print("✗ Update not reflected in database")
                return False
        else:
            print(f"✗ Status update failed: {message}")
            return False
            
    except Exception as e:
        print(f"✗ update_task_billing_status failed: {e}")
        return False

def test_get_tasks_requiring_attention():
    """Test getting tasks requiring attention"""
    print("\nTesting get_tasks_requiring_attention...")
    try:
        attention_df = get_tasks_requiring_attention()
        print(f"✓ Retrieved {len(attention_df)} tasks requiring attention")
        
        if not attention_df.empty:
            required_columns = ['provider_task_id', 'provider_name', 'patient_name', 
                              'billing_status']
            missing_columns = [col for col in required_columns if col not in attention_df.columns]
            
            if missing_columns:
                print(f"✗ Missing columns in attention tasks: {missing_columns}")
                return False
            else:
                print("✓ All required columns present in attention tasks")
        
        return True
    except Exception as e:
        print(f"✗ get_tasks_requiring_attention failed: {e}")
        return False

def test_weekly_billing_summary():
    """Test getting weekly billing summary"""
    print("\nTesting get_weekly_billing_summary...")
    try:
        summary_df = get_weekly_billing_summary()
        print(f"✓ Retrieved {len(summary_df)} summary records")
        
        if not summary_df.empty:
            print(f"  Sample billing weeks: {summary_df['billing_week'].head(3).tolist()}")
        
        return True
    except Exception as e:
        print(f"✗ get_weekly_billing_summary failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("BILLING DASHBOARD FUNCTIONS TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_database_connection,
        test_get_billing_weeks,
        test_get_provider_billing_details,
        test_update_task_billing_status,
        test_get_tasks_requiring_attention,
        test_weekly_billing_summary
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Dashboard functions are working correctly.")
    else:
        print(f"✗ {total - passed} tests failed. Please check the issues above.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()