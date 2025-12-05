#!/usr/bin/env python3

import sqlite3
import sys
import os
from datetime import datetime, timedelta

def populate_billing_status_table():
    """Populate provider_task_billing_status table from provider_tasks data"""
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        print("POPULATING PROVIDER_TASK_BILLING_STATUS TABLE")
        print("=" * 60)
        
        # Get all provider task tables
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name LIKE 'provider_tasks_%' 
            AND name NOT LIKE '%backup%' 
            AND name NOT LIKE '%summary%' 
            AND name NOT LIKE '%restored%'
            ORDER BY name DESC
        """)
        tables = cursor.fetchall()
        
        total_inserted = 0
        
        for table in tables:
            table_name = table[0]
            print(f"Processing {table_name}...")
            
            # Get data from the provider_tasks table
            query = f"""
                SELECT 
                    provider_task_id,
                    provider_id,
                    provider_name,
                    patient_id,
                    patient_name,
                    task_date,
                    minutes_of_service,
                    billing_code,
                    billing_code_description,
                    task_description
                FROM {table_name}
                WHERE provider_name IS NOT NULL AND provider_name != ''
            """
            
            cursor.execute(query)
            provider_tasks = cursor.fetchall()
            
            if not provider_tasks:
                print(f"  No tasks found in {table_name}")
                continue
            
            # Insert into provider_task_billing_status table
            inserted_count = 0
            for task in provider_tasks:
                try:
                    (provider_task_id, provider_id, provider_name, patient_id, 
                     patient_name, task_date, minutes, billing_code, 
                     billing_code_description, task_description) = task
                    
                    # Calculate billing week
                    billing_week = datetime.strptime(task_date, '%Y-%m-%d').strftime('%Y-%W')
                    week_start_date = (datetime.strptime(task_date, '%Y-%m-%d') - timedelta(days=datetime.strptime(task_date, '%Y-%m-%d').weekday())).strftime('%Y-%m-%d')
                    week_end_date = (datetime.strptime(week_start_date, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
                    
                    # Insert record (only if it doesn't exist)
                    cursor.execute("""
                        INSERT OR IGNORE INTO provider_task_billing_status (
                            provider_task_id, provider_id, provider_name, patient_id, 
                            patient_name, task_date, billing_week, week_start_date, 
                            week_end_date, task_description, minutes_of_service, 
                            billing_code, billing_code_description, billing_status,
                            is_billed, is_paid, created_date, updated_date
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        provider_task_id, provider_id, provider_name, patient_id,
                        patient_name, task_date, billing_week, week_start_date,
                        week_end_date, task_description, minutes, billing_code,
                        billing_code_description, 'Pending', 0, 0,
                        datetime.now().isoformat(), datetime.now().isoformat()
                    ))
                    
                    if cursor.rowcount > 0:
                        inserted_count += 1
                        
                except Exception as e:
                    print(f"  Error inserting task {provider_task_id}: {e}")
                    continue
            
            print(f"  Inserted {inserted_count} records from {table_name}")
            total_inserted += inserted_count
        
        conn.commit()
        
        print(f"\n✅ COMPLETED: {total_inserted} total records inserted")
        
        # Verify the results
        cursor.execute('SELECT COUNT(*) FROM provider_task_billing_status')
        final_count = cursor.fetchone()[0]
        print(f"Final count in provider_task_billing_status: {final_count} records")
        
        # Show sample data
        if final_count > 0:
            cursor.execute("""
                SELECT provider_name, billing_status, COUNT(*) as task_count, 
                       SUM(minutes_of_service) as total_minutes
                FROM provider_task_billing_status 
                GROUP BY provider_name, billing_status
                ORDER BY task_count DESC
                LIMIT 5
            """)
            
            sample_data = cursor.fetchall()
            print("\nSample billing status summary:")
            for provider, status, count, minutes in sample_data:
                print(f"  {provider} | {status}: {count} tasks, {minutes} minutes")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    populate_billing_status_table()