#!/usr/bin/env python3
"""
OCTOBER 2025 TASK TRANSFER
Transfers October 2025 coordinator and provider tasks to production
"""

import sqlite3
from datetime import datetime

def transfer_october_tasks():
    """Transfer October 2025 tasks to production"""
    print("🚀 OCTOBER 2025 TASK TRANSFER")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Transfer coordinator tasks
    print("📋 Transferring October 2025 coordinator tasks...")
    
    staging_cursor.execute("""
        SELECT staff_code, patient_name_raw, task_type, notes, minutes_raw, 
               activity_date
        FROM staging_coordinator_tasks 
        WHERE activity_date BETWEEN '2025-10-01' AND '2025-10-31'
    """)
    
    coordinator_tasks = staging_cursor.fetchall()
    print(f"   Found {len(coordinator_tasks)} coordinator tasks")
    
    coordinator_transferred = 0
    for task in coordinator_tasks:
        try:
            production_cursor.execute("""
                INSERT INTO coordinator_tasks (
                    patient_id, coordinator_id, task_date, duration_minutes,
                    task_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task[1],  # patient_id
                task[0],  # coordinator_id
                task[5],  # task_date
                task[4] if task[4] and task[4] != '' else 0,  # duration
                task[2],  # task_type
                task[3]   # notes
            ))
            coordinator_transferred += 1
        except sqlite3.IntegrityError as e:
            print(f"   ⚠️  Skipping coordinator task: {e}")
    
    production_conn.commit()
    print(f"✅ Transferred {coordinator_transferred} coordinator tasks")
    
    # Transfer provider tasks
    print(f"\n👨‍⚕️ Transferring October 2025 provider tasks...")
    
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
                task[3] if task[3] and task[3] != '' else 0,  # minutes
                task[4],  # task_date
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
    
    production_conn.commit()
    print(f"✅ Transferred {provider_transferred} provider tasks")
    
    staging_conn.close()
    production_conn.close()
    
    return coordinator_transferred, provider_transferred

def verify_task_transfer():
    """Verify task transfer was successful"""
    print(f"\n🔍 VERIFYING TASK TRANSFER")
    print("=" * 50)
    
    production_conn = sqlite3.connect('../production.db')
    cursor = production_conn.cursor()
    
    # Check coordinator tasks
    cursor.execute("SELECT COUNT(*) FROM coordinator_tasks WHERE task_date LIKE '2025-10%'")
    oct_coordinator = cursor.fetchone()[0]
    
    # Check provider tasks
    cursor.execute("SELECT COUNT(*) FROM provider_tasks WHERE task_date LIKE '2025-10%'")
    oct_provider = cursor.fetchone()[0]
    
    print(f"📊 October 2025 tasks in production:")
    print(f"   • Coordinator tasks: {oct_coordinator:,}")
    print(f"   • Provider tasks: {oct_provider:,}")
    
    # Expected totals
    expected_coordinator = 70 + 7817  # existing + new
    expected_provider = 0 + 105  # existing + new
    
    print(f"\n✅ Verification:")
    coordinator_ok = oct_coordinator == expected_coordinator
    provider_ok = oct_provider == expected_provider
    
    print(f"   • Coordinator: {oct_coordinator:,} (expected {expected_coordinator:,}) {'✅' if coordinator_ok else '❌'}")
    print(f"   • Provider: {oct_provider:,} (expected {expected_provider:,}) {'✅' if provider_ok else '❌'}")
    
    production_conn.close()
    
    return coordinator_ok and provider_ok

def main():
    """Main task transfer function"""
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        coordinator_count, provider_count = transfer_october_tasks()
        success = verify_task_transfer()
        
        print(f"\n🎉 TASK TRANSFER COMPLETE!")
        print(f"📊 Total transferred:")
        print(f"   • Coordinator tasks: {coordinator_count:,}")
        print(f"   • Provider tasks: {provider_count:,}")
        
        if success:
            print(f"✅ All tasks transferred successfully")
            print(f"🚀 Ready for billing view verification")
        else:
            print(f"⚠️  Some discrepancies in task counts")
            
        return success
        
    except Exception as e:
        print(f"❌ Task transfer failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🚀 PROCEEDING TO BILLING VIEW VERIFICATION")
    else:
        print(f"\n⚠️  Manual review needed before billing verification")