#!/usr/bin/env python3

import sqlite3
import sys
import os

def investigate_billing_status():
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()

        # Check for billing-related tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%billing%'")
        billing_tables = cursor.fetchall()
        print('BILLING-RELATED TABLES:')
        print('=' * 50)
        for table in billing_tables:
            print(f'  - {table[0]}')

        # Check provider_task_billing_status table structure
        print('\nPROVIDER_TASK_BILLING_STATUS TABLE STRUCTURE:')
        print('=' * 50)
        cursor.execute('PRAGMA table_info("provider_task_billing_status")')
        columns = cursor.fetchall()
        for col in columns:
            print(f'  {col[1]} ({col[2]})')

        # Check if the table exists and has data
        cursor.execute('SELECT COUNT(*) FROM provider_task_billing_status')
        count = cursor.fetchone()[0]
        print(f'\nTable has {count} records')

        # Check sample data
        cursor.execute('SELECT * FROM provider_task_billing_status LIMIT 3')
        sample = cursor.fetchall()
        if sample:
            print('\nSample data:')
            for i, row in enumerate(sample):
                print(f'  Row {i+1}: {row}')
        else:
            print('\nNo data in provider_task_billing_status table')

        # Check provider_tasks tables for billing data
        print('\nPROVIDER TASKS WITH BILLING DATA:')
        print('=' * 50)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%' ORDER BY name DESC")
        provider_tables = cursor.fetchall()[:5]  # Get recent 5 tables
        for table in provider_tables:
            table_name = table[0]
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE billing_code IS NOT NULL')
                billing_count = cursor.fetchone()[0]
                cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                total_count = cursor.fetchone()[0]
                print(f'  {table_name}: {billing_count}/{total_count} tasks with billing codes')
            except Exception as e:
                print(f'  {table_name}: Error - {e}')

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    investigate_billing_status()