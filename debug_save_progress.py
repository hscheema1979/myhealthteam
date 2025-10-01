#!/usr/bin/env python3
"""
Debug script to test Save Progress functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import database
from datetime import datetime, date, time
import traceback

def test_save_progress():
    """Test the save progress functionality"""
    
    # Get a patient in stage 5
    conn = database.get_db_connection()
    try:
        cursor = conn.execute("""
            SELECT onboarding_id, first_name, last_name, stage5_complete,
                   tv_date, tv_time, tv_scheduled, patient_notified, initial_tv_completed,
                   assigned_provider_user_id, assigned_coordinator_user_id
            FROM onboarding_patients 
            WHERE stage4_complete = 1 AND stage5_complete = 0
            ORDER BY updated_date DESC 
            LIMIT 1
        """)
        patient = cursor.fetchone()
        
        if not patient:
            print("No patients found in stage 5 for testing")
            return
            
        print(f"Testing with patient: {patient[1]} {patient[2]} (ID: {patient[0]})")
        print(f"Current state:")
        print(f"  TV Date: {patient[4]}")
        print(f"  TV Time: {patient[5]}")
        print(f"  TV Scheduled: {patient[6]}")
        print(f"  Patient Notified: {patient[7]}")
        print(f"  Initial TV Completed: {patient[8]}")
        print(f"  Provider User ID: {patient[9]}")
        print(f"  Coordinator User ID: {patient[10]}")
        print()
        
    finally:
        conn.close()
    
    # Test form data that simulates what would come from the Streamlit form
    form_data = {
        'tv_date': date(2025, 1, 20),
        'tv_time': time(14, 30),
        'assigned_provider': 'Jackson, Anisha (anisha@myhealthteam.org)',
        'assigned_coordinator': 'Hernandez, Hector (hector@myhealthteam.org)',
        'tv_scheduled': True,
        'patient_notified': True,
        'initial_tv_completed': False  # This should be allowed to be False for Save Progress
    }
    
    print("Testing Save Progress with form data:")
    for key, value in form_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    print()
    
    # Test the save function
    print("=== Calling save_onboarding_tv_scheduling_progress ===")
    try:
        result = database.save_onboarding_tv_scheduling_progress(patient[0], form_data)
        print(f"Save result: {result}")
        
        if result:
            print("✅ Save Progress successful!")
            
            # Verify the data was saved
            print("\n=== Verifying saved data ===")
            updated_patient = database.get_onboarding_patient_details(patient[0])
            print("Updated data:")
            print(f"  TV Date: {updated_patient.get('tv_date')}")
            print(f"  TV Time: {updated_patient.get('tv_time')}")
            print(f"  TV Scheduled: {updated_patient.get('tv_scheduled')}")
            print(f"  Patient Notified: {updated_patient.get('patient_notified')}")
            print(f"  Initial TV Completed: {updated_patient.get('initial_tv_completed')}")
            print(f"  Provider User ID: {updated_patient.get('assigned_provider_user_id')}")
            print(f"  Coordinator User ID: {updated_patient.get('assigned_coordinator_user_id')}")
            print(f"  Stage 5 Complete: {updated_patient.get('stage5_complete')}")
            
        else:
            print("❌ Save Progress failed!")
            
    except Exception as e:
        print(f"❌ Exception during save: {e}")
        print(f"Exception type: {type(e).__name__}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_save_progress()