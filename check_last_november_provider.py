#!/usr/bin/env python3

import sqlite3

def check_last_november_provider():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print('LAST PROVIDER UPDATE IN NOVEMBER 2025')
    print('=' * 50)
    
    # Check provider tasks in November 2025
    cursor.execute("""
        SELECT provider_name, task_date, created_date, updated_date, imported_at, 
               minutes_of_service, billing_code, task_description
        FROM provider_tasks_2025_11 
        WHERE task_date IS NOT NULL AND task_date != ''
        ORDER BY task_date DESC, created_date DESC
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    
    print('Most recent provider tasks in November 2025:')
    for i, row in enumerate(results, 1):
        provider_name, task_date, created_date, updated_date, imported_at, minutes, billing_code, description = row
        print(f"{i:2d}. Provider: {provider_name}")
        print(f"    Task Date: {task_date}")
        print(f"    Created: {created_date}")
        print(f"    Updated: {updated_date}")
        print(f"    Imported: {imported_at}")
        print(f"    Minutes: {minutes}, Billing Code: {billing_code}")
        print(f"    Description: {description}")
        print()
    
    # Also check the date range
    cursor.execute('SELECT MIN(task_date), MAX(task_date) FROM provider_tasks_2025_11 WHERE task_date IS NOT NULL AND task_date != ""')
    date_range = cursor.fetchone()
    print(f"Date range in provider_tasks_2025_11: {date_range[0]} to {date_range[1]}")
    
    # Count total provider tasks in November
    cursor.execute("SELECT COUNT(*) FROM provider_tasks_2025_11")
    total_count = cursor.fetchone()[0]
    print(f"Total provider tasks in November 2025: {total_count}")
    
    conn.close()

if __name__ == "__main__":
    check_last_november_provider()