#!/usr/bin/env python3
"""
Split cmlog.csv into monthly partitioned CSV files.
Creates files in downloads/monthly_CM/ named coordinator_tasks_YYYY_MM.csv
"""

import pandas as pd
import os
from pathlib import Path

def split_cmlog_by_month():
    downloads_dir = Path("../downloads")
    cmlog_path = downloads_dir / "cmlog.csv"
    monthly_cm_dir = downloads_dir / "monthly_CM"

    if not cmlog_path.exists():
        print(f"Error: {cmlog_path} not found")
        return

    # Create monthly_CM directory if it doesn't exist
    monthly_cm_dir.mkdir(exist_ok=True)

    print(f"Reading {cmlog_path}...")
    df = pd.read_csv(cmlog_path)

    if 'Year' not in df.columns or 'Month' not in df.columns:
        print("Error: Year and Month columns not found in cmlog.csv")
        return

    # Convert Year and Month to integers, handle NaN
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
    df['Month'] = pd.to_numeric(df['Month'], errors='coerce').astype('Int64')

    # Drop rows with missing Year or Month
    df = df.dropna(subset=['Year', 'Month'])

    # Group by Year and Month
    grouped = df.groupby(['Year', 'Month'])

    for (year, month), group in grouped:
        filename = f"coordinator_tasks_{year}_{month:02d}.csv"
        filepath = monthly_cm_dir / filename

        print(f"Writing {len(group)} rows to {filepath}")
        group.to_csv(filepath, index=False)

    print(f"Split complete. Created {len(grouped)} monthly files in {monthly_cm_dir}")

if __name__ == "__main__":
    split_cmlog_by_month()