import sys
sys.path.append('src')
import database

# Check Test9 in onboarding_patients (using the actual name format)
conn = database.get_db_connection()
onboarding = conn.execute('SELECT onboarding_id, first_name, last_name, patient_id, stage2_complete, stage5_complete FROM onboarding_patients WHERE first_name = "Test9"').fetchone()
if onboarding:
    print('Test9 Onboarding Record:')
    print(f'  onboarding_id: {onboarding[0]}')
    print(f'  name: {onboarding[1]} {onboarding[2]}')
    print(f'  patient_id: {onboarding[3]}')
    print(f'  stage2_complete: {onboarding[4]}')
    print(f'  stage5_complete: {onboarding[5]}')
    
    # Check if patient exists in patients table
    if onboarding[3]:
        patient = conn.execute('SELECT patient_id, first_name, last_name FROM patients WHERE patient_id = ?', (onboarding[3],)).fetchone()
        if patient:
            print(f'  Found in patients table: {patient[1]} {patient[2]} (ID: {patient[0]})')
        else:
            print('  NOT found in patients table')
            
        # Check patient_assignments
        assignments = conn.execute('SELECT assignment_id, provider_id, coordinator_id FROM patient_assignments WHERE patient_id = ?', (onboarding[3],)).fetchall()
        if assignments:
            print(f'  Patient assignments: {len(assignments)} found')
            for assignment in assignments:
                print(f'    Assignment ID: {assignment[0]}, Provider: {assignment[1]}, Coordinator: {assignment[2]}')
        else:
            print('  No patient assignments found')
            
        # Check patient_panel
        panel = conn.execute('SELECT patient_id, provider_id, coordinator_id FROM patient_panel WHERE patient_id = ?', (onboarding[3],)).fetchone()
        if panel:
            print(f'  Found in patient_panel: Provider {panel[1]}, Coordinator: {panel[2]}')
        else:
            print('  NOT found in patient_panel')
    else:
        print('  No patient_id assigned yet')
else:
    print('Test9 not found in onboarding_patients')

conn.close()