#!/usr/bin/env python3
"""
Comprehensive Billing Validation
Tests all billing views and functionality with cleaned production data.
"""

import sqlite3
import os
from datetime import datetime, timedelta

def get_database_connection():
    """Get production database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'production.db')
    return sqlite3.connect(db_path)

def validate_billing_views():
    """Comprehensive billing validation"""
    print("🔍 COMPREHENSIVE BILLING VALIDATION")
    print("=" * 50)

    conn = get_database_connection()
    cursor = conn.cursor()

    # 1. BASIC BILLING TABLES
    print("\n📊 BILLING TABLES STATUS")
    print("-" * 30)

    # Check if billing tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%billing%' OR name LIKE '%provider%' OR name LIKE '%coordinator%'")
    tables = [row[0] for row in cursor.fetchall()]

    if not tables:
        print("   ❌ No billing-related tables found")
        return

    print(f"   📋 Found {len(tables)} billing-related tables:")
    for table in sorted(tables):
        print(f"      • {table}")

    # 2. BILLING VIEWS
    print("\n🔍 BILLING VIEWS ANALYSIS")
    print("-" * 30)

    cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND (name LIKE '%billing%' OR name LIKE '%provider%' OR name LIKE '%coordinator%')")
    views = [row[0] for row in cursor.fetchall()]

    if not views:
        print("   ⚠️ No billing views found")
    else:
        print(f"   📋 Found {len(views)} billing views:")
        for view in sorted(views):
            print(f"      • {view}")

    # 3. TEST COORDINATOR MONTHLY BILLING
    print("\n👩‍💼 COORDINATOR MONTHLY BILLING VALIDATION")
    print("-" * 50)

    # Test coordinator summary view
    test_coordinator_monthly_billing(cursor)

    # 4. TEST PROVIDER WEEKLY BILLING
    print("\n👨‍⚕️ PROVIDER WEEKLY BILLING VALIDATION")
    print("-" * 50)

    # Test provider summary view
    test_provider_weekly_billing(cursor)

    # 5. DETAILED BILLING DATA ANALYSIS
    print("\n💰 DETAILED BILLING DATA ANALYSIS")
    print("-" * 50)

    # Analyze coordinator tasks for billing
    analyze_coordinator_billing_data(cursor)

    # Analyze provider tasks for billing
    analyze_provider_billing_data(cursor)

    # 6. DATA CONSISTENCY CHECKS
    print("\n🔄 DATA CONSISTENCY CHECKS")
    print("-" * 50)

    check_billing_data_consistency(cursor)

    conn.close()

def test_coordinator_monthly_billing(cursor):
    """Test coordinator monthly billing views"""

    try:
        # Check current month coordinator summary
        cursor.execute("SELECT COUNT(*) FROM current_month_coordinator_summary")
        count = cursor.fetchone()[0]
        print(f"   ✅ current_month_coordinator_summary: {count:,} records")

        if count > 0:
            # Sample data
            cursor.execute("""
                SELECT coordinator_code, patient_name, task_date, task_description, minutes_of_service
                FROM current_month_coordinator_summary
                ORDER BY task_date DESC
                LIMIT 3
            """)
            sample = cursor.fetchall()

            print(f"   📋 Sample coordinator billing data:")
            for row in sample:
                print(f"      • {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}min")

        # Test coordinator summary aggregation
        cursor.execute("""
            SELECT coordinator_code, COUNT(*) as task_count, SUM(minutes_of_service) as total_minutes
            FROM current_month_coordinator_summary
            GROUP BY coordinator_code
            ORDER BY total_minutes DESC
            LIMIT 5
        """)
        aggregations = cursor.fetchall()

        if aggregations:
            print(f"   📊 Top coordinators by minutes:")
            for row in aggregations:
                print(f"      • {row[0]}: {row[1]} tasks, {row[2]:,} minutes")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error accessing coordinator billing view: {e}")
        print(f"      This may indicate the view doesn't exist or has schema issues")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in coordinator billing: {e}")

def test_provider_weekly_billing(cursor):
    """Test provider weekly billing views"""

    try:
        # Check current month provider summary
        cursor.execute("SELECT COUNT(*) FROM current_month_provider_summary")
        count = cursor.fetchone()[0]
        print(f"   ✅ current_month_provider_summary: {count:,} records")

        if count > 0:
            # Sample data
            cursor.execute("""
                SELECT provider_name, patient_name, task_date, task_description, minutes_of_service
                FROM current_month_provider_summary
                ORDER BY task_date DESC
                LIMIT 3
            """)
            sample = cursor.fetchall()

            print(f"   📋 Sample provider billing data:")
            for row in sample:
                print(f"      • {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}min")

        # Test provider summary aggregation
        cursor.execute("""
            SELECT provider_name, COUNT(*) as task_count, SUM(minutes_of_service) as total_minutes
            FROM current_month_provider_summary
            GROUP BY provider_name
            ORDER BY total_minutes DESC
            LIMIT 5
        """)
        aggregations = cursor.fetchall()

        if aggregations:
            print(f"   📊 Top providers by minutes:")
            for row in aggregations:
                print(f"      • {row[0]}: {row[1]} tasks, {row[2]:,} minutes")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error accessing provider billing view: {e}")
        print(f"      This may indicate the view doesn't exist or has schema issues")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in provider billing: {e}")

def analyze_coordinator_billing_data(cursor):
    """Analyze coordinator tasks for billing accuracy"""

    try:
        # Check coordinator_tasks table
        cursor.execute("SELECT COUNT(*) FROM coordinator_tasks")
        total_tasks = cursor.fetchone()[0]
        print(f"   📋 Total coordinator tasks in production: {total_tasks:,}")

        # Check date ranges
        cursor.execute("""
            SELECT MIN(task_date) as earliest, MAX(task_date) as latest, COUNT(DISTINCT coordinator_code) as unique_coordinators
            FROM coordinator_tasks
        """)
        date_info = cursor.fetchone()
        print(f"   📅 Date range: {date_info[0]} to {date_info[1]}")
        print(f"   👥 Unique coordinators: {date_info[2]}")

        # Check billing code distribution
        cursor.execute("""
            SELECT billing_code, COUNT(*) as count
            FROM coordinator_tasks
            WHERE billing_code IS NOT NULL
            GROUP BY billing_code
            ORDER BY count DESC
            LIMIT 5
        """)
        billing_codes = cursor.fetchall()

        if billing_codes:
            print(f"   💰 Top coordinator billing codes:")
            for row in billing_codes:
                print(f"      • {row[0]}: {row[1]} tasks")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error analyzing coordinator billing data: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in coordinator analysis: {e}")

def analyze_provider_billing_data(cursor):
    """Analyze provider tasks for billing accuracy"""

    try:
        # Check provider_tasks table
        cursor.execute("SELECT COUNT(*) FROM provider_tasks")
        total_tasks = cursor.fetchone()[0]
        print(f"   📋 Total provider tasks in production: {total_tasks:,}")

        # Check date ranges
        cursor.execute("""
            SELECT MIN(task_date) as earliest, MAX(task_date) as latest, COUNT(DISTINCT provider_name) as unique_providers
            FROM provider_tasks
        """)
        date_info = cursor.fetchone()
        print(f"   📅 Date range: {date_info[0]} to {date_info[1]}")
        print(f"   👥 Unique providers: {date_info[2]}")

        # Check billing code distribution
        cursor.execute("""
            SELECT billing_code, COUNT(*) as count
            FROM provider_tasks
            WHERE billing_code IS NOT NULL
            GROUP BY billing_code
            ORDER BY count DESC
            LIMIT 5
        """)
        billing_codes = cursor.fetchall()

        if billing_codes:
            print(f"   💰 Top provider billing codes:")
            for row in billing_codes:
                print(f"      • {row[0]}: {row[1]} tasks")

        # Check task types
        cursor.execute("""
            SELECT task_description, COUNT(*) as count
            FROM provider_tasks
            GROUP BY task_description
            ORDER BY count DESC
            LIMIT 5
        """)
        task_types = cursor.fetchall()

        if task_types:
            print(f"   📝 Top provider task types:")
            for row in task_types:
                print(f"      • {row[0]}: {row[1]} tasks")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error analyzing provider billing data: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in provider analysis: {e}")

def check_billing_data_consistency(cursor):
    """Check consistency between different billing data sources"""

    try:
        # Check if coordinator codes are consistent
        cursor.execute("SELECT DISTINCT coordinator_code FROM coordinator_tasks")
        coordinator_codes = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT coordinator_code FROM staff_codes")
        valid_codes = [row[0] for row in cursor.fetchall()]

        invalid_coords = set(coordinator_codes) - set(valid_codes)
        if invalid_coords:
            print(f"   ⚠️ Invalid coordinator codes found: {len(invalid_coords)}")
            for code in list(invalid_coords)[:5]:
                print(f"      • {code}")
        else:
            print(f"   ✅ All {len(coordinator_codes)} coordinator codes are valid")

        # Check if provider names are consistent
        cursor.execute("SELECT DISTINCT provider_name FROM provider_tasks")
        provider_names = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT provider_code, alt_provider_code FROM staff_codes")
        valid_providers = []
        for row in cursor.fetchall():
            valid_providers.extend(row)

        invalid_providers = set(provider_names) - set(valid_providers)
        if invalid_providers:
            print(f"   ⚠️ Invalid provider names found: {len(invalid_providers)}")
            for name in list(invalid_providers)[:5]:
                print(f"      • {name}")
        else:
            print(f"   ✅ All {len(provider_names)} provider names are valid")

        # Check for orphaned records (patients not in patients table)
        cursor.execute("""
            SELECT COUNT(DISTINCT p1.patient_id)
            FROM coordinator_tasks p1
            LEFT JOIN patients p2 ON p1.patient_id = p2.patient_id
            WHERE p2.patient_id IS NULL
        """)
        orphaned_coordinator = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(DISTINCT p1.patient_id)
            FROM provider_tasks p1
            LEFT JOIN patients p2 ON p1.patient_id = p2.patient_id
            WHERE p2.patient_id IS NULL
        """)
        orphaned_provider = cursor.fetchone()[0]

        if orphaned_coordinator > 0:
            print(f"   ⚠️ {orphaned_coordinator} coordinator task patients not found in patients table")
        else:
            print(f"   ✅ All coordinator task patients exist in patients table")

        if orphaned_provider > 0:
            print(f"   ⚠️ {orphaned_provider} provider task patients not found in patients table")
        else:
            print(f"   ✅ All provider task patients exist in patients table")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error checking data consistency: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in consistency check: {e}")

if __name__ == "__main__":
    validate_billing_views()