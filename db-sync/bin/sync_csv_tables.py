#!/usr/bin/env python3
"""
Sync csv_* billing tables from Dev to VPS2
Safely syncs ONLY csv_* tables - never touches operational tables
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

# Configuration
DEV_DB = "D:/Git/myhealthteam2/Dev/production.db"
VPS_HOST = "server2"
VPS_DB = "/opt/myhealthteam/production.db"
SSH_KEY = None  # Uses default SSH key

def run_ssh(command):
    """Run SSH command and return output"""
    full_cmd = f"ssh {VPS_HOST} '{command}'"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode

def run_scp(local_path, remote_path):
    """Copy file to remote via SCP"""
    full_cmd = f"scp '{local_path}' {VPS_HOST}:{remote_path}"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.returncode

def sync_table(table_name, dev_conn):
    """Sync a single csv_* table to VPS2"""
    # Get table schema
    cursor = dev_conn.cursor()
    schema = cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone()
    if not schema:
        print(f"  WARNING: Schema not found for {table_name}")
        return False

    schema_sql = schema[0]

    # Get row count
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    if count == 0:
        print(f"  Skipping {table_name} (empty)")
        return True

    print(f"  Syncing {table_name}: {count} rows")

    # Create export SQL
    export_lines = []
    export_lines.append("BEGIN TRANSACTION;")
    export_lines.append("DROP TABLE IF EXISTS " + table_name + ";")
    export_lines.append(schema_sql + ";")

    # Get all rows and create INSERT statements
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    for row in rows:
        # Build VALUES clause with proper escaping
        values = []
        for value in row:
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                # Escape single quotes
                escaped = value.replace("'", "''")
                values.append(f"'{escaped}'")
            elif isinstance(value, bytes):
                # Handle BLOB data as hex
                hex_value = value.hex()
                values.append(f"X'{hex_value}'")
            else:
                values.append(str(value))

        export_lines.append(f"INSERT INTO {table_name} VALUES ({','.join(values)});")

    export_lines.append("COMMIT;")
    export_sql = "\n".join(export_lines)

    # Write to temp file
    temp_file = Path(f"/tmp/{table_name}_sync.sql")
    temp_file.write_text(export_sql, encoding='utf-8')

    # Upload to VPS2
    remote_temp = f"/tmp/{table_name}_sync.sql"
    if run_scp(str(temp_file), remote_temp) != 0:
        print(f"  FAILED to upload {table_name}")
        temp_file.unlink()
        return False

    # Execute on VPS2 - use sqlite3 with input redirection
    # Note: Using bash -c to properly handle the redirection
    sql_cmd = f"bash -c \"sqlite3 {VPS_DB} < {remote_temp}\""
    stdout, stderr, rc = run_ssh(sql_cmd)

    # Cleanup
    run_ssh(f"rm -f {remote_temp}")
    temp_file.unlink()

    if rc != 0:
        print(f"  FAILED to execute on VPS2: {stderr}")
        return False

    print(f"  OK: {count} rows synced")
    return True

def main():
    print("=" * 60)
    print("CSV Billing Tables Sync - Python Version")
    print("=" * 60)
    print(f"Source: {DEV_DB}")
    print(f"Target: {VPS_HOST}:{VPS_DB}")
    print()

    # Connect to dev database
    dev_conn = sqlite3.connect(DEV_DB)
    dev_conn.row_factory = sqlite3.Row
    cursor = dev_conn.cursor()

    # Get all csv_* tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'csv_%' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"Found {len(tables)} csv_* tables")
    print()

    # Sync each table
    success_count = 0
    fail_count = 0

    for table in tables:
        if sync_table(table, dev_conn):
            success_count += 1
        else:
            fail_count += 1

    dev_conn.close()

    print()
    print("=" * 60)
    print(f"Sync Complete: {success_count} succeeded, {fail_count} failed")
    print("=" * 60)

    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
