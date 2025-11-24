#!/usr/bin/env python3
"""
Dashboard-Based Billing Validation
Tests billing functionality based on actual dashboard implementations.
Validates provider weekly billing and coordinator monthly billing.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import calendar

def get_database_connection():
    """Get production database connection"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'production.db')
    return sqlite3.connect(db_path)

def validate_dashboard_billing_views():
    """Validate billing functionality based on dashboard implementations"""
    print("📊 DASHBOARD-BASED BILLING VALIDATION")
    print("=" * 50)

    conn = get_database_connection()
    cursor = conn.cursor()

    # 1. PROVIDER WEEKLY BILLING (from weekly_billing_dashboard.py logic)
    print("\n👨‍⚕️ PROVIDER WEEKLY BILLING VALIDATION")
    print("-" * 50)
    validate_provider_weekly_billing(cursor)

    # 2. PROVIDER TASK BILLING STATUS (from billing_dashboard.py logic)
    print("\n💰 PROVIDER TASK BILLING STATUS")
    print("-" * 50)
    validate_provider_task_billing_status(cursor)

    # 3. COORDINATOR MONTHLY BILLING (from monthly_coordinator_billing_dashboard.py logic)
    print("\n👩‍💼 COORDINATOR MONTHLY BILLING VALIDATION")
    print("-" * 50)
    validate_coordinator_monthly_billing(cursor)

    # 4. COORDINATOR MINUTES TRACKING (from care_coordinator_dashboard_enhanced.py logic)
    print("\n⏱️ COORDINATOR MINUTES TRACKING")
    print("-" * 50)
    validate_coordinator_minutes_tracking(cursor)

    # 5. DATA CONSISTENCY WITH STAFF CODES
    print("\n🔗 STAFF CODE CONSISTENCY CHECK")
    print("-" * 50)
    check_staff_code_consistency(cursor)

    conn.close()

def validate_provider_weekly_billing(cursor):
    """Validate provider weekly billing based on weekly_billing_dashboard.py logic"""

    try:
        # Get available weeks using the dashboard logic
        query = """
        SELECT 
            strftime('%Y-%W', task_date) as billing_week,
            strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
            strftime('%Y-%m-%d', MAX(task_date)) as week_end_date,
            COUNT(*) as total_tasks,
            COUNT(DISTINCT provider_name) as provider_count,
            COUNT(DISTINCT patient_id) as patient_count
        FROM provider_tasks
        WHERE task_date IS NOT NULL
        GROUP BY strftime('%Y-%W', task_date)
        ORDER BY billing_week DESC
        LIMIT 10
        """

        cursor.execute(query)
        weeks = cursor.fetchall()

        print(f"   ✅ Found {len(weeks)} billing weeks")

        # Show recent weeks
        for week in weeks[:5]:
            billing_week, start_date, end_date, task_count, provider_count, patient_count = week
            print(f"   📅 {billing_week}: {task_count:,} tasks, {provider_count} providers, {patient_count} patients")
            print(f"      Range: {start_date} to {end_date}")

        # Check for October 2025 specifically
        oct_2025_query = """
        SELECT 
            strftime('%Y-%W', task_date) as billing_week,
            COUNT(*) as total_tasks
        FROM provider_tasks
        WHERE strftime('%Y', task_date) = '2025'
        AND strftime('%m', task_date) = '10'
        GROUP BY strftime('%Y-%W', task_date)
        ORDER BY billing_week DESC
        """

        cursor.execute(oct_2025_query)
        oct_weeks = cursor.fetchall()

        print(f"   📅 October 2025: {len(oct_weeks)} billing weeks")
        for week in oct_weeks:
            print(f"      • Week {week[0]}: {week[1]} tasks")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error with provider weekly billing: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in provider weekly billing: {e}")

