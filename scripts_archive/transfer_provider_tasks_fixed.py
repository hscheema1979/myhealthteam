#!/usr/bin/env python3
"""
FIXED PROVIDER TASK TRANSFER
Uses correct production schema for provider_tasks table
"""

import sqlite3
from datetime import datetime

def transfer_provider_tasks():
    """Transfer provider tasks with correct schema mapping"""
    print("👨‍⚕️ PROVIDER TASK TRANSFER")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get provider tasks from staging
    staging_cursor.execute("""
        SELECT provider_name, patient_name, task_type, minutes_of_service, 
               activity_date, billing_code, task_description, notes
        FROM staging_provider_tasks 
        WHERE activity_date BETWEEN '2025-10-01' AND '2025-10-31'
    """)
    
    provider_tasks = staging_cursor.fetchall()
    print(f"   Found {len(provider_tasks)} provider tasks")
    
    provider_transferred = 0
    for task in provider_tasks:
        try:
            # Insert using production schema
            production_cursor.execute("""
                INSERT INTO provider_tasks (
                    provider_name, patient_name, task_type, minutes_of_service,
                    task_date, billing_code, task_description, notes,
                    created_date, updated_date, source_system
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task[0],  # provider_name
                task[1],  # patient_name  
                task[2],  # task_type
                task[3] if task[3] and task[3] != '' else 0,  # minutes_of_service
                task[4],  # task_date (activity_date)
                task[5],  # billing_code
                task[6],  # task_description
                task[7],  # notes
                datetime.now().isoformat(),  # created_date
                datetime.now().isoformat(),  # updated_date
                'october_2025_transfer'  # source_system
            ))
            provider_transferred += 1
            
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Skipping provider task: {e}")
        except Exception as e:
            print(f"   ❌ Error transferring task: {e}")
    
    production_conn.commit()
    print(f"✅ Transferred {provider_transferred} provider tasks")
    
    staging_conn.close()
    production_conn.close()
    
    return provider_transferred

def verify_provider_task_transfer():
    """Verify provider task transfer"""
    print(f"\n🔍 PROVIDER TASK VERIFICATION")
    print("=" * 50)
    
    production_conn = sqlite3.connect('../production.db')
    cursor = production_conn.cursor()
    
    # Check October 2025 provider tasks
    cursor.execute("SELECT COUNT(*) FROM provider_tasks WHERE task_date LIKE '2025-10%'")
    oct_provider = cursor.fetchone()[0]
    
    print(f"📊 October 2025 provider tasks: {oct_provider:,}")
    
    # Expected: 0 existing + 105 new = 105 total
    expected = 105
    if oct_provider == expected:
        print(f"✅ Provider task transfer successful: {oct_provider:,} (expected {expected:,})")
        success = True
    else:
        print(f"⚠️  Provider task count mismatch: {oct_provider:,} (expected {expected:,})")
        success = False
    
    production_conn.close()
    return success

def main():
    """Main provider task transfer"""
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        provider_count = transfer_provider_tasks()
        success = verify_provider_task_transfer()
        
        print(f"\n🎉 PROVIDER TASK TRANSFER COMPLETE!")
        print(f"📊 Total transferred: {provider_count:,} provider tasks")
        
        if success:
            print(f"✅ All provider tasks transferred successfully")
        else:
            print(f"⚠️  Some discrepancies in provider task counts")
            
        return success
        
    except Exception as e:
        print(f"❌ Provider task transfer failed: {e}")
        return False

if __name__ == "__main__":
    success = main()