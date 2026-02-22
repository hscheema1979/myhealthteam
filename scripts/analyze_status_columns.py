#!/usr/bin/env python3
"""
Analyze status column values across all patient-related tables.

Identifies unique status values, counts, and data quality issues.
"""

import sqlite3
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import database


def analyze_status_columns(db_path=None):
    """Analyze status values across all patient tables."""
    conn = database.get_db_connection(db_path)

    try:
        # Define tables and their status columns
        status_configs = {
            'patients': 'status',
            'patient_panel': 'status',
            'onboarding_patients': 'patient_status',
            'patient_assignments': 'status',
        }

        all_status_data = {}
        total_patients = 0

        for table_name, status_col in status_configs.items():
            # Check if table exists
            table_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            ).fetchone()

            if not table_check:
                continue

            # Get status counts
            try:
                results = conn.execute(
                    f"SELECT {status_col}, COUNT(*) as count FROM {table_name} GROUP BY {status_col} ORDER BY count DESC"
                ).fetchall()

                all_status_data[table_name] = results
                total_patients += sum(r[1] for r in results)

            except Exception as e:
                print(f"Error querying {table_name}: {e}")
                continue

        return all_status_data, total_patients

    finally:
        conn.close()


def print_status_report(all_status_data, total_patients):
    """Print formatted status analysis report."""

    print("=" * 100)
    print("STATUS COLUMN ANALYSIS ACROSS PATIENT TABLES")
    print("=" * 100)
    print()

    # Summary by table
    for table_name, status_data in all_status_data.items():
        table_total = sum(s[1] for s in status_data)
        print(f"\n{table_name.upper()} ({table_total} patients)")
        print("-" * 100)

        for status, count in status_data:
            if status is None:
                status = "(empty)"
            pct = (count / table_total * 100) if table_total > 0 else 0
            bar = "#" * int(pct / 2)
            print(f"  {status:40s} | {count:5d} | {pct:5.1f}%  {bar}")

    # Cross-table comparison
    print("\n" + "=" * 100)
    print("CROSS-TABLE STATUS COMPARISON")
    print("=" * 100)
    print()

    # Get all unique statuses across tables
    all_statuses = set()
    for status_data in all_status_data.values():
        for status, _ in status_data:
            all_statuses.add(status)

    # Sort by status (case-insensitive)
    sorted_statuses = sorted(all_statuses, key=lambda x: (x.lower() if x else ""))

    print(f"Found {len(sorted_statuses)} unique status values across all tables:\n")
    for status in sorted_statuses:
        present_in = []
        for table_name, status_data in all_status_data.items():
            status_dict = {s: c for s, c in status_data}
            count = status_dict.get(status, 0)
            if count > 0:
                present_in.append(f"{table_name}({count})")

        if present_in:
            print(f"  {status:40s} -> {', '.join(present_in)}")

    # Data quality issues
    print("\n" + "=" * 100)
    print("DATA QUALITY ISSUES")
    print("=" * 100)
    print()

    issues = []

    # Check for statuses with typos (extra spaces)
    for table_name, status_data in all_status_data.items():
        for status, count in status_data:
            if status and '  ' in status:  # Extra spaces
                issues.append(f"{table_name}: '{status}' has extra spaces")
            elif status and status != status.strip():  # Leading/trailing spaces
                issues.append(f"{table_name}: '{status}' has leading/trailing spaces")

    # Check for inconsistent casing
    status_lower_map = defaultdict(list)
    for table_name, status_data in all_status_data.items():
        for status, count in status_data:
            if status:
                status_lower_map[status.lower()].append((status, table_name, count))

    for status_lower, variations in status_lower_map.items():
        if len(variations) > 1:  # Different casings for same status
            issue_str = f"Inconsistent casing for '{status_lower}': "
            for status, table, count in variations:
                issue_str += f"{table}.{status}({count}) "
            issues.append(issue_str)

    if issues:
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("  No obvious data quality issues found!")

    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total patients across all tables: {total_patients}")
    print(f"Unique status values: {len(sorted_statuses)}")


if __name__ == "__main__":
    print("Analyzing status columns across patient tables...\n")
    all_status, total = analyze_status_columns()
    print_status_report(all_status, total)