def validate_provider_task_billing_status(cursor):
    """Validate provider task billing status based on billing_dashboard.py logic"""

    try:
        # Check if provider_task_billing_status table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = 'provider_task_billing_status'
        """)
        if not cursor.fetchone():
            print(f"   ⚠️ provider_task_billing_status table not found")
            return

        # Get billing status summary
        query = """
        SELECT 
            billing_status,
            COUNT(*) as task_count,
            COUNT(CASE WHEN is_billed = 1 THEN 1 END) as billed_count,
            COUNT(CASE WHEN is_paid = 1 THEN 1 END) as paid_count
        FROM provider_task_billing_status
        GROUP BY billing_status
        ORDER BY task_count DESC
        """

        cursor.execute(query)
        status_summary = cursor.fetchall()

        if status_summary:
            print(f"   📊 Billing status distribution:")
            for status in status_summary:
                status_name, total, billed, paid = status
                print(f"      • {status_name}: {total:,} tasks ({billed:,} billed, {paid:,} paid)")
        else:
            print(f"   ℹ️ No billing status data found")

        # Check current week summary
        current_week_query = """
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

        cursor.execute(current_week_query)
        current_summary = cursor.fetchone()

        if current_summary:
            total, billed, not_billable, attention, carryover = current_summary
            print(f"   📈 Current week summary: {total:,} tasks")
            print(f"      • Billed: {billed:,}")
            print(f"      • Not billable: {not_billable:,}")
            print(f"      • Requires attention: {attention:,}")
            print(f"      • Carried over: {carryover:,}")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error with provider billing status: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in provider billing status: {e}")

def validate_coordinator_monthly_billing(cursor):
    """Validate coordinator monthly billing based on monthly_coordinator_billing_dashboard.py logic"""

    try:
        # Get available months from coordinator monthly billing tables
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'patient_monthly_billing_20%'
        ORDER BY name DESC
        LIMIT 10
        """

        cursor.execute(query)
        tables = cursor.fetchall()

        print(f"   ✅ Found {len(tables)} coordinator monthly billing tables")

        # Check the most recent month
        for table in tables[:1]:
            table_name = table[0]
            # Extract year and month
            parts = table_name.split('_')
            year = int(parts[3])
            month = int(parts[4])

            print(f"   📅 Recent month: {calendar.month_name[month]} {year}")

            # Get billing summary from the table
            summary_query = f"""
            SELECT 
                billing_code,
                billing_code_description,
                COUNT(DISTINCT patient_id) as patient_count,
                SUM(total_minutes) as total_minutes
            FROM {table_name}
            GROUP BY billing_code, billing_code_description
            ORDER BY patient_count DESC, total_minutes DESC
            LIMIT 5
            """

            cursor.execute(summary_query)
            billing_summary = cursor.fetchall()

            if billing_summary:
                print(f"   📊 Top billing codes:")
                for code, description, patient_count, total_minutes in billing_summary:
                    print(f"      • {code}: {patient_count} patients, {total_minutes:,} minutes")
                    if description:
                        print(f"        ({description[:50]}...)")
            else:
                print(f"   ℹ️ No billing data found for {calendar.month_name[month]} {year}")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error with coordinator monthly billing: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in coordinator monthly billing: {e}")

def validate_coordinator_minutes_tracking(cursor):
    """Validate coordinator minutes tracking based on care_coordinator_dashboard_enhanced.py logic"""

    try:
        # Get available coordinator monthly summary tables
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'coordinator_monthly_summary_20%'
        ORDER BY name DESC
        LIMIT 5
        """

        cursor.execute(query)
        tables = cursor.fetchall()

        if not tables:
            print(f"   ⚠️ No coordinator monthly summary tables found")
            return

        print(f"   ✅ Found {len(tables)} coordinator monthly summary tables")

        # Check the current month table
        current_table = tables[0][0]
        print(f"   📅 Current month table: {current_table}")

        # Get total minutes for current month
        minutes_query = f"""
        SELECT 
            COUNT(*) as total_records,
            SUM(total_minutes) as total_minutes,
            COUNT(DISTINCT coordinator_id) as unique_coordinators,
            AVG(total_minutes) as avg_minutes_per_patient
        FROM {current_table}
        WHERE total_minutes IS NOT NULL
        """

        cursor.execute(minutes_query)
        minutes_summary = cursor.fetchone()

        if minutes_summary:
            total_records, total_minutes, unique_coordinators, avg_minutes = minutes_summary
            print(f"   📊 Current month summary:")
            print(f"      • Total records: {total_records:,}")
            print(f"      • Total minutes: {total_minutes:,}")
            print(f"      • Unique coordinators: {unique_coordinators}")
            print(f"      • Avg minutes per patient: {round(avg_minutes or 0, 1)}")

            # Get top coordinators by minutes
            top_coords_query = f"""
            SELECT 
                coordinator_id,
                patient_id,
                total_minutes,
                task_date
            FROM {current_table}
            WHERE total_minutes IS NOT NULL
            ORDER BY total_minutes DESC
            LIMIT 3
            """

            cursor.execute(top_coords_query)
            top_coords = cursor.fetchall()

            if top_coords:
                print(f"   🔝 Top coordinator activities:")
                for coord_id, patient_id, minutes, task_date in top_coords:
                    print(f"      • Coordinator {coord_id} - Patient {patient_id}: {minutes} minutes on {task_date}")

        else:
            print(f"   ℹ️ No coordinator minutes data found")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error with coordinator minutes tracking: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in coordinator minutes tracking: {e}")

