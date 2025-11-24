import os
import sys
import pandas as pd
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DOWNLOADS = os.path.join(ROOT, 'downloads')
INPUT = os.path.join(DOWNLOADS, 'cmlog.csv')
OUT_DIR = os.path.join(DOWNLOADS, 'monthly_CM')

DATE_PREFS = [
    'Task Date', 'task_date', 'Date', 'date', 'DATE',
    'Created Date', 'created_date', 'Updated Date', 'updated_date'
]

def pick_date_column(cols):
    # strict preference list first
    for c in DATE_PREFS:
        if c in cols:
            return c
    # otherwise any column that contains 'date'
    for c in cols:
        if 'date' in c.lower():
            return c
    return None

def main():
    if not os.path.exists(INPUT):
        print(f"WARNING: input file not found: {INPUT}")
        sys.exit(0)
    os.makedirs(OUT_DIR, exist_ok=True)

    # Read as strings, then parse date
    df = pd.read_csv(INPUT, dtype=str)
    cols = list(df.columns)
    date_col = pick_date_column(cols)
    if not date_col:
        print("ERROR: Could not locate a date column in cmlog.csv; available columns:")
        print(cols)
        sys.exit(1)

    # Normalize and parse date
    dt = pd.to_datetime(df[date_col], errors='coerce', infer_datetime_format=True)
    df['_ym'] = dt.dt.strftime('%Y_%m')
    df = df[~df['_ym'].isna()]

    if df.empty:
        print("WARNING: No valid dated rows after parsing; skipping split.")
        sys.exit(0)

    # Write out per month
    months = sorted(df['_ym'].unique())
    count = 0
    for ym in months:
        part = df[df['_ym'] == ym].drop(columns=['_ym'])
        out_path = os.path.join(OUT_DIR, f'coordinator_tasks_{ym}.csv')
        part.to_csv(out_path, index=False)
        count += 1
        print(f"Wrote {len(part)} rows to {out_path}")

    print(f"Completed CM monthly split: {count} files -> {OUT_DIR}")

if __name__ == '__main__':
    main()