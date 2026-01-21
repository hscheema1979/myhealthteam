#!/usr/bin/env python3
"""
Populate CSV Billing Summaries
Generates weekly and monthly billing summaries from csv_* tasks tables
"""

import sqlite3
import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src import database

DB_PATH = os.path.join(project_root, "production.db")

def get_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_summary_tables(conn, year, month):
    """Ensure summary tables exist for given month"""
    ym = f"{year}_{month:02d}"

    # Weekly summary table
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS csv_weekly_billing_summary_{ym} (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_id INTEGER NOT NULL,
            provider_name TEXT NOT NULL,
            week_start_date DATE NOT NULL,
            week_end_date DATE NOT NULL,
            year INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            billing_code TEXT,
            billing_code_description TEXT,
            task_type TEXT,
            total_tasks INTEGER DEFAULT 0,
            total_minutes INTEGER DEFAULT 0,
            total_hours REAL DEFAULT 0.0,
            unique_patients INTEGER DEFAULT 0,
            source_file TEXT,
            source_system TEXT DEFAULT 'CSV_IMPORT',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(provider_id, week_start_date, billing_code)
        )
    """)

    # Monthly summary table (coordinator + provider)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS csv_monthly_billing_summary_{ym} (
            summary_id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id INTEGER NOT NULL,
            staff_name TEXT NOT NULL,
            staff_type TEXT NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            billing_code TEXT,
            billing_code_description TEXT,
            task_type TEXT,
            total_tasks INTEGER DEFAULT 0,
            total_minutes INTEGER DEFAULT 0,
            total_hours REAL DEFAULT 0.0,
            unique_patients INTEGER DEFAULT 0,
            source_file TEXT,
            source_system TEXT DEFAULT 'CSV_IMPORT',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(staff_id, staff_type, year, month, billing_code, task_type)
        )
    """)

def populate_provider_weekly_summary(conn, year, month):
    """Populate csv_weekly_billing_summary from csv_provider_tasks data"""
    ym = f"{year}_{month:02d}"
    source_table = f"csv_provider_tasks_{ym}"
    summary_table = f"csv_weekly_billing_summary_{ym}"

    print(f"  Populating {summary_table} from {source_table}...")

    cursor = conn.cursor()

    # Check if source table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (source_table,))
    if not cursor.fetchone():
        print(f"    Source table {source_table} not found, skipping")
        return 0

    # Ensure summary table exists
    ensure_summary_tables(conn, year, month)

    # Populate weekly summaries
    cursor.execute(f"""
        INSERT OR REPLACE INTO {summary_table}
        (provider_id, provider_name, week_start_date, week_end_date,
         year, week_number, billing_code, task_type,
         total_tasks, total_minutes, total_hours, unique_patients,
         source_file, updated_date)
        SELECT
            staff_id as provider_id,
            staff_name as provider_name,
            date(task_date, 'weekday 0', '-6 days') as week_start_date,
            date(task_date, 'weekday 0', '-0 days') as week_end_date,
            CAST(strftime('%Y', task_date) AS INTEGER) as year,
            CAST(strftime('%W', task_date) AS INTEGER) as week_number,
            billing_code,
            task_type,
            COUNT(*) as total_tasks,
            CAST(SUM(duration_minutes) AS INTEGER) as total_minutes,
            ROUND(SUM(duration_minutes) / 60.0, 2) as total_hours,
            COUNT(DISTINCT patient_id) as unique_patients,
            MAX(source_file) as source_file,
            datetime('now') as updated_date
        FROM {source_table}
        WHERE staff_id IS NOT NULL AND duration_minutes > 0
        GROUP BY staff_id, staff_name,
                 strftime('%Y', task_date), strftime('%W', task_date),
                 billing_code, task_type
    """)

    count = cursor.rowcount
    conn.commit()
    print(f"    Inserted/updated {count} weekly summary records")
    return count

