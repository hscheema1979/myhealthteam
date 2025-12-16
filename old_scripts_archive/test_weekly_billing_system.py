"""
Test Weekly Billing System (P00) with Historical Data
This script validates the billing cycle logic and carryover functionality.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.billing.weekly_billing_processor import WeeklyBillingProcessor
from src.database import get_db_connection

def test_billing_system():
    """Comprehensive test of the weekly billing system."""
    print("=" * 60)
    print("WEEKLY BILLING SYSTEM (P00) - COMPREHENSIVE TEST")
    print("=" * 60)
    
    processor = WeeklyBillingProcessor()
    
    # Test 1: Current billing week calculation
    print("\n1. TESTING BILLING WEEK CALCULATION")
    print("-" * 40)
    current_week = processor.get_current_billing_week()
    print(f"Current billing week: {current_week[0]}")
    print(f"Week start: {current_week[1]}")
    print(f"Week end: {current_week[2]}")
    
    # Test with last week
    last_week_date = datetime.now() - timedelta(days=7)
    last_week = processor.get_current_billing_week(last_week_date)
    print(f"Last week: {last_week[0]} ({last_week[1]} to {last_week[2]})")
    
    # Test 2: Check if billing system tables exist
    print("\n2. TESTING DATABASE SCHEMA")
    print("-" * 40)
    conn = get_db_connection()
    
    required_tables = [
        'weekly_billing_reports',
        'provider_task_billing_status', 
        'billing_status_history'
    ]
    
    for table in required_tables:
        result = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
            (table,)
        ).fetchone()
        status = "✓ EXISTS" if result else "✗ MISSING"
        print(f"Table {table}: {status}")
    
    # Test 3: Check existing provider task data
    print("\n3. ANALYZING EXISTING PROVIDER TASK DATA")
    print("-" * 40)
    
    # Get current month table
    now = datetime.now()
    current_table = f"provider_tasks_{now.year}_{now.month:02d}"
    
    # Check if current month table exists
    table_exists = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
        (current_table,)
    ).fetchone()
    
    if table_exists:
        # Get sample data from current month
        sample_data = pd.read_sql_query(f"""
            SELECT 
                provider_task_id,
                task_id,
                provider_id,
                patient_id,
                status,
                minutes_of_service,
                billing_code,
                task_date,
                created_date
            FROM {current_table}
            ORDER BY task_date DESC
            LIMIT 10
        """, conn)
        
        print(f"Sample data from {current_table}:")
        print(sample_data.to_string(index=False))
        
        # Get summary statistics
        total_tasks = conn.execute(f"SELECT COUNT(*) FROM {current_table}").fetchone()[0]
        completed_tasks = conn.execute(f"SELECT COUNT(*) FROM {current_table} WHERE status = 'completed'").fetchone()[0]
        
        print(f"\nSummary for {current_table}:")
        print(f"Total tasks: {total_tasks}")
        print(f"Completed tasks: {completed_tasks}")
        
    else:
        print(f"Table {current_table} does not exist")
        
        # Try to find any provider_tasks tables
        all_tables = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE 'provider_tasks_%'
            ORDER BY name DESC
        """).fetchall()
        
        if all_tables:
            print("Available provider_tasks tables:")
            for table in all_tables[:5]:  # Show first 5
                print(f"  - {table[0]}")
        else:
            print("No provider_tasks tables found")
    
    # Test 4: Initialize billing system if needed
    print("\n4. TESTING SYSTEM INITIALIZATION")
    print("-" * 40)
    
    try:
        setup_result = processor.setup_billing_system()
        print(f"System setup: {'✓ SUCCESS' if setup_result else '✗ FAILED'}")
    except Exception as e:
        print(f"System setup: ✗ ERROR - {e}")
    
    # Test 5: Test data migration
    print("\n5. TESTING DATA MIGRATION")
    print("-" * 40)
    
    try:
        migration_result = processor.migrate_existing_data()
        print(f"Data migration: {'✓ SUCCESS' if migration_result else '✗ FAILED'}")
        
        # Check migrated data
        migrated_count = conn.execute(
            "SELECT COUNT(*) FROM provider_task_billing_status"
        ).fetchone()[0]
        print(f"Migrated tasks: {migrated_count}")
        
    except Exception as e:
        print(f"Data migration: ✗ ERROR - {e}")
    
    # Test 6: Test weekly processing with last week's date
    print("\n6. TESTING WEEKLY PROCESSING (LAST WEEK)")
    print("-" * 40)
    
    try:
        # Process last week's billing
        last_week_result = processor.process_weekly_billing(last_week_date)
        print(f"Last week processing: ✓ SUCCESS")
        print(f"Billing week: {last_week_result['billing_week']}")
        print(f"Tasks processed: {last_week_result['tasks_processed']}")
        print(f"Tasks marked as billed: {last_week_result['tasks_billed']}")
        print(f"Carryover tasks: {last_week_result['carryover_tasks']}")
        
    except Exception as e:
        print(f"Last week processing: ✗ ERROR - {e}")
    
    # Test 7: Test current week processing
    print("\n7. TESTING WEEKLY PROCESSING (CURRENT WEEK)")
    print("-" * 40)
    
    try:
        # Process current week's billing
        current_week_result = processor.process_weekly_billing()
        print(f"Current week processing: ✓ SUCCESS")
        print(f"Billing week: {current_week_result['billing_week']}")
        print(f"Tasks processed: {current_week_result['tasks_processed']}")
        print(f"Tasks marked as billed: {current_week_result['tasks_billed']}")
        print(f"Carryover tasks: {current_week_result['carryover_tasks']}")
        
    except Exception as e:
        print(f"Current week processing: ✗ ERROR - {e}")
    
    # Test 8: Validate billing status distribution
    print("\n8. TESTING BILLING STATUS DISTRIBUTION")
    print("-" * 40)
    
    try:
        status_distribution = pd.read_sql_query("""
            SELECT 
                billing_status,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM provider_task_billing_status), 2) as percentage
            FROM provider_task_billing_status
            GROUP BY billing_status
            ORDER BY count DESC
        """, conn)
        
        print("Billing status distribution:")
        print(status_distribution.to_string(index=False))
        
    except Exception as e:
        print(f"Status distribution: ✗ ERROR - {e}")
    
    # Test 9: Test carryover logic
    print("\n9. TESTING CARRYOVER LOGIC")
    print("-" * 40)
    
    try:
        # Get unbilled tasks from previous weeks
        unbilled_tasks = pd.read_sql_query("""
            SELECT 
                billing_week,
                COUNT(*) as unbilled_count
            FROM provider_task_billing_status
            WHERE billing_status = 'Not Billed'
            AND billing_week < ?
            GROUP BY billing_week
            ORDER BY billing_week DESC
            LIMIT 5
        """, conn, params=(current_week[0],))
        
        if not unbilled_tasks.empty:
            print("Unbilled tasks from previous weeks:")
            print(unbilled_tasks.to_string(index=False))
        else:
            print("No unbilled tasks from previous weeks found")
            
    except Exception as e:
        print(f"Carryover logic test: ✗ ERROR - {e}")
    
    # Test 10: Test weekly report data retrieval
    print("\n10. TESTING WEEKLY REPORT DATA")
    print("-" * 40)
    
    try:
        # Get weekly report data for last week
        last_week_data = processor.get_weekly_report_data(last_week[0])
        print(f"Last week report data: {len(last_week_data)} records")
        
        if not last_week_data.empty:
            print("Sample last week data:")
            print(last_week_data.head().to_string(index=False))
        
        # Get current week data
        current_week_data = processor.get_weekly_report_data(current_week[0])
        print(f"Current week report data: {len(current_week_data)} records")
        
    except Exception as e:
        print(f"Weekly report data: ✗ ERROR - {e}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("WEEKLY BILLING SYSTEM TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_billing_system()