def check_staff_code_consistency(cursor):
    """Check consistency between staff codes and actual data"""

    try:
        # Get all staff codes
        cursor.execute("""
            SELECT coordinator_code, provider_code, alt_provider_code, full_name
            FROM staff_codes
        """)
        staff_codes = cursor.fetchall()

        if not staff_codes:
            print(f"   ❌ No staff codes found")
            return

        print(f"   📋 Validating {len(staff_codes)} staff members")

        # Check provider names in provider_tasks against staff codes
        cursor.execute("""
            SELECT DISTINCT provider_name
            FROM provider_tasks
            WHERE provider_name IS NOT NULL
        """)
        provider_names_in_tasks = [row[0] for row in cursor.fetchall()]

        # Check which provider names match staff codes
        valid_provider_codes = []
        for coord_code, provider_code, alt_provider_code, full_name in staff_codes:
            if provider_code in provider_names_in_tasks:
                valid_provider_codes.append(provider_code)
            if alt_provider_code and alt_provider_code in provider_names_in_tasks:
                valid_provider_codes.append(alt_provider_code)

        print(f"   ✅ Provider codes from staff table: {len(valid_provider_codes)}")
        print(f"   📊 Provider names in tasks: {len(provider_names_in_tasks)}")

        # Check for provider names that don't match staff codes
        valid_providers_set = set(valid_provider_codes)
        invalid_provider_names = set(provider_names_in_tasks) - valid_providers_set

        if invalid_provider_names:
            print(f"   ⚠️ Provider names not in staff codes: {len(invalid_provider_names)}")
            for name in list(invalid_provider_names)[:3]:
                print(f"      • {name}")
        else:
            print(f"   ✅ All provider names in tasks match staff codes")

        # Check coordinator codes
        cursor.execute("""
            SELECT DISTINCT coordinator_id
            FROM coordinator_tasks
            WHERE coordinator_id IS NOT NULL
        """)
        coord_ids_in_tasks = [row[0] for row in cursor.fetchall()]

        valid_coord_codes = [coord_code for coord_code, _, _, _ in staff_codes if coord_code]

        print(f"   📊 Coordinator IDs in tasks: {len(coord_ids_in_tasks)}")
        print(f"   📋 Valid coordinator codes: {len(valid_coord_codes)}")

        # Check which coordinator IDs match staff codes
        invalid_coord_ids = set(coord_ids_in_tasks) - set(valid_coord_codes)
        if invalid_coord_ids:
            print(f"   ⚠️ Coordinator IDs not in staff codes: {len(invalid_coord_ids)}")
            for coord_id in list(invalid_coord_ids)[:3]:
                print(f"      • {coord_id}")
        else:
            print(f"   ✅ All coordinator IDs in tasks match staff codes")

    except sqlite3.OperationalError as e:
        print(f"   ❌ Error checking staff code consistency: {e}")
    except Exception as e:
        print(f"   ⚠️ Unexpected error in staff code consistency: {e}")

if __name__ == "__main__":
    validate_dashboard_billing_views()