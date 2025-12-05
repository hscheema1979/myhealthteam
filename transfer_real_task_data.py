#!/usr/bin/env python3
"""
DIRECT TASK DATA TRANSFER - September, October, November 2025
Transfers real task data from sheets_data.db to production.db
"""

import sqlite3
import shutil
from datetime import datetime

def backup_production_db():
    """Create backup of production.db before transfer"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f'production_backup_{timestamp}.db'
    shutil.copy2('production.db', backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def transfer_coordinator_tasks():
    """Transfer coordinator tasks for September, October, November 2025"""
    print("\n📋 TRANSFERRING COORDINATOR TASKS")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    months_data = [
        ('2025_09', '2025-09-01', '2025-09-30'),
        ('2025_10', '2025-10-01', '2025-10-31'),
        ('2025_11', '2025-11-01', '2025-11-30')
    ]
    
    total_transferred = 0
    
    for month_suffix, start_date, end_date in months_data:
        table_name = f'coordinator_tasks_{month_suffix}'
        print(f"\n📅 Processing {table_name}...")
        
        try:
            # Check if staging table exists
            staging_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not staging_cursor.fetchone():
                print(f"   ⚠️  {table_name} not found in sheets_data.db")
                continue
            
            # Clear existing placeholder data in production
            production_cursor.execute(f"DELETE FROM {table_name}")
            
            # Get data from staging
            staging_cursor.execute(f"SELECT * FROM {table_name}")
            rows = staging_cursor.fetchall()
            
            # Get column names
            staging_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in staging_cursor.fetchall()]
            
            print(f"   Found {len(rows)} records in staging")
            
            # Insert into production (adjusting for different schema)
            if len(rows) > 0:
                # For coordinator_tasks tables, we'll insert the raw data
                # Adjust columns as needed based on schema differences
                for row in rows:
                    try:
                        if len(columns) >= 6:  # Expected minimal columns
                            production_cursor.execute(f"""
                                INSERT INTO {table_name} (
                                    coordinator_id, patient_id, task_date, duration_minutes, 
                                    task_type, notes, source_system, imported_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                row[0] if len(row) > 0 else None,  # coordinator_id
                                row[1] if len(row) > 1 else None,  # patient_id
                                row[2] if len(row) > 2 else None,  # task_date
                                row[3] if len(row) > 3 else 0,     # duration_minutes
                                row[4] if len(row) > 4 else None,  # task_type
                                row[5] if len(row) > 5 else None,  # notes
                                'monthly_CM',                      # source_system
                                datetime.now().isoformat()         # imported_at
                            ))
                            total_transferred += 1
                    except Exception as e:
                        print(f"   ❌ Error inserting row: {e}")
                        continue
                
                print(f"   ✅ Transferred {total_transferred} coordinator tasks for {month_suffix}")
            
        except Exception as e:
            print(f"   ❌ Error processing {table_name}: {e}")
    
    staging_conn.close()
    production_conn.commit()
    production_conn.close()
    
    return total_transferred

