#!/usr/bin/env python3
"""
CORRECTED PROVIDER TASK TRANSFER
Properly maps staging schema to production schema
"""

import sqlite3
from datetime import datetime

def transfer_provider_tasks_correct():
    """Transfer provider tasks with correct schema mapping"""
    print("👨‍⚕️ CORRECTED PROVIDER TASK TRANSFER")
    print("=" * 50)
    
    staging_conn = sqlite3.connect('sheets_data.db')
    production_conn = sqlite3.connect('../production.db')
    
    staging_cursor = staging_conn.cursor()
    production_cursor = production_conn.cursor()
    
    # Get provider tasks from staging using correct column names
    staging_cursor.execute("""
        SELECT provider_code, patient_name_raw, patient_id, service, 
               billing_code, minutes_raw, activity_date
        FROM staging_provider_tasks 
        WHERE activity_date BETWEEN '2025-10-01' AND '2025-10-31'
    """)
    
    provider_tasks = staging_cursor.fetchall()
    print(f"   Found {len(provider_tasks)} provider tasks")
    
    provider_transferred = 0
    for task in provider_tasks:
        try:
            # Map staging columns to production schema correctly
            production_cursor.execute("""
                INSERT INTO provider_tasks (
                    provider_name, patient_name, patient_id, task_description,
                    minutes_of_service, task_date, billing_code, source_system
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task[0],  # provider_code -> provider_name
                task[1],  # patient_name_raw -> patient_name
                task[2],  # patient_id (direct map)
                task[3],  # service -> task_description
                int(task[5]) if task[5] and task[5].isdigit() else 0,  # minutes_raw -> minutes_of_service
                task[6],  # activity_date -> task_date
                task[4],  # billing_code (direct map)
                'staging_october_2025'  # source_system
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

def final_verification():
    """Final verification of all October 2025 data"""
    print(f"\n🔍 FINAL TRANSFER VERIFICATION")
    print("=" * 60)
    
    production_conn = sqlite3.connect('../production.db')
    cursor = production_conn.cursor()
    
    # Check all October 2025 data
    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM coordinator_tasks WHERE task_date LIKE '2025-10%'")
    oct_coordinator = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM provider_tasks WHERE task_date LIKE '2025-10%'")
    oct_provider = cursor.fetchone()[0]
    
    print(f"📊 FINAL PRODUCTION DATABASE STATE:")
    print(f"   • Total patients: {total_patients:,}")
    print(f"   • October 2025 coordinator tasks: {oct_coordinator:,}")
    print(f"   • October 2025 provider tasks: {oct_provider:,}")
    print()
    
    # Expected totals after transfer
    expected_patients = 613  # 512 + 101
    expected_coordinator = 70 + 7817  # existing + new
    expected_provider = 105  # new only
    
    print(f"✅ EXPECTED vs ACTUAL:")
    print(f"   • Patients: {expected_patients:,} vs {total_patients:,} {'✅' if total_patients == expected_patients else '❌'}")
    print(f"   • Coordinator tasks: {expected_coordinator:,} vs {oct_coordinator:,} {'✅' if oct_coordinator == expected_coordinator else '❌'}")
    print(f"   • Provider tasks: {expected_provider:,} vs {oct_provider:,} {'✅' if oct_provider == expected_provider else '❌'}")
    
    production_conn.close()
    
    # Overall success
    all_success = (total_patients == expected_patients and 
                   oct_coordinator == expected_coordinator and 
                   oct_provider == expected_provider)
    
    return all_success

def main():
    """Main corrected provider task transfer"""
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        provider_count = transfer_provider_tasks_correct()
        success = final_verification()
        
        print(f"\n🎉 OCTOBER 2025 DATA TRANSFER COMPLETE!")
        print(f"📊 Final Summary:")
        print(f"   • New patients: 101")
        print(f"   • Coordinator tasks: 7,817")
        print(f"   • Provider tasks: {provider_count}")
        print(f"   • Total records added: {101 + 7817 + provider_count:,}")
        
        if success:
            print(f"✅ ALL TRANSFERS SUCCESSFUL!")
            print(f"🚀 READY FOR BILLING VIEW VERIFICATION")
        else:
            print(f"⚠️  Some transfer discrepancies detected")
            
        return success
        
    except Exception as e:
        print(f"❌ Transfer failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print(f"\n🎯 PROCEEDING TO BILLING VIEW VERIFICATION")
    else:
        print(f"\n⚠️  Address transfer issues before billing verification")