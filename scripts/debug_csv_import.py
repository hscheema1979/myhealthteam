#!/usr/bin/env python3
"""
Debug script to test CSV import process and identify data loss issues.
"""

import pandas as pd
import sqlite3
import os
import sys

def debug_csv_import(csv_file, db_file, table_name):
    """Debug the CSV import process step by step."""
    
    print(f"=== DEBUG CSV IMPORT ===")
    print(f"CSV File: {csv_file}")
    print(f"Database: {db_file}")
    print(f"Table: {table_name}")
    print()
    
    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"ERROR: CSV file does not exist: {csv_file}")
        return
    
    # Read CSV and analyze
    print("1. Reading CSV file...")
    try:
        df = pd.read_csv(csv_file)
        print(f"   - Successfully read CSV")
        print(f"   - Shape: {df.shape}")
        print(f"   - Columns: {list(df.columns)}")
        print(f"   - Data types:")
        for col, dtype in df.dtypes.items():
            print(f"     {col}: {dtype}")
        print()
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return
    
    # Check for empty columns
    print("2. Checking for empty columns...")
    empty_cols = df.columns[df.isnull().all()].tolist()
    unnamed_cols = [col for col in df.columns if 'Unnamed:' in str(col)]
    print(f"   - Empty columns: {empty_cols}")
    print(f"   - Unnamed columns: {unnamed_cols}")
    print()
    
    # Apply skip_empty_columns logic
    print("3. Applying skip_empty_columns logic...")
    df_cleaned = df.copy()
    # Drop columns where all values are NaN
    df_cleaned.dropna(axis=1, how='all', inplace=True)
    # Drop columns with names like "Unnamed: 0"
    df_cleaned.drop(df_cleaned.columns[df_cleaned.columns.str.contains('Unnamed:', case=False)], axis=1, inplace=True, errors='ignore')
    print(f"   - Shape after cleaning: {df_cleaned.shape}")
    print(f"   - Columns after cleaning: {list(df_cleaned.columns)}")
    print()
    
    # Check for problematic data
    print("4. Checking for problematic data...")
    for col in df_cleaned.columns:
        null_count = df_cleaned[col].isnull().sum()
        if null_count > 0:
            print(f"   - Column '{col}': {null_count} null values")
    print()
    
    # Test database connection and import
    print("5. Testing database import...")
    try:
        conn = sqlite3.connect(db_file)
        
        # Drop table if exists
        conn.execute(f"DROP TABLE IF EXISTS [{table_name}];")
        print(f"   - Dropped table '{table_name}' if it existed")
        
        # Import data
        df_cleaned.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"   - Successfully imported data to table '{table_name}'")
        
        # Check row count
        cursor = conn.execute(f"SELECT COUNT(*) FROM [{table_name}];")
        row_count = cursor.fetchone()[0]
        print(f"   - Rows in database: {row_count}")
        print(f"   - Original CSV rows: {len(df)}")
        print(f"   - Cleaned CSV rows: {len(df_cleaned)}")
        
        if row_count != len(df_cleaned):
            print(f"   - WARNING: Row count mismatch!")
        
        # Sample some data
        print("\n6. Sample data from database:")
        cursor = conn.execute(f"SELECT * FROM [{table_name}] LIMIT 5;")
        sample_rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        print(f"   - Columns in DB: {columns}")
        for i, row in enumerate(sample_rows):
            print(f"   - Row {i+1}: {row}")
        
        conn.close()
        
    except Exception as e:
        print(f"ERROR during database import: {e}")
        return
    
    print("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python debug_csv_import.py <csv_file> <db_file> <table_name>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    db_file = sys.argv[2]
    table_name = sys.argv[3]
    
    debug_csv_import(csv_file, db_file, table_name)