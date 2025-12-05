#!/usr/bin/env python3

import sqlite3
import sys
import os

def check_provider_task_structure():
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()

        # Check provider task tables for 2025
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%'")
        tables = cursor.fetchall()
        print('PROVIDER TASK TABLES:')
        print('=' * 50)
        for table in tables:
            print(f'  - {table[0]}')

        # Get sample data from the latest month to understand structure
        cursor.execute("SELECT * FROM provider_tasks_2025_11 LIMIT 3")
        sample = cursor.fetchall()
        print('\nSAMPLE PROVIDER TASK DATA (2025_11):')
        print('=' * 50)
        for i, row in enumerate(sample):
            print(f'Row {i+1}: {row}')

        # Check available columns
        cursor.execute("PRAGMA table_info('provider_tasks_2025_11')")
        columns = cursor.fetchall()
        print('\nCOLUMNS IN provider_tasks_2025_11:')
        print('=' * 50)
        for col in columns:
            print(f'  {col[1]} ({col[2]})')

        # Check data for monthly summary potential
        print('\nMONTHLY SUMMARY DATA ANALYSIS:')
        print('=' * 50)
        
        # Count tasks by month for 2025
        cursor.execute("""
            SELECT strftime('%Y-%m', task_date) as month, COUNT(*) as task_count
            FROM provider_tasks_2025_11 
            WHERE task_date IS NOT NULL AND task_date != ''
            GROUP BY strftime('%Y-%m', task_date)
            ORDER BY month
        """)
        monthly_counts = cursor.fetchall()
        print("Tasks by month in 2025_11:")
        for month, count in monthly_counts:
            print(f"  {month}: {count} tasks")

        # Check provider distribution
        cursor.execute("""
            SELECT provider_name, COUNT(*) as task_count
            FROM provider_tasks_2025_11 
            WHERE provider_name IS NOT NULL AND provider_name != ''
            GROUP BY provider_name
            ORDER BY task_count DESC
            LIMIT 10
        """)
        provider_counts = cursor.fetchall()
        print("\nTop 10 providers by task count:")
        for provider, count in provider_counts:
            print(f"  {provider}: {count} tasks")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_provider_task_structure()