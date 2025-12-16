#!/usr/bin/env python3
"""
Populate workflow tables from existing provider and coordinator task data.

This script:
1. Populates provider_task_billing_status from all provider_tasks_* tables
2. Populates coordinator_monthly_summary from coordinator_tasks
3. Populates provider_weekly_payroll_status from provider_task_billing_status
"""

import calendar
import sqlite3
from datetime import datetime

DB_PATH = "production.db"


def get_db():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)


def populate_provider_billing_status():
    """Populate provider_task_billing_status from all provider_tasks_* tables"""
    conn = get_db()
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("POPULATING: provider_task_billing_status")
    print("=" * 60)

    try:
        # Get all provider_tasks_* table names
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            AND name LIKE 'provider_tasks_20%'
            ORDER BY name DESC
        """)

        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found {len(tables)} provider_tasks tables to process")

        total_inserted = 0

        for table_name in tables:
            print(f"  Processing {table_name}...", end=" ")

            # Insert from this table
            cursor.execute(f"""
                INSERT OR IGNORE INTO provider_task_billing_status (
                    provider_task_id, provider_id, provider_name, patient_name,
                    task_date, billing_week, week_start_date, week_end_date,
                    task_description, minutes_of_service, billing_code,
                    billing_code_description, billing_status, is_billed,
                    created_date, billed_by, notes, paid_by_zen
                )
                SELECT
                    pt.provider_task_id,
                    pt.provider_id,
                    pt.provider_name,
                    pt.patient_name,
                    pt.task_date,
                    CAST(strftime('%W', pt.task_date) AS INTEGER) as billing_week,
                    DATE(pt.task_date, 'weekday 0', '-6 days') as week_start_date,
                    DATE(pt.task_date, 'weekday 0') as week_end_date,
                    pt.task_description,
                    pt.minutes_of_service,
                    pt.billing_code,
                    COALESCE(pt.billing_code_description, 'Unknown') as billing_code_description,
                    'Pending' as billing_status,
                    FALSE as is_billed,
                    CURRENT_TIMESTAMP as created_date,
                    'system_import' as billed_by,
                    pt.notes,
                    CASE WHEN pt.notes LIKE '%paid by zen%' THEN TRUE ELSE FALSE END as paid_by_zen
                FROM {table_name} pt
                WHERE pt.billing_code IS NOT NULL
                    AND pt.billing_code NOT IN ('Not_Billable', '', 'PENDING', 'nan')
                    AND pt.minutes_of_service > 0
            """)

            count = cursor.rowcount
            total_inserted += count
            print(f"{count} records")

        conn.commit()

        # Final count
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN paid_by_zen THEN 1 ELSE 0 END) as paid_by_zen_count
            FROM provider_task_billing_status
        """)
        total_count, paid_by_zen_count = cursor.fetchone()
        print(f"\n✓ Total provider_task_billing_status records: {total_count}")
        print(f"  - Paid by ZEN (already reimbursed): {paid_by_zen_count}")
        print(f"  - Need billing to Medicare: {total_count - paid_by_zen_count}")

        return total_count

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 0
    finally:
        conn.close()


