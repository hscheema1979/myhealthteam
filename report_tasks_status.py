#!/usr/bin/env python3
"""
Task Status Report
==================
Comprehensive report on provider and coordinator tasks status.
Validates that all transforms are working correctly and identifies any issues.

Usage:
    python report_tasks_status.py
"""

import glob
import os
import re
import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = "production.db"
CSV_DIR = "downloads"


def get_db_connection():
    """Get database connection with proper row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_date(date_str):
    """Parse date from various formats"""
    if pd.isna(date_str) or not date_str:
        return None
    date_str = str(date_str).strip()
    if not date_str:
        return None
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%m/%d/%y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def get_table_list(conn, pattern):
    """Get list of tables matching pattern"""
    cursor = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE ?
        ORDER BY name
    """,
        (pattern,),
    )
    return [row["name"] for row in cursor.fetchall()]


def get_staff_name(conn, user_id):
    """Get staff name from user_id"""
    if not user_id:
        return "NULL"
    cursor = conn.execute("SELECT full_name FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else f"Unknown({user_id})"


def report_provider_tasks(conn):
    """Generate provider tasks report"""
    print("\n" + "=" * 80)
    print("PROVIDER TASKS ANALYSIS")
    print("=" * 80)

    provider_tables = get_table_list(conn, "provider_tasks_%")
    print(f"\nFound {len(provider_tables)} provider task tables")

    # Summary by month
    print("\n📊 Tasks by Month:")
    total_tasks = 0
    monthly_stats = []

    for table in provider_tables:
        # Count total per month
        cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
        month_total = cursor.fetchone()["count"]
        total_tasks += month_total

        # Count NULL provider_ids
        cursor = conn.execute(
            f"SELECT COUNT(*) as null_count FROM {table} WHERE provider_id IS NULL"
        )
        null_count = cursor.fetchone()["null_count"]

        month_label = table.replace("provider_tasks_", "").replace("_", "-")
        status = "⚠️" if null_count > 0 else "✅"
        print(
            f"   {status} {month_label}: {month_total:,} tasks ({null_count:,} NULL provider_id)"
        )

        monthly_stats.append(
            {"month": month_label, "total": month_total, "nulls": null_count}
        )

    print(f"\n📈 Total Provider Tasks: {total_tasks:,}")

    # Tasks per provider
    print("\n👥 Tasks by Provider:")
    cursor = conn.execute(
        """
        SELECT provider_id, COUNT(*) as task_count
        FROM provider_tasks
        WHERE provider_id IS NOT NULL
        GROUP BY provider_id
        ORDER BY task_count DESC
    """
    )
    provider_rows = cursor.fetchall()

    for row in provider_rows:
        provider_name = get_staff_name(conn, row["provider_id"])
        print(f"   - {provider_name}: {row['task_count']:,} tasks")

    # Top months
    print("\n📅 Top 5 Months by Task Count:")
    monthly_stats_sorted = sorted(monthly_stats, key=lambda x: x["total"], reverse=True)
    for stat in monthly_stats_sorted[:5]:
        print(f"   {stat['month']}: {stat['total']:,} tasks")

    # NULL provider issues
    print("\n🚨 NULL provider_id Issues:")
    cursor = conn.execute(
        """
        SELECT DISTINCT patient_id, task_date, task_description
        FROM provider_tasks
        WHERE provider_id IS NULL
        LIMIT 10
    """
    )
    null_rows = cursor.fetchall()

    if null_rows:
        for row in null_rows:
            print(f"   - Patient: {row['patient_id']}, Date: {row['task_date']}")
    else:
        print("   ✅ No NULL provider_id found")

    return provider_tables


def report_coordinator_tasks(conn):
    """Generate coordinator tasks report"""
    print("\n" + "=" * 80)
    print("COORDINATOR TASKS ANALYSIS")
    print("=" * 80)

    coordinator_tables = get_table_list(conn, "coordinator_tasks_%")
    print(f"\nFound {len(coordinator_tables)} coordinator task tables")

    # Summary by month
    print("\n📊 Tasks by Month:")
    total_tasks = 0
    monthly_stats = []

    for table in coordinator_tables:
        # Count total per month
        cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
        month_total = cursor.fetchone()["count"]
        total_tasks += month_total

        # Count NULL coordinator_ids
        cursor = conn.execute(
            f"SELECT COUNT(*) as null_count FROM {table} WHERE coordinator_id IS NULL"
        )
        null_count = cursor.fetchone()["null_count"]

        month_label = table.replace("coordinator_tasks_", "").replace("_", "-")
        status = "⚠️" if null_count > 0 else "✅"
        print(
            f"   {status} {month_label}: {month_total:,} tasks ({null_count:,} NULL coordinator_id)"
        )

        monthly_stats.append(
            {"month": month_label, "total": month_total, "nulls": null_count}
        )

    print(f"\n📈 Total Coordinator Tasks: {total_tasks:,}")

    # Tasks per coordinator
    print("\n👥 Tasks by Coordinator:")
    cursor = conn.execute(
        """
        SELECT coordinator_id, COUNT(*) as task_count
        FROM coordinator_tasks
        WHERE coordinator_id IS NOT NULL
        GROUP BY coordinator_id
        ORDER BY task_count DESC
    """
    )
    coordinator_rows = cursor.fetchall()

    for row in coordinator_rows:
        coordinator_name = get_staff_name(conn, row["coordinator_id"])
        print(f"   - {coordinator_name}: {row['task_count']:,} tasks")

    # Top months
    print("\n📅 Top 5 Months by Task Count:")
    monthly_stats_sorted = sorted(monthly_stats, key=lambda x: x["total"], reverse=True)
    for stat in monthly_stats_sorted[:5]:
        print(f"   {stat['month']}: {stat['total']:,} tasks")

    # NULL coordinator issues
    print("\n🚨 NULL coordinator_id Issues:")
    cursor = conn.execute(
        """
        SELECT DISTINCT patient_id, task_date, task_type
        FROM coordinator_tasks
        WHERE coordinator_id IS NULL
        LIMIT 10
    """
    )
    null_rows = cursor.fetchall()

    if null_rows:
        for row in null_rows:
            print(
                f"   - Patient: {row['patient_id']}, Date: {row['task_date']}, Type: {row['task_type']}"
            )
    else:
        print("   ✅ No NULL coordinator_id found")

    return coordinator_tables


def report_staff_mappings(conn):
    """Report on staff code mappings"""
    print("\n" + "=" * 80)
    print("STAFF CODE MAPPINGS STATUS")
    print("=" * 80)

    cursor = conn.execute(
        """
        SELECT staff_code, user_id, mapping_type, confidence_level, notes
        FROM staff_code_mapping
        ORDER BY mapping_type, staff_code
    """
    )
    mappings = cursor.fetchall()

    print(f"\nTotal Mappings: {len(mappings)}")
    print("\n📋 Mappings by Type:")

    by_type = {}
    for row in mappings:
        mtype = row["mapping_type"]
        if mtype not in by_type:
            by_type[mtype] = []
        by_type[mtype].append(row)

    for mtype, rows in by_type.items():
        print(f"\n   {mtype} ({len(rows)}):")
        for row in rows[:5]:  # Show first 5 of each
            name = get_staff_name(conn, row["user_id"])
            print(
                f"      - {row['staff_code']} → {name} (confidence: {row['confidence_level']})"
            )
        if len(rows) > 5:
            print(f"      ... and {len(rows) - 5} more")

    # Unmatched staff codes
    print("\n🚨 Unmatched/Missing Mappings:")
    cursor = conn.execute(
        """
        SELECT staff_code FROM staff_code_mapping
        WHERE confidence_level IN ('UNMATCHED', 'LOW') OR user_id IS NULL
    """
    )
    unmatched = cursor.fetchall()

    if unmatched:
        for row in unmatched:
            print(f"   - {row['staff_code']} (unmatched)")
    else:
        print("   ✅ All mappings have valid user_id and confidence")


def compare_csv_to_db(conn):
    """Compare CSV file counts to database counts"""
    print("\n" + "=" * 80)
    print("CSV vs DATABASE COMPARISON")
    print("=" * 80)

    print("\n📁 Checking if CSV counts match database...")
    print("(Run python compare_csv_vs_database.py for full detailed comparison)")

    # Quick spot check for recent months
    recent_months = ["2025_10", "2025_11", "2025_12"]

    for month in recent_months:
        print(f"\n   {month.replace('_', '-')}:")

        # Provider tasks
        table = f"provider_tasks_{month}"
        cursor = conn.execute(f"SELECT COUNT(*) as count FROM {table}")
        db_count = cursor.fetchone()["count"]

        # Estimate CSV count (approximate)
        psl_files = glob.glob(os.path.join(CSV_DIR, "PSL_ZEN-*.csv"))
        csv_estimate = 0
        for file_path in psl_files:
            try:
                df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
                # Rough filter for month
                month_num = month.split("_")[1]
                year_short = month.split("_")[0][-2:]
                month_pattern = f"/{month_num}/{year_short}"
                month_rows = df[df["DOS"].astype(str).str.contains(month_pattern)]
                csv_estimate += len(month_rows)
            except:
                pass

        if db_count > 0:
            print(
                f"      ✅ Provider tasks: {db_count:,} in DB (CSV estimate: ~{csv_estimate:,})"
            )
        else:
            print(
                f"      ⚠️  Provider tasks: {db_count:,} in DB (CSV estimate: ~{csv_estimate:,}) - NO DATA!"
            )


def report_summary(conn):
    """Print executive summary"""
    print("\n" + "=" * 80)
    print("EXECUTIVE SUMMARY")
    print("=" * 80)

    cursor = conn.execute("SELECT COUNT(*) as count FROM provider_tasks")
    provider_total = cursor.fetchone()["count"]

    cursor = conn.execute("SELECT COUNT(*) as count FROM coordinator_tasks")
    coordinator_total = cursor.fetchone()["count"]

    cursor = conn.execute(
        "SELECT COUNT(*) as count FROM provider_tasks WHERE provider_id IS NULL"
    )
    provider_null = cursor.fetchone()["count"]

    cursor = conn.execute(
        "SELECT COUNT(*) as count FROM coordinator_tasks WHERE coordinator_id IS NULL"
    )
    coordinator_null = cursor.fetchone()["count"]

    print(f"\n📊 Overall Statistics:")
    print(f"   - Provider Tasks: {provider_total:,} total")
    print(f"   - Coordinator Tasks: {coordinator_total:,} total")
    print(f"   - Combined Total: {provider_total + coordinator_total:,} tasks")

    print(f"\n🚨 Issues Found:")
    if provider_null > 0:
        print(f"   ❌ {provider_null:,} provider tasks with NULL provider_id")
    else:
        print(f"   ✅ No NULL provider_id in provider tasks")
    if coordinator_null > 0:
        print(f"   ❌ {coordinator_null:,} coordinator tasks with NULL coordinator_id")
    else:
        print(f"   ✅ No NULL coordinator_id in coordinator tasks")

    # Recent month coverage
    print(f"\n📅 Recent Month Coverage:")
    cursor = conn.execute(
        "SELECT COUNT(*) as count FROM provider_tasks WHERE task_date >= '2025-10-01'"
    )
    recent_provider = cursor.fetchone()["count"]
    cursor = conn.execute(
        "SELECT COUNT(*) as count FROM coordinator_tasks WHERE task_date >= '2025-10-01'"
    )
    recent_coordinator = cursor.fetchone()["count"]
    print(f"   - Oct-Dec 2025 Provider Tasks: {recent_provider:,}")
    print(f"   - Oct-Dec 2025 Coordinator Tasks: {recent_coordinator:,}")

    print(f"\n✅ Data Quality Score:")
    score = 100
    if provider_null > 0:
        score -= (provider_null / provider_total) * 100
    if coordinator_null > 0:
        score -= (coordinator_null / coordinator_total) * 100

    if score >= 95:
        status = "EXCELLENT"
    elif score >= 85:
        status = "GOOD"
    elif score >= 70:
        status = "FAIR"
    else:
        status = "POOR"

    print(f"   {status}: {score:.1f}% complete mapping")


def main():
    """Main report generation"""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TASKS STATUS REPORT")
    print("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("Database:", DB_PATH)
    print("CSV Directory:", CSV_DIR)
    print("=" * 80)

    # Verify database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return

    conn = get_db_connection()

    try:
        # Generate all reports
        report_summary(conn)
        report_staff_mappings(conn)
        provider_tables = report_provider_tasks(conn)
        coordinator_tables = report_coordinator_tasks(conn)
        compare_csv_to_db(conn)

        # Final statistics
        print("\n" + "=" * 80)
        print("FINAL STATISTICS")
        print("=" * 80)
        print(f"✅ Provider Task Tables: {len(provider_tables)}")
        print(f"✅ Coordinator Task Tables: {len(coordinator_tables)}")
        print("\nReport Complete - Review issues above and take action as needed")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
