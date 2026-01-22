#!/usr/bin/env python3
"""
Sync CSV Task Tables from Dev to VPS2
Uses the same approach as sync_csv_summaries.py (which works reliably)
"""

import sqlite3
import subprocess
import sys
import os
from pathlib import Path

DEV_DB = "D:/Git/myhealthteam2/Dev/production.db"
VPS_HOST = "server2"
VPS_DB = "/opt/myhealthteam/production.db"

# Use bash.exe on Windows for ssh/scp commands
SHELL = os.environ.get('MSYSTEM', None) and "bash" or None
if os.name == 'nt':  # Windows
    # Try to find bash.exe in Git for Windows or WSL
    for path in [
        r"C:\Program Files\Git\bin\bash.exe",
        r"C:\Program Files\Git\usr\bin\bash.exe",
        r"C:\msys64\usr\bin\bash.exe",
    ]:
        if os.path.exists(path):
            SHELL = path
            break

def run_ssh(command):
    if SHELL:
        cmd = [SHELL, "-lc", f"ssh {VPS_HOST} '{command}'"]
    else:
        cmd = ["ssh", VPS_HOST, command]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def run_scp(local, remote):
    if SHELL:
        cmd = [SHELL, "-lc", f"scp '{local}' {VPS_HOST}:'{remote}'"]
    else:
        cmd = ["scp", local, f"{VPS_HOST}:{remote}"]
    return subprocess.run(cmd, capture_output=True, text=True)

def sync_table(table_name, dev_conn):
    """Sync a CSV task table to VPS2"""
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

    print(f"    Exporting {count} rows...")

    # Build export SQL
    export_lines = [
        "BEGIN TRANSACTION;",
        f"DROP TABLE IF EXISTS {table_name};",
        schema[0] + ";"
    ]

    # Fetch all rows and build INSERT statements
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    for row in rows:
        values = []
        for value in row:
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                # Escape single quotes by doubling them
                escaped = value.replace("'", "''")
                values.append(f"'{escaped}'")
            else:
                values.append(str(value))
        export_lines.append(f"INSERT INTO {table_name} VALUES ({','.join(values)});")

    export_lines.append("COMMIT;")
    export_sql = "\n".join(export_lines)

    # Write temp file locally
    temp_file = Path(f"D:/Git/myhealthteam2/Dev/db-sync/temp/{table_name}_sync.sql")
    temp_file.parent.mkdir(exist_ok=True)
    temp_file.write_text(export_sql, encoding='utf-8')

    # Upload and execute
    remote_temp = f"/tmp/{table_name}_sync.sql"

    # Upload via SCP
    scp_result = run_scp(str(temp_file), remote_temp)

    if scp_result.returncode != 0:
        print(f"    FAILED to upload: {scp_result.stderr}")
        temp_file.unlink()
        return False

    # Execute on VPS2
    stdout, stderr, rc = run_ssh(f"sqlite3 {VPS_DB} < {remote_temp}")
    run_ssh(f"rm -f {remote_temp}")
    temp_file.unlink()

    if rc != 0:
        print(f"    FAILED: {stderr[:200]}")
        return False

    # Verify row count
    verify_cmd = f"sqlite3 {VPS_DB} \"SELECT COUNT(*) FROM {table_name}\""
    v_stdout, _, _ = run_ssh(verify_cmd)
    remote_count = int(v_stdout) if v_stdout.isdigit() else 0

    if remote_count == count:
        print(f"    OK: {count} rows")
        return True
    else:
        print(f"    WARNING: count mismatch local={count}, remote={remote_count}")
        return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Sync CSV task tables to VPS2')
    parser.add_argument('--all', action='store_true', help='Sync all CSV task tables')
    parser.add_argument('--month', type=str, help='Specific month (format: 2025_12)')
    args = parser.parse_args()

    print("=" * 60)
    print("CSV Task Tables Sync to VPS2")
    print("=" * 60)

    conn = sqlite3.connect(DEV_DB)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    if args.all:
        # Get all CSV task tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND (name LIKE 'csv_coordinator_tasks_%' OR name LIKE 'csv_provider_tasks_%')
            ORDER BY name DESC
        """)
        tables = [row[0] for row in cursor.fetchall()]
    elif args.month:
        # Get tables for specific month
        coord_table = f"csv_coordinator_tasks_{args.month}"
        prov_table = f"csv_provider_tasks_{args.month}"
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN (?, ?)
            ORDER BY name
        """, (coord_table, prov_table))
        tables = [row[0] for row in cursor.fetchall()]
    else:
        # Get current month tables
        from datetime import datetime
        current_month = datetime.now().strftime("%Y_%m")
        coord_table = f"csv_coordinator_tasks_{current_month}"
        prov_table = f"csv_provider_tasks_{current_month}"
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN (?, ?)
            ORDER BY name
        """, (coord_table, prov_table))
        tables = [row[0] for row in cursor.fetchall()]

    if not tables:
        print("No CSV task tables found to sync")
        conn.close()
        return 0

    print(f"Found {len(tables)} CSV task tables")

    success = 0
    failed = 0
    for table in tables:
        if sync_table(table, conn):
            success += 1
        else:
            failed += 1

    conn.close()

    print()
    print("=" * 60)
    print(f"Complete! Success: {success}, Failed: {failed}")
    print("=" * 60)
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