def populate_coordinator_monthly_summary():
    """Populate coordinator_monthly_summary from coordinator_tasks"""
    conn = get_db()
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("POPULATING: coordinator_monthly_summary")
    print("=" * 60)

    try:
        # Clear existing data
        print("  Clearing existing records...", end=" ")
        cursor.execute("DELETE FROM coordinator_monthly_summary")
        print("done")

        # Insert aggregated coordinator data by patient/month
        print("  Aggregating coordinator tasks...", end=" ")
        cursor.execute("""
            INSERT INTO coordinator_monthly_summary (
                coordinator_id, coordinator_name, patient_id, patient_name,
                year, month, month_start_date, month_end_date,
                total_tasks_completed, total_time_spent_minutes,
                billing_code, billing_code_description,
                billing_status, is_billed, billed_by,
                created_date, updated_date
            )
            SELECT
                ct.coordinator_id,
                ct.coordinator_name,
                ct.patient_id,
                ct.patient_id as patient_name,
                CAST(strftime('%Y', ct.task_date) AS INTEGER) as year,
                CAST(strftime('%m', ct.task_date) AS INTEGER) as month,
                DATE(strftime('%Y-%m-01', ct.task_date)) as month_start_date,
                DATE(strftime('%Y-%m-01', ct.task_date, '+1 month'), '-1 day') as month_end_date,
                COUNT(*) as total_tasks_completed,
                CAST(SUM(COALESCE(ct.duration_minutes, 0)) AS INTEGER) as total_time_spent_minutes,
                CASE
                    WHEN SUM(COALESCE(ct.duration_minutes, 0)) >= 50 THEN '99492'
                    WHEN SUM(COALESCE(ct.duration_minutes, 0)) >= 20 THEN '99491'
                    ELSE '99490'
                END as billing_code,
                CASE
                    WHEN SUM(COALESCE(ct.duration_minutes, 0)) >= 50 THEN 'Care Management - Complex'
                    WHEN SUM(COALESCE(ct.duration_minutes, 0)) >= 20 THEN 'Care Management - Moderate'
                    ELSE 'Care Management - Basic'
                END as billing_code_description,
                'Pending' as billing_status,
                FALSE as is_billed,
                NULL as billed_by,
                CURRENT_TIMESTAMP as created_date,
                CURRENT_TIMESTAMP as updated_date
            FROM coordinator_tasks ct
            WHERE ct.coordinator_id IS NOT NULL
                AND ct.patient_id IS NOT NULL
                AND TRIM(ct.patient_id) != ''
                AND COALESCE(ct.duration_minutes, 0) > 0
            GROUP BY ct.coordinator_id, ct.coordinator_name, ct.patient_id,
                CAST(strftime('%Y', ct.task_date) AS INTEGER),
                CAST(strftime('%m', ct.task_date) AS INTEGER)
        """)

        conn.commit()

        # Final count
        cursor.execute("SELECT COUNT(*) FROM coordinator_monthly_summary")
        final_count = cursor.fetchone()[0]
        print(f"done")
        print(f"✓ Total coordinator_monthly_summary records: {final_count}")

        return final_count

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 0
    finally:
        conn.close()


def populate_provider_weekly_payroll():
    """Populate provider_weekly_payroll_status from provider_task_billing_status"""
    conn = get_db()
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("POPULATING: provider_weekly_payroll_status")
    print("=" * 60)

    try:
        # Check if provider_task_billing_status has data
        cursor.execute("SELECT COUNT(*) FROM provider_task_billing_status")
        billing_count = cursor.fetchone()[0]

        if billing_count == 0:
            print(
                "  WARNING: provider_task_billing_status is empty, skipping payroll population"
            )
            return 0

        print(f"  Found {billing_count} billing records")

        # Clear existing data
        print("  Clearing existing records...", end=" ")
        cursor.execute("DELETE FROM provider_weekly_payroll_status")
        print("done")

        # Aggregate by provider + week + visit_type
        # NOTE: Includes ALL tasks (paid_by_zen flag is for audit trail only, not exclusion)
        # Payroll and billing are separate workflows - both use all tasks
        print("  Aggregating payroll by visit type...", end=" ")
        cursor.execute("""
            INSERT INTO provider_weekly_payroll_status (
                provider_id, provider_name,
                pay_week_start_date, pay_week_end_date,
                pay_week_number, pay_year, visit_type,
                task_count, total_minutes_of_service,
                payroll_status, created_date
            )
            SELECT
                ptbs.provider_id,
                ptbs.provider_name,
                ptbs.week_start_date,
                ptbs.week_end_date,
                ptbs.billing_week,
                CAST(strftime('%Y', ptbs.task_date) AS INTEGER),
                ptbs.task_description as visit_type,
                COUNT(*) as task_count,
                SUM(COALESCE(ptbs.minutes_of_service, 0)) as total_minutes,
                'Pending' as payroll_status,
                CURRENT_TIMESTAMP as created_date
            FROM provider_task_billing_status ptbs
            WHERE ptbs.provider_id IS NOT NULL
                AND COALESCE(ptbs.minutes_of_service, 0) > 0
            GROUP BY ptbs.provider_id, ptbs.provider_name,
                ptbs.week_start_date, ptbs.week_end_date,
                ptbs.task_description
        """)

        print(f"done")

        # Now update paid_by_zen counts (tasks already paid by ZEN - don't double-pay)
        print("  Adding paid_by_zen tracking (prevent double-payment)...", end=" ")
        cursor.execute("""
            UPDATE provider_weekly_payroll_status
            SET paid_by_zen_count = (
                SELECT COUNT(*) FROM provider_task_billing_status ptbs
                WHERE ptbs.provider_id = provider_weekly_payroll_status.provider_id
                  AND ptbs.task_description = provider_weekly_payroll_status.visit_type
                  AND ptbs.week_start_date = provider_weekly_payroll_status.pay_week_start_date
                  AND ptbs.paid_by_zen = TRUE
            ),
            paid_by_zen_minutes = (
                SELECT SUM(minutes_of_service) FROM provider_task_billing_status ptbs
                WHERE ptbs.provider_id = provider_weekly_payroll_status.provider_id
                  AND ptbs.task_description = provider_weekly_payroll_status.visit_type
                  AND ptbs.week_start_date = provider_weekly_payroll_status.pay_week_start_date
                  AND ptbs.paid_by_zen = TRUE
            )
        """)

        conn.commit()

        # Final count
        cursor.execute("SELECT COUNT(*) FROM provider_weekly_payroll_status")
        final_count = cursor.fetchone()[0]
        print(f"done")
        print(f"✓ Total provider_weekly_payroll_status records: {final_count}")

        return final_count

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 0
    finally:
        conn.close()


