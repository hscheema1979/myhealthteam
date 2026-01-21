#!/usr/bin/env python3
"""
Generate correct UNION ALL views for VPS2 database
Automatically detects table schemas and creates compatible views
"""

import subprocess
import sys

VPS_HOST = "server2"
VPS_DB = "/opt/myhealthteam/production.db"

def run_ssh(command):
    """Run SSH command and return output"""
    full_cmd = f"ssh {VPS_HOST} '{command}'"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr, result.returncode

def get_table_schema(table_name):
    """Get column names for a table"""
    cmd = f'sqlite3 {VPS_DB} "PRAGMA table_info({table_name});"'
    full_cmd = f"ssh {VPS_HOST} {cmd!r}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    stdout = result.stdout.strip()

    columns = []
    for line in stdout.split('\n'):
        if not line:
            continue
        parts = line.split('|')
        if len(parts) >= 2:
            columns.append(parts[1])

    return columns

def get_all_coordinator_tables():
    """Get all coordinator_tasks tables"""
    cmd = f'sqlite3 {VPS_DB} "SELECT name FROM sqlite_master WHERE type=\'table\' AND name LIKE \'coordinator_tasks_%\' ORDER BY name;"'
    full_cmd = f"ssh {VPS_HOST} {cmd!r}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return [line for line in result.stdout.strip().split('\n') if line]

def get_all_provider_tables():
    """Get all provider_tasks tables"""
    cmd = f'sqlite3 {VPS_DB} "SELECT name FROM sqlite_master WHERE type=\'table\' AND name LIKE \'provider_tasks_%\' ORDER BY name;"'
    full_cmd = f"ssh {VPS_HOST} {cmd!r}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return [line for line in result.stdout.strip().split('\n') if line]

def get_coordinator_view_schema():
    """Get the union of all columns across coordinator tables"""
    tables = get_all_coordinator_tables()

    all_columns = set()
    table_columns = {}

    for table in tables:
        cols = get_table_schema(table)
        table_columns[table] = cols
        all_columns.update(cols)

    # Define the canonical column order
    canonical_order = [
        'coordinator_task_id',
        'coordinator_id',
        'coordinator_name',
        'patient_id',
        'task_date',
        'duration_minutes',
        'task_type',
        'notes',
        'source_system',
        'imported_at',
        'submission_status',
        'created_at_pst',
        'task_id'
    ]

    # Filter to only columns that exist in at least one table
    final_columns = [c for c in canonical_order if c in all_columns]

    return final_columns, table_columns

def get_provider_view_schema():
    """Get the union of all columns across provider tables"""
    tables = get_all_provider_tables()

    all_columns = set()
    table_columns = {}

    for table in tables:
        cols = get_table_schema(table)
        table_columns[table] = cols
        all_columns.update(cols)

    # Group tables by schema
    schema_groups = {}
    for table, cols in table_columns.items():
        cols_tuple = tuple(cols)
        if cols_tuple not in schema_groups:
            schema_groups[cols_tuple] = []
        schema_groups[cols_tuple].append(table)

    return schema_groups, table_columns

def generate_coordinator_view():
    """Generate coordinator_tasks view SQL"""
    print("=" * 70)
    print("GENERATING coordinator_tasks VIEW")
    print("=" * 70)

    final_columns, table_columns = get_coordinator_view_schema()

    print(f"\nCanonical columns ({len(final_columns)}):")
    for i, col in enumerate(final_columns):
        print(f"  {i}: {col}")

    # Group tables by which columns they have
    table_groups = {}
    for table, cols in table_columns.items():
        missing = [c for c in final_columns if c not in cols]
        has = [c for c in final_columns if c in cols]
        key = tuple(missing)  # Group by which columns are missing
        if key not in table_groups:
            table_groups[key] = {'tables': [], 'has': has, 'missing': missing}
        table_groups[key]['tables'].append(table)

    print(f"\nFound {len(table_groups)} schema groups:")
    for i, (missing, info) in enumerate(table_groups.items()):
        print(f"  Group {i}: {len(info['tables'])} tables, missing {list(missing)}")
        for t in sorted(info['tables']):
            print(f"    - {t}")

    # Generate the view
    sql_lines = []
    sql_lines.append("-- Coordinator Tasks View")
    sql_lines.append("-- Auto-generated to handle schema differences")
    sql_lines.append("DROP VIEW IF EXISTS coordinator_tasks;")
    sql_lines.append("CREATE VIEW coordinator_tasks AS")

    first = True
    for missing, info in sorted(table_groups.items()):
        for table in sorted(info['tables']):
            if first:
                first = False
            else:
                sql_lines.append("UNION ALL")

            select_cols = info['has'] + [f"NULL as {c}" for c in info['missing']]
            sql_lines.append(f"SELECT {', '.join(select_cols)}")
            sql_lines.append(f"FROM {table}")

    return '\n'.join(sql_lines)

