#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import create_onboarding_workflow_instance, insert_patient_from_onboarding, get_db_connection

def test_complete_workflow():
    """Test the complete workflow from onboarding creation to patient insertion"""
    
    # Create a new onboarding patient
    patient_data = {
        'first_name': 'NewTest',
        'last_name': 'Patient',
        'date_of_birth': '1985-05-15',
        'gender': 'Female',
        'phone_primary': '555-0123',
        'email': 'newtest@example.com'
    }
    
    pot_user_id = 1  # Some POT user
    
    print("Creating new onboarding workflow instance...")
    onboarding_id = create_onboarding_workflow_instance(patient_data, pot_user_id)
    print(f"Created onboarding_id: {onboarding_id}")
    
    # Check initial state
    conn = get_db_connection()
    onboarding_record = conn.execute("""
        SELECT onboarding_id, first_name, last_name, patient_id 
        FROM onboarding_patients WHERE onboarding_id = ?
    """, (onboarding_id,)).fetchone()
    
    print(f"Initial onboarding record: {dict(onboarding_record) if onboarding_record else None}")
    
    # Now run the insert_patient_from_onboarding function
    print(f"\nRunning insert_patient_from_onboarding with onboarding_id: {onboarding_id}")
    result_patient_id = insert_patient_from_onboarding(onboarding_id)
    print(f"Function returned: {result_patient_id}")
    
    # Verify all records
    onboarding_record = conn.execute("""
        SELECT onboarding_id, first_name, last_name, patient_id 
        FROM onboarding_patients WHERE onboarding_id = ?
    """, (onboarding_id,)).fetchone()
    
    patient_record = conn.execute("""
        SELECT patient_id, first_name, last_name, date_of_birth 
        FROM patients WHERE patient_id = ?
    """, (result_patient_id,)).fetchone()
    
    assignment_record = conn.execute("""
        SELECT patient_id, provider_id, coordinator_id, assignment_date 
        FROM patient_assignments WHERE patient_id = ?
    """, (result_patient_id,)).fetchone()
    
    print(f"Final onboarding record: {dict(onboarding_record) if onboarding_record else None}")
    print(f"Patient record: {dict(patient_record) if patient_record else None}")
    print(f"Assignment record: {dict(assignment_record) if assignment_record else None}")
    
    # Verify consistency
    if onboarding_record and patient_record and onboarding_record['patient_id'] == patient_record['patient_id']:
        if assignment_record:
            if assignment_record['patient_id'] == patient_record['patient_id']:
                print("✓ SUCCESS: Complete workflow works correctly!")
                print(f"✓ All tables use the same patient_id: {result_patient_id}")
                print("✓ Assignment record created successfully")
            else:
                print("✗ FAILURE: Assignment patient_id doesn't match")
        else:
            print("✓ SUCCESS: Complete workflow works correctly!")
            print(f"✓ All tables use the same patient_id: {result_patient_id}")
            print("ℹ No assignment record created (no provider/coordinator assigned - this is expected)")
    else:
        print("✗ FAILURE: Inconsistent patient_id between onboarding and patient tables")
    
    conn.close()

if __name__ == "__main__":
    test_complete_workflow()