#!/usr/bin/env python3

import sqlite3
import sys
import os
from datetime import datetime, timedelta

def check_provider_billing_data():
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()

        # Check recent provider task data for billing information
        print('PROVIDER TASK BILLING DATA ANALYSIS:')
        print('=' * 60)
        
        # Get data from the latest month (2025_11)
        cursor.execute("""
            SELECT 
                provider_name,
                patient_name,
                task_date,
                minutes_of_service,
                billing_code,
                task_description
            FROM provider_tasks_2025_11
            WHERE provider_name IS NOT NULL AND provider_name != ''
            ORDER BY task_date DESC
            LIMIT 10
        """)
        
        recent_tasks = cursor.fetchall()
        
        print(f'Recent provider tasks (2025_11):')
        for i, task in enumerate(recent_tasks, 1):
            provider, patient, task_date, minutes, billing_code, description = task
            print(f'  {i:2d}. {provider} | {patient} | {task_date} | {minutes}min | {billing_code} | {description}')
        
        # Check billing code distribution
        print('\nBILLING CODE DISTRIBUTION (2025_11):')
        print('=' * 60)
        cursor.execute("""
            SELECT 
                billing_code,
                COUNT(*) as task_count,
                SUM(minutes_of_service) as total_minutes,
                AVG(minutes_of_service) as avg_minutes
            FROM provider_tasks_2025_11
            GROUP BY billing_code
            ORDER BY task_count DESC
        """)
        
        billing_codes = cursor.fetchall()
        for code, count, total_min, avg_min in billing_codes:
            print(f'  {code}: {count} tasks, {total_min} total min, {avg_min:.1f} avg min')
        
        # Check provider distribution
        print('\nPROVIDER DISTRIBUTION (2025_11):')
        print('=' * 60)
        cursor.execute("""
            SELECT 
                provider_name,
                COUNT(*) as task_count,
                SUM(minutes_of_service) as total_minutes
            FROM provider_tasks_2025_11
            GROUP BY provider_name
            ORDER BY task_count DESC
        """)
        
        providers = cursor.fetchall()
        for provider, count, total_min in providers:
            print(f'  {provider}: {count} tasks, {total_min} total minutes')
        
        # Check if we need to populate provider_task_billing_status
        print('\nPROVIDER_TASK_BILLING_STATUS TABLE:')
        print('=' * 60)
        cursor.execute('SELECT COUNT(*) FROM provider_task_billing_status')
        status_count = cursor.fetchone()[0]
        print(f'Current records in provider_task_billing_status: {status_count}')
        
        if status_count == 0:
            print('❗ Table needs to be populated with provider task data')
            print('   Required: Migration script to populate billing status table')
        else:
            print('✅ Table has data')

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_provider_billing_data()