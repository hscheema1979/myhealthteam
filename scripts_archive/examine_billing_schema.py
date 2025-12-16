#!/usr/bin/env python3
"""
Examine Billing Schema
Investigates the actual structure of billing tables and views
"""

import sqlite3
import os

def get_database_connection():
    """Get production database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'production.db')
    return sqlite3.connect(db_path)

def examine_billing_schema():
    """Examine the actual schema of billing-related tables and views"""
    print("🔍 BILLING SCHEMA INVESTIGATION")
    print("=" * 50)

    conn = get_database_connection()
    cursor = conn.cursor()

    # 1. Check coordinator_tasks table structure
    print("\n👩‍💼 COORDINATOR_TASKS TABLE STRUCTURE")
    print("-" * 50)
    examine_table_schema(cursor, 'coordinator_tasks')

    # 2. Check provider_tasks table structure
    print("\n👨‍⚕️ PROVIDER_TASKS TABLE STRUCTURE")
    print("-" * 50)
    examine_table_schema(cursor, 'provider_tasks')

    # 3. Check current_month_coordinator_summary view
    print("\n📊 CURRENT_MONTH_COORDINATOR_SUMMARY VIEW")
    print("-" * 50)
    examine_view_schema(cursor, 'current_month_coordinator_summary')

    # 4. Check if current_month_provider_summary exists
    print("\n📊 CURRENT_MONTH_PROVIDER_SUMMARY VIEW")
    print("-" * 50)
    examine_view_schema(cursor, 'current_month_provider_summary')

    # 5. Check weekly billing view
    print("\n📊 V_WEEKLY_BILLING_SUMMARY VIEW")
    print("-" * 50)
    examine_view_schema(cursor, 'v_weekly_billing_summary')

    # 6. Check provider monthly summary
    print("\n📊 PROVIDER_MONTHLY_SUMMARY VIEW")
    print("-" * 50)
    examine_view_schema(cursor, 'provider_monthly_summary')

    # 7. Check provider weekly summary
    print("\n📊 PROVIDER_WEEKLY_SUMMARY VIEW")
    print("-" * 50)
    examine_view_schema(cursor, 'provider_weekly_summary')

    # 8. Check coordinator monthly summary
    print("\n📊 PROVIDER_WEEKLY_SUMMARY VIEW")
    print("-" * 50)
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name='staging_coordinator_monthly_summary'")
        result = cursor.fetchone()
        if result:
            print(f"   ✅ Found view definition:")
            print(f"   {result[0]}")
        else:
            print(f"   ❌ View not found")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    conn.close()

def examine_table_schema(cursor, table_name):
    """Examine the schema of a table"""
    try:
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        print(f"   📋 {table_name} columns ({len(columns)} columns):")
        for col in columns:
            print(f"      • {col[1]} ({col[2]}) {'[PK]' if col[5] else ''}")

        # Get sample data
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        sample = cursor.fetchall()
        if sample:
            print(f"   📋 Sample data (3 rows):")
            column_names = [col[1] for col in columns]
            for i, row in enumerate(sample):
                print(f"      Row {i+1}:")
                for j, value in enumerate(row):
                    if j < len(column_names):
                        print(f"        {column_names[j]}: {value}")
                print()

    except sqlite3.OperationalError as e:
        print(f"   ❌ Table {table_name} not found: {e}")

def examine_view_schema(cursor, view_name):
    """Examine the schema of a view"""
    try:
        # Get view definition
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND name = ?", (view_name,))
        result = cursor.fetchone()
        if result:
            print(f"   ✅ View definition found:")
            print(f"   {result[0]}")

            # Try to get column info
            cursor.execute(f"PRAGMA table_info({view_name})")
            columns = cursor.fetchall()
            if columns:
                print(f"   📋 Columns ({len(columns)} columns):")
                for col in columns:
                    print(f"      • {col[1]} ({col[2]})")

            # Try to get sample data
            cursor.execute(f"SELECT * FROM {view_name} LIMIT 2")
            sample = cursor.fetchall()
            if sample:
                print(f"   📋 Sample data ({len(sample)} rows):")
                for i, row in enumerate(sample):
                    print(f"      Row {i+1}: {row}")

        else:
            print(f"   ❌ View {view_name} definition not found")

    except sqlite3.OperationalError as e:
        print(f"   ❌ View {view_name} not found: {e}")
    except Exception as e:
        print(f"   ⚠️ Error examining view {view_name}: {e}")

if __name__ == "__main__":
    examine_billing_schema()