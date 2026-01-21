#!/usr/bin/env python3
"""
Sync CSV Billing Summaries from Dev to VPS2
"""

import sqlite3
import subprocess
import sys
from pathlib import Path

DEV_DB = "D:/Git/myhealthteam2/Dev/production.db"
VPS_HOST = "server2"
VPS_DB = "/opt/myhealthteam/production.db"

def run_ssh(command):
    result = subprocess.run(f"ssh {VPS_HOST} '{command}'", shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def sync_summary_table(table_name, dev_conn):
    """Sync a CSV summary table to VPS2"""
    print(f"  Syncing {table_name}...")

    cursor = dev_conn.cursor()

    # Get schema
    schema = cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone()
    if not schema:
        print(f"    Schema not found")
        return False

    # Get row count
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    if count == 0:
        print(f"    Skipping (empty)")
        return True

    # Build export SQL
    export_lines = ["BEGIN TRANSACTION;", f"DROP TABLE IF EXISTS {table_name};", schema[0] + ";"]

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
            else:
                values.append(str(value))
        export_lines.append(f"INSERT INTO {table_name} VALUES ({','.join(values)});")

    export_lines.append("COMMIT;")
    export_sql = "\n".join(export_lines)

    # Write temp file
    temp_file = Path(f"/tmp/{table_name}_sync.sql")
    temp_file.write_text(export_sql, encoding='utf-8')

    # Upload and execute
    remote_temp = f"/tmp/{table_name}_sync.sql"
    subprocess.run(f"scp '{temp_file}' {VPS_HOST}:{remote_temp}", shell=True, capture_output=True)

    stdout, stderr, rc = run_ssh(f"bash -c \"sqlite3 {VPS_DB} < {remote_temp}\"")
    run_ssh(f"rm -f {remote_temp}")
    temp_file.unlink()

    if rc != 0:
        print(f"    FAILED: {stderr}")
        return False

    print(f"    OK: {count} rows")
    return True

def main():
    print("Syncing CSV Billing Summaries to VPS2...")

    conn = sqlite3.connect(DEV_DB)
    conn.row_factory = sqlite3.Row

    # Get all CSV summary tables
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'csv_%_billing_summary%'
        ORDER BY name DESC
    """)
    tables = [row[0] for row in cursor.fetchall()]

    print(f"Found {len(tables)} CSV summary tables")

    success = 0
    for table in tables:
        if sync_summary_table(table, conn):
            success += 1

    conn.close()

    print(f"\nSynced: {success}/{len(tables)} tables")
    return 0 if success == len(tables) else 1

if __name__ == "__main__":
    sys.exit(main())