def generate_provider_view():
    """Generate provider_tasks view SQL"""
    print("\n" + "=" * 70)
    print("GENERATING provider_tasks VIEW")
    print("=" * 70)

    schema_groups, table_columns = get_provider_view_schema()

    print(f"\nFound {len(schema_groups)} unique schemas:")
    for i, (cols_tuple, tables) in enumerate(sorted(schema_groups.items())):
        print(f"\nSchema {i} ({len(cols_tuple)} columns, {len(tables)} tables):")
        for col in cols_tuple:
            print(f"  - {col}")
        print(f"Tables:")
        for t in sorted(tables):
            print(f"  - {t}")

    # Find the most common schema to use as the base (but skip 2026_01)
    # Exclude 2026_01 from table_columns before processing
    table_columns_filtered = {k: v for k, v in table_columns.items() if k != 'provider_tasks_2026_01'}

    # Rebuild schema groups without 2026_01
    schema_groups_filtered = {}
    for table, cols in table_columns_filtered.items():
        cols_tuple = tuple(cols)
        if cols_tuple not in schema_groups_filtered:
            schema_groups_filtered[cols_tuple] = []
        schema_groups_filtered[cols_tuple].append(table)

    if not schema_groups_filtered:
        print("ERROR: No compatible provider tables found")
        return "-- ERROR: No compatible provider tables"

    most_common = max(schema_groups_filtered.items(), key=lambda x: len(x[1]))
    base_columns = list(most_common[0])

    print(f"\nUsing most common schema with {len(base_columns)} columns:")

    # Group all tables by missing columns relative to base schema
    table_groups = {}
    for table, cols in table_columns_filtered.items():
        missing = [c for c in base_columns if c not in cols]
        key = tuple(missing)
        if key not in table_groups:
            table_groups[key] = {'tables': [], 'has': [c for c in base_columns if c in cols]}
        table_groups[key]['tables'].append(table)

    print(f"\nFound {len(table_groups)} groups relative to base schema:")

    # Generate the view
    sql_lines = []
    sql_lines.append("\n-- Provider Tasks View")
    sql_lines.append("-- Auto-generated to handle schema differences")
    sql_lines.append("-- Note: Tables with incompatible schemas are excluded")
    sql_lines.append("DROP VIEW IF EXISTS provider_tasks;")
    sql_lines.append("CREATE VIEW provider_tasks AS")

    first = True
    for missing, info in sorted(table_groups.items()):
        # Skip tables that are missing too many columns (incompatible)
        if len(missing) > 5:
            print(f"  EXCLUDING {len(info['tables'])} tables with {len(missing)} missing columns")
            continue

        print(f"  Group with {len(missing)} missing columns: {len(info['tables'])} tables")

        for table in sorted(info['tables']):
            if first:
                first = False
            else:
                sql_lines.append("UNION ALL")

            select_cols = info['has'] + [f"NULL as {c}" for c in missing]
            sql_lines.append(f"SELECT {', '.join(select_cols)}")
            sql_lines.append(f"FROM {table}")

    # List excluded tables
    excluded = []
    for missing, info in table_groups.items():
        if len(missing) > 5:
            excluded.extend(info['tables'])

    if excluded:
        sql_lines.append("\n-- Excluded tables (incompatible schema):")
        for t in sorted(excluded):
            sql_lines.append(f"--   {t}")

    return '\n'.join(sql_lines)

def main():
    print("VPS2 View Generator")
    print("=" * 70)

    # Test connection
    cmd = f'sqlite3 {VPS_DB} "SELECT 1;"'
    full_cmd = f"ssh {VPS_HOST} {cmd!r}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: Cannot connect to VPS2 database: {result.stderr}")
        return 1

    print(f"Connected to {VPS_HOST}:{VPS_DB}\n")

    # Generate coordinator view
    coord_sql = generate_coordinator_view()

    # Generate provider view
    prov_sql = generate_provider_view()

    # Combine and output
    full_sql = "BEGIN;\n" + coord_sql + ";\n" + prov_sql + ";\nCOMMIT;"

    # Write to file
    output_file = "D:/Git/myhealthteam2/Dev/db-sync/bin/migration_phase2e_auto_views.sql"
    with open(output_file, 'w') as f:
        f.write(full_sql)

    print(f"\n{'=' * 70}")
    print(f"View SQL written to: {output_file}")
    print("=" * 70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
