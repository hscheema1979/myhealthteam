#!/usr/bin/env python3

import sqlite3
import sys
import os

def check_billing_data_availability():
    """Check what billing data is available for Oct/Nov 2025"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()

        print('CHECKING BILLING DATA AVAILABILITY')
        print('=' * 60)

        # Check main provider_tasks table
        try:
            cursor.execute('SELECT COUNT(*) FROM provider_tasks WHERE task_date IS NOT NULL')
            main_count = cursor.fetchone()[0]
            print(f'provider_tasks table: {main_count} records')
        except Exception as e:
            print(f'provider_tasks table: ERROR - {e}')

        # Check partitioned tables for Oct/Nov 2025
        partition_counts = {}
        for month in ['09', '10', '11']:
            table_name = f'provider_tasks_2025_{month}'
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE task_date IS NOT NULL')
                partition_count = cursor.fetchone()[0]
                partition_counts[table_name] = partition_count
                print(f'{table_name}: {partition_count} records')
            except Exception as e:
                print(f'{table_name}: ERROR - {e}')
                partition_counts[table_name] = 0

        # Check what months are available in provider_tasks table
        print(f'\nChecking months in provider_tasks:')
        try:
            cursor.execute("""
                SELECT DISTINCT strftime('%Y-%m', task_date) as month
                FROM provider_tasks 
                WHERE task_date IS NOT NULL
                ORDER BY month DESC
                LIMIT 10
            """)
            available_months = cursor.fetchall()
            print(f'Available months in provider_tasks: {[month[0] for month in available_months]}')
        except Exception as e:
            print(f'Error checking provider_tasks months: {e}')

        # Check what months are available in partitioned tables
        print(f'\nChecking months in partitioned tables:')
        for table_name, count in partition_counts.items():
            if count > 0:
                try:
                    cursor.execute(f"""
                        SELECT DISTINCT strftime('%Y-%m', task_date) as month
                        FROM {table_name}
                        WHERE task_date IS NOT NULL
                        ORDER BY month DESC
                    """)
                    months = cursor.fetchall()
                    print(f'{table_name}: months {[month[0] for month in months]}')
                except Exception as e:
                    print(f'Error checking {table_name} months: {e}')

        # Check billing_status table for October/November
        print(f'\nChecking provider_task_billing_status table:')
        try:
            cursor.execute("""
                SELECT strftime('%Y-%m', task_date) as month, COUNT(*) as count
                FROM provider_task_billing_status
                WHERE task_date IS NOT NULL
                GROUP BY strftime('%Y-%m', task_date)
                ORDER BY month DESC
            """)
            billing_months = cursor.fetchall()
            print('Billing status by month:')
            for month, count in billing_months:
                print(f'  {month}: {count} records')
        except Exception as e:
            print(f'Error checking billing status table: {e}')

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_billing_data_availability()