#!/usr/bin/env python3
"""
Test script to debug the save progress issue in stage 5 onboarding
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import database
from datetime import datetime, date, time
import traceback

def test_save_progress():
    """Test the save_onboarding_tv_scheduling_progress function"""
    
    # First, let's find an onboarding patient in stage 5
    print("=== Finding onboarding patients in stage 5 ===")
    
    conn = database.get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT onboarding_id, first_name, last_name, stage5_complete, 
                   assigned_provider_user_id, assigned_coordinator_user_id,
                   tv_date, tv_time, tv_scheduled, patient_notified, initial_tv_completed
            FROM onboarding_patients 
            WHERE stage4_complete = 1 
            ORDER BY updated_date DESC 
            LIMIT 5
        """)
        patients = cursor.fetchall()
        
        if not patients:
            print("No patients found in stage 4+ for testing")
            return
            
        for patient in patients:
            print(f"Patient: {patient[1]} {patient[2]} (ID: {patient[0]})")
            print(f"  Stage 5 Complete: {patient[3]}")
            print(f"  Provider ID: {patient[4]}")
            print(f"  Coordinator ID: {patient[5]}")
            print(f"  TV Date: {patient[6]}")
            print(f"  TV Time: {patient[7]}")
            print(f"  TV Scheduled: {patient[8]}")
            print(f"  Patient Notified: {patient[9]}")
            print(f"  Initial TV Completed: {patient[10]}")
            print()
            
    finally:
        conn.close()
    
    if not patients:
        return
        
    # Use the first patient for testing
    test_patient = patients[0]
    onboarding_id = test_patient[0]
    
    print(f"=== Testing save progress for patient {test_patient[1]} {test_patient[2]} (ID: {onboarding_id}) ===")
    
    # Test data similar to what would come from the form
    test_form_data = {
        'tv_date': date(2025, 1, 15),
        'tv_time': time(10, 30),
        'assigned_provider': 'Jackson, Anisha (anisha@myhealthteam.org)',
        'assigned_coordinator': 'Hernandez, Hector (hector@myhealthteam.org)',
        'tv_scheduled': True,
        'patient_notified': True,
        'initial_tv_completed': False
    }
    
    print("Test form data:")
    for key, value in test_form_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    print()
    
    # Test the save function
    print("=== Testing save_onboarding_tv_scheduling_progress ===")
    try:
        result = database.save_onboarding_tv_scheduling_progress(onboarding_id, test_form_data)
        print(f"Save result: {result}")
        
        if result:
            print("✅ Save successful!")
            
            # Verify the data was saved
            print("\n=== Verifying saved data ===")
            conn = database.get_db_connection()
            try:
                cursor = conn.execute("""
                    SELECT tv_date, tv_time, assigned_provider_user_id, assigned_coordinator_user_id,
                           tv_scheduled, patient_notified, initial_tv_completed, updated_date
                    FROM onboarding_patients 
                    WHERE onboarding_id = ?
                """, (onboarding_id,))
                saved_data = cursor.fetchone()
                
                if saved_data:
                    print("Saved data:")
                    print(f"  TV Date: {saved_data[0]}")
                    print(f"  TV Time: {saved_data[1]}")
                    print(f"  Provider User ID: {saved_data[2]}")
                    print(f"  Coordinator User ID: {saved_data[3]}")
                    print(f"  TV Scheduled: {saved_data[4]}")
                    print(f"  Patient Notified: {saved_data[5]}")
                    print(f"  Initial TV Completed: {saved_data[6]}")
                    print(f"  Updated Date: {saved_data[7]}")
                else:
                    print("❌ No data found after save")
                    
            finally:
                conn.close()
        else:
            print("❌ Save failed!")
            
    except Exception as e:
        print(f"❌ Exception during save: {e}")
        print(f"Exception type: {type(e).__name__}")
        print("Traceback:")
        traceback.print_exc()

def test_user_lookup():
    """Test user lookup functionality"""
    print("\n=== Testing user lookup ===")
    
    test_users = [
        'Jackson, Anisha (anisha@myhealthteam.org)',
        'Hernandez, Hector (hector@myhealthteam.org)',
        'Select Provider...',
        'Select Coordinator...'
    ]
    
    conn = database.get_db_connection()
    try:
        for user_string in test_users:
            print(f"\nTesting: '{user_string}'")
            
            if user_string in ['Select Provider...', 'Select Coordinator...']:
                print("  -> Skipped (default selection)")
                continue
                
            try:
                # Extract username from format "Full Name (username)"
                username = user_string.split('(')[-1].replace(')', '').strip()
                print(f"  Extracted username: '{username}'")
                
                cursor = conn.execute("SELECT user_id, full_name, role FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                
                if result:
                    print(f"  Found user: ID={result[0]}, Name='{result[1]}', Role='{result[2]}'")
                else:
                    print(f"  ❌ User not found for username: '{username}'")
                    
            except Exception as e:
                print(f"  ❌ Error processing user string: {e}")
                
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting save progress debug test...")
    test_user_lookup()
    test_save_progress()
    print("\nTest completed.")