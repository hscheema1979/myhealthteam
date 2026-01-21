#!/usr/bin/env python3
"""
Sync summary tables from Dev to VPS2
After daily_summary_update.py runs, sync the results to VPS2
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

# Configuration
DEV_DB = "D:/Git/myhealthteam2/Dev/production.db"
VPS_HOST = "server2"
VPS_DB = "/opt/myhealthteam/production.db"

SUMMARY_TABLES = [
    "provider_weekly_summary_with_billing",
    "provider_weekly_payroll_status",
    "coordinator_monthly_summary",
]

def run_ssh(command):
    """Run SSH command and return output"""
    full_cmd = f"ssh {VPS_HOST} '{command}'"
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def sync_table(table_name, dev_conn):
    """Sync a single summary table to VPS2"""
    print(f"  Syncing {table_name}...")

    cursor = dev_conn.cursor()

    # Get table schema
    schema = cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone()
    if not schema:
        print(f"    WARNING: Schema not found for {table_name}")
        return False

    schema_sql = schema[0]

    # Get row count
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    if count == 0:
        print(f"    Skipping {table_name} (empty)")
        return True

    print(f"    {count} rows to sync")

    # Create export SQL - drop, recreate, and insert
    export_lines = []
    export_lines.append("BEGIN TRANSACTION;")
    export_lines.append(f"DROP TABLE IF EXISTS {table_name};")
    export_lines.append(schema_sql + ";")

    # Get all rows
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    for row in rows:
        values = []
        for value in row:
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                escaped = value.replace("'", "''")
                values.append(f"'{escaped}'")
            elif isinstance(value, bytes):
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
    scp_cmd = f"scp '{temp_file}' {VPS_HOST}:{remote_temp}"
    result = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    FAILED to upload")
        temp_file.unlink()
        return False

    # Execute on VPS2
    sql_cmd = f"bash -c \"sqlite3 {VPS_DB} < {remote_temp}\""
    stdout, stderr, rc = run_ssh(sql_cmd)

    # Cleanup
    run_ssh(f"rm -f {remote_temp}")
    temp_file.unlink()

    if rc != 0:
        print(f"    FAILED to execute: {stderr}")
        return False

    print(f"    OK: {count} rows synced")
    return True

def main():
    print("=" * 60)
    print("Summary Tables Sync to VPS2")
    print("=" * 60)

    # Connect to dev database
    dev_conn = sqlite3.connect(DEV_DB)
    dev_conn.row_factory = sqlite3.Row

    success_count = 0
    fail_count = 0

    for table in SUMMARY_TABLES:
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