def transfer_provider_tasks():
    """Transfer provider tasks for September, October, November 2025"""
    print("\n👩‍⚕️ TRANSFERRING PROVIDER TASKS")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    months_data = [
        ('2025_09', '2025-09-01', '2025-09-30'),
        ('2025_10', '2025-10-01', '2025-10-31'),
        ('2025_11', '2025-11-01', '2025-11-30')
    ]
    
    total_transferred = 0
    
    for month_suffix, start_date, end_date in months_data:
        table_name = f'provider_tasks_{month_suffix}'
        print(f"\n📅 Processing {table_name}...")
        
        try:
            # Check if staging table exists
            staging_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not staging_cursor.fetchone():
                print(f"   ⚠️  {table_name} not found in sheets_data.db")
                continue
            
            # Clear existing placeholder data in production
            production_cursor.execute(f"DELETE FROM {table_name}")
            
            # Get data from staging
            staging_cursor.execute(f"SELECT * FROM {table_name}")
            rows = staging_cursor.fetchall()
            
            print(f"   Found {len(rows)} records in staging")
            
            # Insert into production
            if len(rows) > 0:
                for row in rows:
                    try:
                        # Adjust based on actual provider_tasks schema
                        production_cursor.execute(f"""
                            INSERT INTO {table_name} (
                                provider_task_id, task_id, provider_id, provider_name,
                                patient_name, user_id, patient_id, status, notes,
                                minutes_of_service, billing_code_id, created_date,
                                updated_date, task_date, month, year, billing_code,
                                billing_code_description, task_description, source_system, imported_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            None,   # provider_task_id (auto-increment)
                            row[1] if len(row) > 1 else None,  # task_id
                            row[2] if len(row) > 2 else None,  # provider_id
                            row[3] if len(row) > 3 else None,  # provider_name
                            row[4] if len(row) > 4 else None,  # patient_name
                            row[5] if len(row) > 5 else None,  # user_id
                            row[6] if len(row) > 6 else None,  # patient_id
                            row[7] if len(row) > 7 else 'N',   # status
                            row[8] if len(row) > 8 else None,  # notes
                            row[9] if len(row) > 9 else 0,     # minutes_of_service
                            row[10] if len(row) > 10 else None, # billing_code_id
                            row[11] if len(row) > 11 else None, # created_date
                            row[12] if len(row) > 12 else None, # updated_date
                            row[13] if len(row) > 13 else None, # task_date
                            row[14] if len(row) > 14 else int(month_suffix.split('_')[1]), # month
                            row[15] if len(row) > 15 else int(month_suffix.split('_')[0]), # year
                            row[16] if len(row) > 16 else None, # billing_code
                            row[17] if len(row) > 17 else None, # billing_code_description
                            row[18] if len(row) > 18 else None, # task_description
                            'monthly_PSL',                     # source_system
                            datetime.now().isoformat()         # imported_at
                        ))
                        total_transferred += 1
                    except Exception as e:
                        print(f"   ❌ Error inserting row: {e}")
                        continue
                
                print(f"   ✅ Transferred {total_transferred} provider tasks for {month_suffix}")
            
        except Exception as e:
            print(f"   ❌ Error processing {table_name}: {e}")
    
    staging_conn.close()
    production_conn.commit()
    production_conn.close()
    
    return total_transferred

def verify_transfer():
    """Verify that data was transferred correctly"""
    print("\n🔍 VERIFYING TRANSFER")
    print("=" * 50)
    
    production_conn = sqlite3.connect('production.db')
    cursor = production_conn.cursor()
    
    tables_to_check = [
        'coordinator_tasks_2025_09',
        'coordinator_tasks_2025_10', 
        'coordinator_tasks_2025_11',
        'provider_tasks_2025_09',
        'provider_tasks_2025_10',
        'provider_tasks_2025_11'
    ]
    
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} records")
        except Exception as e:
            print(f"   {table}: Error - {e}")
    
    production_conn.close()

def main():
    """Main transfer function"""
    print("🚀 TASK DATA TRANSFER - September, October, November 2025")
    print("=" * 60)
    print(f"Source: sheets_data.db")
    print(f"Target: production.db")
    print(f"Time: {datetime.now()}")
    
    # Create backup
    backup_path = backup_production_db()
    
    # Transfer coordinator tasks
    coordinator_count = transfer_coordinator_tasks()
    
    # Transfer provider tasks  
    provider_count = transfer_provider_tasks()
    
    # Verify transfer
    verify_transfer()
    
    print(f"\n✅ TRANSFER COMPLETE")
    print(f"   Coordinator tasks transferred: {coordinator_count}")
    print(f"   Provider tasks transferred: {provider_count}")
    print(f"   Total tasks transferred: {coordinator_count + provider_count}")
    print(f"   Backup saved as: {backup_path}")
    
    return coordinator_count + provider_count

if __name__ == "__main__":
    main()