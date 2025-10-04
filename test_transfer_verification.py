#!/usr/bin/env python3

import sys
sys.path.append('src')
from database import sync_onboarding_to_patient_panel, get_db_connection

def test_transfer_functions():
    """Test the updated transfer functions"""
    print("Testing transfer functions...")
    
    # Test with Test11 data
    result = sync_onboarding_to_patient_panel('TEST11 TEST11 10/06/1949')
    print(f'Transfer result: {result}')
    
    # Verify the data was transferred correctly
    conn = get_db_connection()
    try:
        # Check onboarding data
        onboarding = conn.execute("""
            SELECT patient_id, facility_assignment, tv_date, tv_time, initial_tv_provider, 
                   assigned_provider_user_id, assigned_coordinator_user_id 
            FROM onboarding_patients WHERE patient_id LIKE '%TEST11%'
        """).fetchone()
        print(f'Onboarding data: {dict(onboarding) if onboarding else None}')
        
        # Check patients table
        patient = conn.execute("""
            SELECT patient_id, facility, tv_date, tv_time, initial_tv_provider, assigned_coordinator_id 
            FROM patients WHERE patient_id LIKE '%TEST11%'
        """).fetchone()
        print(f'Patients data: {dict(patient) if patient else None}')
        
        # Check patient_panel table
        panel = conn.execute("""
            SELECT patient_id, facility, current_facility_id, provider_id, coordinator_id, 
                   initial_tv_completed_date, initial_tv_provider 
            FROM patient_panel WHERE patient_id LIKE '%TEST11%'
        """).fetchone()
        print(f'Patient panel data: {dict(panel) if panel else None}')
        
        # Verify all critical fields are populated
        if patient and panel:
            missing_fields = []
            
            # Check patients table critical fields
            if not patient[1]:  # facility
                missing_fields.append('patients.facility')
            if not patient[2]:  # tv_date
                missing_fields.append('patients.tv_date')
            if not patient[3]:  # tv_time
                missing_fields.append('patients.tv_time')
            if not patient[4]:  # initial_tv_provider
                missing_fields.append('patients.initial_tv_provider')
            if not patient[5]:  # assigned_coordinator_id
                missing_fields.append('patients.assigned_coordinator_id')
                
            # Check patient_panel table critical fields
            if not panel[1]:  # facility
                missing_fields.append('patient_panel.facility')
            if not panel[2]:  # current_facility_id
                missing_fields.append('patient_panel.current_facility_id')
            if not panel[3]:  # provider_id
                missing_fields.append('patient_panel.provider_id')
            if not panel[4]:  # coordinator_id
                missing_fields.append('patient_panel.coordinator_id')
            if not panel[5]:  # initial_tv_completed_date
                missing_fields.append('patient_panel.initial_tv_completed_date')
            if not panel[6]:  # initial_tv_provider
                missing_fields.append('patient_panel.initial_tv_provider')
            
            if missing_fields:
                print(f"WARNING: Missing fields: {missing_fields}")
                return False
            else:
                print("SUCCESS: All critical fields are populated!")
                return True
        else:
            print("ERROR: Patient or panel data not found")
            return False
            
    finally:
        conn.close()

if __name__ == "__main__":
    test_transfer_functions()