#!/usr/bin/env python3
"""
Test script to simulate the exact form submission scenario from the onboarding dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src import database
from datetime import datetime, date, time

def test_form_simulation():
    """Simulate the exact form submission scenario"""
    print("=== Testing Form Simulation ===")
    
    # Find a stage 5 patient (Test5 Test5)
    patients = database.get_onboarding_queue()
    print(f"Found {len(patients)} patients in onboarding queue")
    
    if patients:
        print("Sample patient data structure:")
        print(patients[0].keys())
        print("First patient:", patients[0])
    
    test_patient = None
    
    for patient in patients:
        # Check what fields are available
        print(f"Patient: {patient}")
        if 'Test5' in patient.get('patient_name', ''):
            test_patient = patient
            break
    
    if not test_patient:
        print("❌ Test5 patient not found, using first stage 5 patient if available")
        for patient in patients:
            if 'Stage 5' in patient.get('current_stage', ''):
                test_patient = patient
                break
    
    if not test_patient:
        print("❌ No stage 5 patients found")
        return False
    
    print(f"Using patient: {test_patient}")
    
    # Get patient details
    patient_details = database.get_onboarding_patient_details(test_patient['onboarding_id'])
    print(f"Patient details retrieved: {patient_details}")
    
    # Simulate the exact form data that would be collected
    # This matches the form_data dictionary in the onboarding dashboard
    form_data = {
        'tv_date': date(2025, 1, 15),  # date object
        'tv_time': time(10, 30),       # time object
        'assigned_provider': 'Jackson, Anisha (anisha@myhealthteam.org)',  # string from selectbox
        'assigned_coordinator': 'Hernandez, Hector (hector@myhealthteam.org)',  # string from selectbox
        'tv_scheduled': True,          # boolean from checkbox
        'patient_notified': True,      # boolean from checkbox
        'initial_tv_completed': False  # boolean from checkbox
    }
    
    print("\nForm data to be saved:")
    for key, value in form_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # Test the save function with exact form data
    print(f"\n=== Calling save_onboarding_tv_scheduling_progress ===")
    print(f"Patient ID: {patient_details['onboarding_id']}")
    
    try:
        result = database.save_onboarding_tv_scheduling_progress(patient_details['onboarding_id'], form_data)
        print(f"Save result: {result}")
        
        if result:
            print("✅ Save successful!")
            
            # Verify the saved data
            updated_details = database.get_onboarding_patient_details(patient_details['onboarding_id'])
            print("\nVerified saved data:")
            print(f"  TV Date: {updated_details.get('tv_date')}")
            print(f"  TV Time: {updated_details.get('tv_time')}")
            print(f"  Provider User ID: {updated_details.get('assigned_provider_user_id')}")
            print(f"  Coordinator User ID: {updated_details.get('assigned_coordinator_user_id')}")
            print(f"  TV Scheduled: {updated_details.get('tv_scheduled')}")
            print(f"  Patient Notified: {updated_details.get('patient_notified')}")
            print(f"  Initial TV Completed: {updated_details.get('initial_tv_completed')}")
            
        else:
            print("❌ Save failed!")
            
    except Exception as e:
        print(f"❌ Exception during save: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return result

def test_edge_cases():
    """Test edge cases that might cause issues"""
    print("\n=== Testing Edge Cases ===")
    
    # Test with default selections
    form_data_with_defaults = {
        'tv_date': date(2025, 1, 15),
        'tv_time': time(10, 30),
        'assigned_provider': 'Select Provider...',  # Default selection
        'assigned_coordinator': 'Select Coordinator...',  # Default selection
        'tv_scheduled': True,
        'patient_notified': True,
        'initial_tv_completed': False
    }
    
    patients = database.get_onboarding_queue()
    stage5_patients = [p for p in patients if 'Stage 5' in p.get('current_stage', '')]
    if stage5_patients:
        test_patient = stage5_patients[0]
        print(f"Testing with default selections for patient {test_patient['onboarding_id']}")
        
        try:
            result = database.save_onboarding_tv_scheduling_progress(test_patient['onboarding_id'], form_data_with_defaults)
            print(f"Save with defaults result: {result}")
        except Exception as e:
            print(f"Exception with defaults: {e}")

if __name__ == "__main__":
    test_form_simulation()
    test_edge_cases()
    print("\nTest completed.")