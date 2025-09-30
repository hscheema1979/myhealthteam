# export_table_month_to_csv.py
"""
Export a table's data for a specific year and month to CSV from production.db
Usage:
    python export_table_month_to_csv.py <table_name> <year> <month> <output_csv>

Example:
    python export_table_month_to_csv.py coordinator_tasks 2025 09 exports/coordinator_tasks_2025_09.csv
"""
import sys
import sqlite3
import pandas as pd
from pathlib import Path

if len(sys.argv) != 5:
    print("Usage: python export_table_month_to_csv.py <table_name> <year> <month> <output_csv>")
    sys.exit(1)

table = sys.argv[1]
year = sys.argv[2]
month = sys.argv[3]
outfile = sys.argv[4]

db_path = str(Path(__file__).resolve().parent.parent.parent / "production.db")

# Table must have a date column (e.g., 'date', 'task_date', or 'created_at')
# We'll try to infer the date column name
DATE_COLUMNS = ["date", "task_date", "created_at", "service_date", "admit_date"]

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Find the date column
cursor = conn.execute(f"PRAGMA table_info({table})")
columns = [row[1] for row in cursor.fetchall()]
date_col = None
for col in DATE_COLUMNS:
    if col in columns:
        date_col = col
        break
if not date_col:
    print(f"No date column found in {table}. Columns: {columns}")
    sys.exit(1)

# Query for the given year and month (assume date format is YYYY-MM-DD or similar)
query = f"SELECT * FROM {table} WHERE strftime('%Y', {date_col}) = ? AND strftime('%m', {date_col}) = ?"
df = pd.read_sql_query(query, conn, params=(year, month))

# Ensure output directory exists
Path(outfile).parent.mkdir(parents=True, exist_ok=True)
df.to_csv(outfile, index=False)
print(f"Exported {len(df)} rows from {table} for {year}-{month} to {outfile}")
conn.close()
