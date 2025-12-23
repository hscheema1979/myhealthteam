#!/usr/bin/env python3
"""
Split psl.csv into monthly partitioned CSV files.
Creates files in downloads/monthly_PSL/ named provider_tasks_YYYY_MM.csv
"""

import pandas as pd
import os
from pathlib import Path

def split_psl_by_month():
    downloads_dir = Path("../downloads")
    psl_path = downloads_dir / "psl.csv"
    monthly_psl_dir = downloads_dir / "monthly_PSL"

    if not psl_path.exists():
        print(f"Error: {psl_path} not found")
        return

    # Create monthly_PSL directory if it doesn't exist
    monthly_psl_dir.mkdir(exist_ok=True)

    print(f"Reading {psl_path}...")
    df = pd.read_csv(psl_path)

    if 'Year' not in df.columns or 'Month' not in df.columns:
        print("Error: Year and Month columns not found in psl.csv")
        return

    # Convert Year and Month to integers, handle NaN
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce').astype('Int64')
    df['Month'] = pd.to_numeric(df['Month'], errors='coerce').astype('Int64')

    # Drop rows with missing Year or Month
    df = df.dropna(subset=['Year', 'Month'])

    # Group by Year and Month
    grouped = df.groupby(['Year', 'Month'])

    for (year, month), group in grouped:
        filename = f"provider_tasks_{year}_{month:02d}.csv"
        filepath = monthly_psl_dir / filename

        print(f"Writing {len(group)} rows to {filepath}")
        group.to_csv(filepath, index=False)

    print(f"Split complete. Created {len(grouped)} monthly files in {monthly_psl_dir}")

if __name__ == "__main__":
    split_psl_by_month()