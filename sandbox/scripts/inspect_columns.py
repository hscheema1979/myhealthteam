import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / 'production.db'

tables = {
    'SOURCE_PATIENT_DATA': ['LAST', 'FIRST', 'DOB'],
    'SOURCE_COORDINATOR_TASKS_HISTORY': ['Pt Name'],
    'SOURCE_PROVIDER_TASKS_HISTORY': ['Patient Last, First DOB'],
}

def get_columns(conn, table):
    cur = conn.execute(f"PRAGMA table_info('{table}')")
    return [row[1] for row in cur.fetchall()]

def main():
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        sys.exit(2)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        for table, wanted in tables.items():
            print(f"Table: {table}")
            try:
                cols = get_columns(conn, table)
                print(' Columns in DB: ' + ', '.join(cols))
            except Exception as e:
                print(f"  ERROR reading table {table}: {e}")
            print(' Wanted columns to focus on: ' + ', '.join(wanted))
            print()
    finally:
        conn.close()

if __name__ == '__main__':
    main()
