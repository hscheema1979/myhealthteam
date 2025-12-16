#!/usr/bin/env python3
"""
Test script to verify the onboarding TV scheduling progress fix
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database import save_onboarding_tv_scheduling_progress
import sqlite3
from datetime import datetime, date, time

def test_onboarding_fix():
    print("Testing onboarding TV scheduling progress fix...")
    
    # Test data for onboarding_id 6 (test4 test4)
    onboarding_id = 6
    
    # First, let's check what users exist in the database
    conn = sqlite3.connect('production.db')
    conn.row_factory = sqlite3.Row
    
    users = conn.execute("SELECT user_id, username, first_name, last_name FROM users LIMIT 5").fetchall()
    print("Available users:")
    for user in users:
        print(f"  ID: {user['user_id']}, Username: {user['username']}, Name: {user['first_name']} {user['last_name']}")
    
    conn.close()
    
    # Sample TV scheduling data using the correct format expected by the function
    tv_scheduling_data = {
        'tv_scheduled': True,
        'tv_date': date(2024, 1, 15),
        'tv_time': time(10, 30),
        'assigned_provider': f"{users[0]['first_name']} {users[0]['last_name']} ({users[0]['username']})" if users else None,
        'assigned_coordinator': f"{users[1]['first_name']} {users[1]['last_name']} ({users[1]['username']})" if len(users) > 1 else None,
        'patient_notified': True,
        'initial_tv_completed': True
    }
    
    print(f"\nSaving TV scheduling progress for onboarding_id: {onboarding_id}")
    print(f"Data: {tv_scheduling_data}")
    
    # Check before state
    print("\n--- Before State ---")
    conn = sqlite3.connect('production.db')
    conn.row_factory = sqlite3.Row
    
    before_patient = conn.execute("""
        SELECT onboarding_id, first_name, last_name, date_of_birth, patient_id 
        FROM onboarding_patients 
        WHERE onboarding_id = ?
    """, (onboarding_id,)).fetchone()
    
    print(f"Before - patient_id: {before_patient['patient_id'] if before_patient else 'No record'}")
    conn.close()
    
    try:
        # Call the updated function
        save_onboarding_tv_scheduling_progress(onboarding_id, tv_scheduling_data)
        print("✅ Successfully saved TV scheduling progress")
        
        # Verify the results
        print("\n--- After State ---")
        
        # Check onboarding_patients table
        conn = sqlite3.connect('production.db')
        conn.row_factory = sqlite3.Row
        
        patient_info = conn.execute("""
            SELECT onboarding_id, first_name, last_name, date_of_birth, patient_id 
            FROM onboarding_patients 
            WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        if patient_info:
            print(f"1. Onboarding Patients - patient_id: '{patient_info['patient_id']}'")
            
            # Check if patient_id was actually set
            if patient_info['patient_id']:
                # Check patients table
                patient_record = conn.execute("""
                    SELECT patient_id, first_name, last_name, date_of_birth 
                    FROM patients 
                    WHERE patient_id = ?
                """, (patient_info['patient_id'],)).fetchone()
                
                if patient_record:
                    print(f"2. Patients Table - Found record: {patient_record['patient_id']}")
                else:
                    print("2. Patients Table - ❌ No record found")
                
                # Check patient_assignments table
                assignments = conn.execute("""
                    SELECT patient_id, provider_id, coordinator_id, status 
                    FROM patient_assignments 
                    WHERE patient_id = ?
                """, (patient_info['patient_id'],)).fetchall()
                
                print(f"3. Patient Assignments - Found {len(assignments)} assignments")
                for assignment in assignments:
                    print(f"   - Provider: {assignment['provider_id']}, Coordinator: {assignment['coordinator_id']}, Status: {assignment['status']}")
                
                # Check patient_panel table
                panel_assignments = conn.execute("""
                    SELECT patient_id, provider_id, coordinator_id, status 
                    FROM patient_panel 
                    WHERE patient_id = ?
                """, (patient_info['patient_id'],)).fetchall()
                
                print(f"4. Patient Panel - Found {len(panel_assignments)} panel assignments")
                for panel in panel_assignments:
                    print(f"   - Provider: {panel['provider_id']}, Coordinator: {panel['coordinator_id']}, Status: {panel['status']}")
            else:
                print("❌ patient_id was not set - the assignment creation logic may not have been triggered")
        else:
            print("❌ No patient record found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_onboarding_fix()