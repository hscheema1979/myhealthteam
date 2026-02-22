#!/usr/bin/env python3
"""
Analyze duplicate columns across patient-related tables in the database.

Identifies columns that appear in multiple tables to help understand data redundancy
and potential consolidation opportunities.
"""

import sqlite3
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import database


def analyze_duplicate_columns(db_path=None):
    """
    Analyze columns across patient-related tables to find duplicates.

    Returns:
        dict: {column_name: [list of tables that have this column]}
    """
    conn = database.get_db_connection(db_path)

    try:
        # Main patient-related tables to analyze
        patient_tables = [
            'patients',
            'patient_panel',
            'onboarding_patients',
            'patient_assignments',
            'patient_assignment_history',
            'patient_visits',
        ]

        # Map columns to tables
        column_tables = defaultdict(list)

        for table_name in patient_tables:
            # Check if table exists
            table_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            ).fetchone()

            if not table_check:
                continue

            # Get all columns for this table
            columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()

            for col in columns:
                col_name = col['name']
                column_tables[col_name].append(table_name)

        # Filter to only columns that appear in multiple tables
        duplicates = {col: tables for col, tables in column_tables.items() if len(tables) > 1}

        return duplicates, column_tables

    finally:
        conn.close()


def print_duplicate_report(duplicates, column_tables):
    """Print a formatted report of duplicate columns."""

    print("=" * 80)
    print("DUPLICATE COLUMNS ACROSS PATIENT TABLES")
    print("=" * 80)
    print()

    if not duplicates:
        print("No duplicate columns found!")
        return

    # Group by number of tables
    by_count = defaultdict(list)
    for col, tables in duplicates.items():
        by_count[len(tables)].append((col, tables))

    # Sort by count (descending)
    for count in sorted(by_count.keys(), reverse=True):
        cols = sorted(by_count[count])
        print(f"\nColumns appearing in {count} table(s):")
        print("-" * 80)
        for col, tables in cols:
            tables_str = ", ".join(tables)
            print(f"  {col:40s} -> {tables_str}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total columns with duplicates: {len(duplicates)}")
    print(f"Total unique columns analyzed: {len(column_tables)}")
    print()

    # Most duplicated columns
    most_duped = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:20]
    print("Top 20 Most Common Columns Across Tables:")
    print("-" * 80)
    for col, tables in most_duped:
        print(f"  {col:40s} ({len(tables)} tables)")


def export_to_markdown(duplicates, output_file="docs/duplicate_columns_analysis.md"):
    """Export duplicate column analysis to markdown file."""

    md_content = """# Duplicate Columns Analysis

This document analyzes columns that appear in multiple patient-related tables.

## Tables Analyzed

- `patients` - Master patient table
- `patient_panel` - Denormalized view for dashboards
- `onboarding_patients` - Patient onboarding data
- `patient_assignments` - Current assignments
- `patient_assignment_history` - Assignment tracking
- `patient_visits` - Visit records

## Columns Found in Multiple Tables

"""

    # Group by number of tables
    by_count = defaultdict(list)
    for col, tables in duplicates.items():
        by_count[len(tables)].append((col, tables))

    for count in sorted(by_count.keys(), reverse=True):
        cols = sorted(by_count[count])
        md_content += f"\n### Columns in {count} Tables\n\n"
        for col, tables in cols:
            tables_str = ", ".join([f"`{t}`" for t in tables])
            md_content += f"- **{col}** → {tables_str}\n"

    md_content += f"\n---\n\n*Total: {len(duplicates)} duplicate columns found*\n"

    # Write to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content)

    print(f"\nMarkdown report saved to: {output_path}")


if __name__ == "__main__":
    print("Analyzing duplicate columns in patient-related tables...")
    print()

    duplicates, all_columns = analyze_duplicate_columns()

    if duplicates:
        print_duplicate_report(duplicates, all_columns)
        export_to_markdown(duplicates)
    else:
        print("No duplicate columns found.")
