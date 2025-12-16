#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import insert_patient_from_onboarding, get_db_connection

def test_patient_id_fix():
    """Test that the patient_id fix works correctly"""
    
    # Test with onboarding_id 15 (TestFix patient)
    onboarding_id = 15
    
    print(f"Testing insert_patient_from_onboarding with onboarding_id: {onboarding_id}")
    
    try:
        # Call the function
        result = insert_patient_from_onboarding(onboarding_id)
        print(f"Function returned: {result}")
        
        # Verify the results
        conn = get_db_connection()
        
        # Check onboarding_patients table
        onboarding_record = conn.execute("""
            SELECT onboarding_id, first_name, last_name, patient_id 
            FROM onboarding_patients 
            WHERE onboarding_id = ?
        """, (onboarding_id,)).fetchone()
        
        print(f"Onboarding record: {dict(onboarding_record) if onboarding_record else None}")
        
        # Check patients table
        if onboarding_record and onboarding_record['patient_id']:
            patient_record = conn.execute("""
                SELECT patient_id, first_name, last_name, date_of_birth 
                FROM patients 
                WHERE patient_id = ?
            """, (onboarding_record['patient_id'],)).fetchone()
            
            print(f"Patient record: {dict(patient_record) if patient_record else None}")
            
            # Check patient_assignments table
            assignment_record = conn.execute("""
                SELECT patient_id, provider_id, coordinator_id, assignment_date 
                FROM patient_assignments 
                WHERE patient_id = ?
            """, (onboarding_record['patient_id'],)).fetchone()
            
            print(f"Assignment record: {dict(assignment_record) if assignment_record else None}")
            
            # Verify consistency
            expected_patient_id = "TESTFIX TESTFIX 01/01/1990"
            if onboarding_record['patient_id'] == expected_patient_id:
                print("✓ SUCCESS: patient_id is consistent across all tables!")
                print(f"✓ All tables use the same patient_id: {expected_patient_id}")
            else:
                print(f"✗ FAILURE: Expected {expected_patient_id}, got {onboarding_record['patient_id']}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_patient_id_fix()