def verify_data():
    """Verify that all workflow tables are properly populated"""
    conn = get_db()
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("DATA VERIFICATION")
    print("=" * 60)

    try:
        # Check provider billing status
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT provider_id) as providers,
                   COUNT(DISTINCT billing_week) as weeks,
                   SUM(CASE WHEN paid_by_zen THEN 1 ELSE 0 END) as paid_by_zen_count
            FROM provider_task_billing_status
        """)
        result = cursor.fetchone()
        print(
            f"✓ provider_task_billing_status: {result[0]} tasks from {result[1]} providers across {result[2]} weeks"
        )
        print(f"  - Already paid by ZEN (not billable to Medicare): {result[3]} tasks")

        # Check coordinator summary
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT coordinator_id) as coordinators,
                   COUNT(DISTINCT patient_id) as patients
            FROM coordinator_monthly_summary
        """)
        result = cursor.fetchone()
        print(
            f"✓ coordinator_monthly_summary: {result[0]} records from {result[1]} coordinators, {result[2]} unique patients"
        )

        # Check payroll status
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(DISTINCT provider_id) as providers,
                   COUNT(DISTINCT visit_type) as visit_types,
                   SUM(total_minutes_of_service) as total_minutes,
                   SUM(CASE WHEN paid_by_zen_count > 0 THEN paid_by_zen_count ELSE 0 END) as already_paid_count,
                   SUM(CASE WHEN paid_by_zen_count > 0 THEN paid_by_zen_minutes ELSE 0 END) as already_paid_minutes
            FROM provider_weekly_payroll_status
        """)
        result = cursor.fetchone()
        print(
            f"✓ provider_weekly_payroll_status: {result[0]} records from {result[1]} providers, {result[2]} visit types"
        )
        print(f"  - Total minutes: {result[3]:,}")
        print(
            f"  - Already paid by ZEN (do NOT double-pay): {result[4]} tasks, {result[5]:,} minutes"
        )

        # Check for missing billing codes in provider billing
        cursor.execute("""
            SELECT COUNT(*) FROM provider_task_billing_status
            WHERE billing_code IS NULL OR billing_code = ''
        """)
        missing = cursor.fetchone()[0]
        if missing > 0:
            print(
                f"⚠ WARNING: {missing} provider billing records have missing billing codes"
            )

        print("\n✓ All workflow tables successfully populated!")

    except Exception as e:
        print(f"✗ Error during verification: {e}")
        import traceback

        traceback.print_exc()
    finally:
        conn.close()


def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print("WORKFLOW TABLE POPULATION")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Step 1: Populate provider billing
        provider_count = populate_provider_billing_status()

        # Step 2: Populate coordinator summary
        coordinator_count = populate_coordinator_monthly_summary()

        # Step 3: Populate payroll
        payroll_count = populate_provider_weekly_payroll()

        # Step 4: Verify
        verify_data()

        print("\n" + "=" * 60)
        print("COMPLETION SUMMARY")
        print("=" * 60)
        print(
            f"Provider Billing Status Records:  {provider_count:,} (includes 'paid by zen' tracking)"
        )
        print(f"Coordinator Monthly Summary:     {coordinator_count:,}")
        print(
            f"Provider Weekly Payroll:         {payroll_count:,} (excludes 'paid by zen' tasks)"
        )
        print(
            f"Total Workflow Records:          {provider_count + coordinator_count + payroll_count:,}"
        )
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