def populate_monthly_summary(conn, year, month):
    """Populate csv_monthly_billing_summary from both coordinator and provider CSV data"""
    ym = f"{year}_{month:02d}"
    summary_table = f"csv_monthly_billing_summary_{ym}"

    print(f"  Populating {summary_table}...")

    cursor = conn.cursor()

    # Ensure summary table exists
    ensure_summary_tables(conn, year, month)

    # Delete existing data for this month to avoid duplicates
    # (NULL billing_code doesn't enforce uniqueness properly)
    cursor.execute(f"DELETE FROM {summary_table} WHERE year = ? AND month = ?", (year, month))
    conn.commit()

    total_count = 0

    # Process coordinator tasks
    coord_source = f"csv_coordinator_tasks_{ym}"
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (coord_source,))
    if cursor.fetchone():
        print(f"    Processing coordinator data from {coord_source}...")
        cursor.execute(f"""
            INSERT INTO {summary_table}
            (staff_id, staff_name, staff_type, year, month,
             task_type, total_tasks, total_minutes, total_hours, unique_patients,
             source_file, updated_date)
            SELECT
                staff_id,
                staff_name,
                'coordinator' as staff_type,
                {month} as month,
                {year} as year,
                task_type,
                COUNT(*) as total_tasks,
                CAST(SUM(duration_minutes) AS INTEGER) as total_minutes,
                ROUND(SUM(duration_minutes) / 60.0, 2) as total_hours,
                COUNT(DISTINCT patient_id) as unique_patients,
                MAX(source_file) as source_file,
                datetime('now') as updated_date
            FROM {coord_source}
            WHERE staff_id IS NOT NULL AND duration_minutes > 0
            GROUP BY staff_id, staff_name, task_type
        """)
        count = cursor.rowcount
        total_count += count
        print(f"      {count} coordinator records")

    # Process provider tasks
    prov_source = f"csv_provider_tasks_{ym}"
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (prov_source,))
    if cursor.fetchone():
        print(f"    Processing provider data from {prov_source}...")
        cursor.execute(f"""
            INSERT INTO {summary_table}
            (staff_id, staff_name, staff_type, year, month,
             billing_code, task_type, total_tasks, total_minutes, total_hours,
             unique_patients, source_file, updated_date)
            SELECT
                staff_id,
                staff_name,
                'provider' as staff_type,
                {month} as month,
                {year} as year,
                billing_code,
                task_type,
                COUNT(*) as total_tasks,
                CAST(SUM(duration_minutes) AS INTEGER) as total_minutes,
                ROUND(SUM(duration_minutes) / 60.0, 2) as total_hours,
                COUNT(DISTINCT patient_id) as unique_patients,
                MAX(source_file) as source_file,
                datetime('now') as updated_date
            FROM {prov_source}
            WHERE staff_id IS NOT NULL AND duration_minutes > 0
            GROUP BY staff_id, staff_name, billing_code, task_type
        """)
        count = cursor.rowcount
        total_count += count
        print(f"      {count} provider records")

    conn.commit()
    print(f"    Total: {total_count} monthly summary records")
    return total_count

def populate_all_for_month(conn, year, month):
    """Populate all summaries for a given month"""
    ym = f"{year}_{month:02d}"
    print(f"Processing {ym}...")

    weekly_count = populate_provider_weekly_summary(conn, year, month)
    monthly_count = populate_monthly_summary(conn, year, month)

    return weekly_count, monthly_count

def main():
    print("=" * 60)
    print("Populate CSV Billing Summaries")
    print("=" * 60)

    conn = get_connection()

    # Get all available CSV months
    cursor = conn.cursor()

    # Coordinator tables
    cursor.execute("""
        SELECT DISTINCT substr(name, 22, 7) as ym
        FROM sqlite_master
        WHERE type='table' AND name LIKE 'csv_coordinator_tasks_%'
        ORDER BY ym DESC
    """)
    coord_months = [row[0] for row in cursor.fetchall()]

    # Provider tables
    cursor.execute("""
        SELECT DISTINCT substr(name, 20, 7) as ym
        FROM sqlite_master
        WHERE type='table' AND name LIKE 'csv_provider_tasks_%'
        ORDER BY ym DESC
    """)
    prov_months = [row[0] for row in cursor.fetchall()]

    all_months = sorted(set(coord_months + prov_months))
    print(f"Found CSV data for months: {all_months}")
    print()

    total_weekly = 0
    total_monthly = 0

    for ym in all_months:
        if not ym or not ym.replace('_', '').isdigit():
            continue
        parts = ym.split('_')
        if len(parts) != 2:
            continue
        year, month = parts
        try:
            year, month = int(year), int(month)
        except ValueError:
            continue

        weekly, monthly = populate_all_for_month(conn, year, month)
        total_weekly += weekly
        total_monthly += monthly
        print()

    conn.close()

    print("=" * 60)
    print(f"Complete!")
    print(f"  Total weekly records: {total_weekly}")
    print(f"  Total monthly records: {total_monthly}")
    print("=" * 60)

if __name__ == "__main__":
    main()
