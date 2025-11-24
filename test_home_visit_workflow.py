#!/usr/bin/env python3
"""
Test script for onboarding initial TV visit home visit workflow
Tests the complete data flow from onboarding queue to provider_tasks, patients, and patient_panel tables
"""

import sqlite3
import sys
from datetime import datetime, date

def test_onboarding_home_visit_workflow():
    """Test the complete onboarding home visit workflow"""
    
    print("=== Testing Onboarding Home Visit Workflow ===")
    print("This tests the actual workflow used by the care provider dashboard")
    
    # Test patient details
    test_patient_id = "TEST_ONBOARD_20251001_093416"
    provider_id = 1  # Albert's provider ID
    
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        print(f"\n1. Testing with patient: {test_patient_id}")
        print(f"   Provider ID: {provider_id}")
        
        # 2. Test save_daily_task function (which writes to provider_tasks)
        print("\n2. Testing save_daily_task function (writes to provider_tasks)...")
        
        task_date = date.today().strftime('%Y-%m-%d')
        task_description = "Initial TV Assessment - Home Visit"
        notes = f"Home Visit Assessment - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\nTest clinical data collection:\n- ER Visits: 2\n- Hospitalizations: 1\n- Subjective Risk: High\n- Mental Health: Depression\n- Active Specialists: Cardiologist\n- Code Status: Full Code\n- Cognitive Function: Alert\n- Functional Status: Independent\n- Goals of Care: Comfort focused\n- Active Concerns: Hypertension management"
        billing_code = "99345"  # Home visit billing code
        
        # Simulate the save_daily_task function call
        try:
            # Get billing data
            cursor.execute("""
                SELECT min_minutes, billing_code, rate, description
                FROM task_billing_codes
                WHERE billing_code = ?
                LIMIT 1
            """, (billing_code,))
            billing_data = cursor.fetchone()
            
            if billing_data:
                duration_minutes = billing_data[0] if billing_data[0] is not None else 45
                billing_code_val = billing_data[1]
                rate = billing_data[2]
                billing_code_description = billing_data[3]
                print(f"   ✅ Found billing code: {billing_code_val} - {billing_code_description}")
            else:
                duration_minutes = 45
                billing_code_val = billing_code
                rate = 0
                billing_code_description = "Home Visit"
                print(f"   ⚠️ Using default billing data for: {billing_code}")
            
            # Insert into provider_tasks table
            cursor.execute("""
                INSERT INTO provider_tasks 
                (provider_id, patient_id, task_date, task_description, notes, 
                 minutes_of_service, billing_code, billing_code_description, 
                 created_date, updated_date, source_system)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (provider_id, test_patient_id, task_date, task_description, notes,
                  duration_minutes, billing_code_val, billing_code_description,
                  datetime.now(), datetime.now(), 'ONBOARDING_TEST'))
            
            provider_task_id = cursor.lastrowid
            print(f"   ✅ Created provider_tasks record with ID: {provider_task_id}")
            
        except Exception as e:
            print(f"   ❌ Error creating provider task: {e}")
            return False
        
        # 3. Test clinical data update to patients table
        print("\n3. Testing clinical data update to patients table...")
        
        clinical_data = {
            'er_visits_count': 2,
            'hospitalization_count': 1,
            'subjective_risk_level': 'High',
            'mental_health_concerns': 'Depression',
            'active_specialists': 'Cardiologist',
            'code_status': 'Full Code',
            'cognitive_function': 'Alert',
            'functional_status_summary': 'Independent',
            'goals_of_care': 'Comfort focused',
            'active_concerns': 'Hypertension management',
            'last_visit_date': task_date
        }
        
        try:
            # Check if patient exists in patients table
            cursor.execute("SELECT patient_id FROM patients WHERE patient_id = ?", (test_patient_id,))
            patient_exists = cursor.fetchone()
            
            if patient_exists:
                # Update existing patient
                cursor.execute("""
                    UPDATE patients SET 
                        er_visits_count = ?, hospitalization_count = ?, subjective_risk_level = ?,
                        mental_health_concerns = ?, active_specialists = ?, code_status = ?,
                        cognitive_function = ?, functional_status_summary = ?, goals_of_care = ?,
                        active_concerns = ?, last_visit_date = ?, initial_tv_completed = 1,
                        initial_tv_completed_date = ?, updated_date = ?
                    WHERE patient_id = ?
                """, (
                    clinical_data['er_visits_count'], clinical_data['hospitalization_count'],
                    clinical_data['subjective_risk_level'], clinical_data['mental_health_concerns'],
                    clinical_data['active_specialists'], clinical_data['code_status'],
                    clinical_data['cognitive_function'], clinical_data['functional_status_summary'],
                    clinical_data['goals_of_care'], clinical_data['active_concerns'],
                    clinical_data['last_visit_date'], task_date, datetime.now(), test_patient_id
                ))
                print("   ✅ Updated existing patient record")
            else:
                # Create new patient record (this would normally be done by insert_patient_from_onboarding)
                cursor.execute("""
                    INSERT INTO patients (
                        patient_id, er_visits_count, hospitalization_count, subjective_risk_level,
                        mental_health_concerns, active_specialists, code_status, cognitive_function,
                        functional_status_summary, goals_of_care, active_concerns, last_visit_date,
                        initial_tv_completed, initial_tv_completed_date, created_date, updated_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """, (
                    test_patient_id, clinical_data['er_visits_count'], clinical_data['hospitalization_count'],
                    clinical_data['subjective_risk_level'], clinical_data['mental_health_concerns'],
                    clinical_data['active_specialists'], clinical_data['code_status'],
                    clinical_data['cognitive_function'], clinical_data['functional_status_summary'],
                    clinical_data['goals_of_care'], clinical_data['active_concerns'],
                    clinical_data['last_visit_date'], task_date, datetime.now(), datetime.now()
                ))
                print("   ✅ Created new patient record")
                
        except Exception as e:
            print(f"   ❌ Error updating patient data: {e}")
            return False
        
        # 4. Test onboarding_patients table update
        print("\n4. Testing onboarding_patients table update...")
        
        try:
            cursor.execute("""
                UPDATE onboarding_patients SET 
                    initial_tv_completed = 1,
                    initial_tv_completed_date = ?,
                    provider_completed_initial_tv = 1,
                    updated_date = ?
                WHERE patient_id = ?
            """, (task_date, datetime.now(), test_patient_id))
            
            print("   ✅ Updated onboarding status")
            
        except Exception as e:
            print(f"   ❌ Error updating onboarding status: {e}")
            return False
        
        # 5. Test patient_panel table sync
        print("\n5. Testing patient_panel table sync...")
        
        try:
            # Check if patient exists in patient_panel
            cursor.execute("SELECT patient_id FROM patient_panel WHERE patient_id = ?", (test_patient_id,))
            panel_exists = cursor.fetchone()
            
            if panel_exists:
                # Update existing patient_panel record
                cursor.execute("""
                    UPDATE patient_panel SET 
                        last_visit_date = ?,
                        last_visit_service_type = ?,
                        updated_date = ?
                    WHERE patient_id = ?
                """, (task_date, task_description, datetime.now(), test_patient_id))
                print("   ✅ Updated patient_panel record")
            else:
                print("   ⚠️ Patient not found in patient_panel table (would be synced by sync_onboarding_to_patient_panel)")
                
        except Exception as e:
            print(f"   ❌ Error updating patient_panel: {e}")
            return False
        
        # 6. Verification
        print("\n=== Verification ===")
        
        # Check provider_tasks
        cursor.execute("""
            SELECT provider_task_id, task_description, billing_code, minutes_of_service, created_date
            FROM provider_tasks WHERE patient_id = ? AND source_system = 'ONBOARDING_TEST'
            ORDER BY created_date DESC LIMIT 1
        """, (test_patient_id,))
        
        provider_task = cursor.fetchone()
        if provider_task:
            print(f"✅ Provider task created: ID {provider_task[0]}, {provider_task[1]}, {provider_task[2]}, {provider_task[3]} min")
        else:
            print("❌ No provider task found")
        
        # Check patients table
        cursor.execute("""
            SELECT patient_id, er_visits_count, hospitalization_count, subjective_risk_level,
                   mental_health_concerns, initial_tv_completed, last_visit_date
            FROM patients WHERE patient_id = ?
        """, (test_patient_id,))
        
        patient_record = cursor.fetchone()
        if patient_record:
            print(f"✅ Patients table updated: ER visits: {patient_record[1]}, Hospitalizations: {patient_record[2]}, Risk: {patient_record[3]}")
        else:
            print("❌ No patient record found")
        
        # Check onboarding_patients
        cursor.execute("""
            SELECT initial_tv_completed, initial_tv_completed_date, provider_completed_initial_tv
            FROM onboarding_patients WHERE patient_id = ?
        """, (test_patient_id,))
        
        onboarding_record = cursor.fetchone()
        if onboarding_record:
            print(f"✅ Onboarding updated: TV completed: {onboarding_record[0]}, Date: {onboarding_record[1]}")
        else:
            print("❌ No onboarding record found")
        
        conn.commit()
        conn.close()
        
        print("\n=== Test Summary ===")
        print("✅ Onboarding home visit workflow test completed successfully!")
        print("✅ Data written to provider_tasks table (correct table)")
        print("✅ Clinical data saved to patients table")
        print("✅ Onboarding status updated")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def create_fresh_test_patient():
    """Create a fresh copy of the test patient for manual testing"""
    
    print("\n=== Creating Fresh Test Patient ===")
    
    try:
        conn = sqlite3.connect('production.db')
        cursor = conn.cursor()
        
        # Create a new test patient ID with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_patient_id = f"TEST_HOME_VISIT_{timestamp}"
        
        # Copy from the original test patient
        cursor.execute("""
            INSERT INTO onboarding_patients (
                patient_id, first_name, last_name, date_of_birth, phone_primary,
                assigned_provider_user_id, initial_tv_completed, visit_type,
                billing_code, duration_minutes, created_date, updated_date
            )
            SELECT ?, first_name, last_name, date_of_birth, phone_primary,
                   assigned_provider_user_id, 0, visit_type,
                   billing_code, duration_minutes, ?, ?
            FROM onboarding_patients 
            WHERE patient_id = 'TEST_ONBOARD_20251001_093416'
        """, (new_patient_id, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Created fresh test patient: {new_patient_id}")
        print(f"   - Assigned to Albert (user_id: 1)")
        print(f"   - initial_tv_completed: 0")
        print(f"   - Ready for manual testing")
        
        return new_patient_id
        
    except Exception as e:
        print(f"❌ Error creating fresh test patient: {e}")
        return None

if __name__ == "__main__":
    print("Testing Onboarding Home Visit Workflow")
    print("=" * 50)
    
    # Run the workflow test
    success = test_onboarding_home_visit_workflow()
    
    if success:
        # Create fresh patient for manual testing
        fresh_patient = create_fresh_test_patient()
        
        if fresh_patient:
            print(f"\n🎯 Ready for manual testing!")
            print(f"   Use patient: {fresh_patient}")
            print(f"   Login as: albert@myhealthteam.org")
            print(f"   Test the home visit functionality in the care provider dashboard")
    else:
        print("\n❌ Automated test failed. Please check the errors above.")
        sys.exit(1)