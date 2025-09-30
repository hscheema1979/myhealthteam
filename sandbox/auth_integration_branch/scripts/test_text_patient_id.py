#!/usr/bin/env python3
"""
Test script to verify that the updated patient_id generation works correctly with text-based format.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import get_db_connection, generate_patient_id, create_onboarding_workflow_instance, transfer_onboarding_to_patient_table

def test_text_patient_id_generation():
    """Test the new text-based patient_id generation"""
    print("Testing text-based patient_id generation...")
    
    # Test the generate_patient_id function directly
    test_cases = [
        ("John", "Doe", "1990-01-15"),
        ("Mary Jane", "Smith-Wilson", "1985-12-25"),
        ("José", "García", "1975-06-30"),
        ("", "TestEmpty", "2000-01-01"),  # Edge case: empty first name
        ("TestEmpty", "", "2000-01-01"),  # Edge case: empty last name
    ]
    
    print("\n1. Testing generate_patient_id function:")
    for first_name, last_name, dob in test_cases:
        patient_id = generate_patient_id(first_name, last_name, dob)
        print(f"  {first_name} {last_name} ({dob}) -> {patient_id}")
    
    # Test with a new onboarding patient
    print("\n2. Testing complete onboarding workflow with text-based patient_id:")
    
    # Create test patient data
    test_patient_data = {
        'first_name': 'TextTest',
        'last_name': 'Patient',
        'date_of_birth': '1995-03-20',
        'phone_primary': '555-0123',
        'email': 'texttest@example.com',
        'gender': 'M'
    }
    
    try:
        # Create onboarding workflow instance
        onboarding_id = create_onboarding_workflow_instance(test_patient_data, pot_user_id=1)
        print(f"  Created onboarding record with ID: {onboarding_id}")
        
        # Transfer to patient table (this should use text-based patient_id)
        patient_id = transfer_onboarding_to_patient_table(onboarding_id)
        print(f"  Generated patient_id: {patient_id}")
        
        # Verify the patient_id format
        expected_patient_id = generate_patient_id(
            test_patient_data['first_name'], 
            test_patient_data['last_name'], 
            test_patient_data['date_of_birth']
        )
        print(f"  Expected patient_id: {expected_patient_id}")
        
        if patient_id == expected_patient_id:
            print("  ✓ SUCCESS: Patient ID matches expected text-based format!")
        else:
            print("  ✗ FAILURE: Patient ID does not match expected format!")
            return False
        
        # Verify in database
        conn = get_db_connection()
        try:
            # Check patients table
            patient_record = conn.execute(
                "SELECT patient_id, first_name, last_name, date_of_birth FROM patients WHERE patient_id = ?", 
                (patient_id,)
            ).fetchone()
            
            if patient_record:
                print(f"  ✓ Found in patients table: {dict(patient_record)}")
            else:
                print("  ✗ NOT found in patients table!")
                return False
            
            # Check onboarding_patients table
            onboarding_record = conn.execute(
                "SELECT patient_id, first_name, last_name, date_of_birth FROM onboarding_patients WHERE onboarding_id = ?", 
                (onboarding_id,)
            ).fetchone()
            
            if onboarding_record and onboarding_record[0] == patient_id:
                print(f"  ✓ Found in onboarding_patients table: {dict(onboarding_record)}")
            else:
                print("  ✗ NOT found in onboarding_patients table or patient_id mismatch!")
                return False
            
            # Test duplicate prevention
            print("\n3. Testing duplicate prevention:")
            duplicate_patient_id = transfer_onboarding_to_patient_table(onboarding_id)
            if duplicate_patient_id is None:
                print("  ✓ SUCCESS: Duplicate prevention working correctly!")
            else:
                print(f"  ✗ FAILURE: Duplicate created with patient_id: {duplicate_patient_id}")
                return False
            
        finally:
            # Clean up test data
            conn.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
            conn.execute("DELETE FROM onboarding_patients WHERE onboarding_id = ?", (onboarding_id,))
            conn.execute("DELETE FROM patient_panel WHERE patient_id = ?", (patient_id,))
            conn.commit()
            conn.close()
            print("  ✓ Test data cleaned up")
        
        print("\n✓ ALL TESTS PASSED! Text-based patient_id generation is working correctly.")
        return True
        
    except Exception as e:
        print(f"  ✗ ERROR during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_text_patient_id_generation()
    sys.exit(0 if success else 1)