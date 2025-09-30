"""
Test transfer of onboarding data to patients table.
This script creates a temporary onboarding patient, fills clinical/onboarding fields,
runs `transfer_onboarding_to_patient_table`, prints before/after, then cleans up.
"""
import sys, os, shutil
# Ensure repo root is in sys.path for 'from src import database'
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)
from src import database

# Patch: use a copy of production.db for all DB operations
ORIG_DB = os.path.join(repo_root, 'production.db')
TEST_DB = os.path.join(repo_root, 'test_transfer.db')
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
shutil.copy2(ORIG_DB, TEST_DB)
database.DB_PATH = TEST_DB
import pprint

def main():
    pp = pprint.PrettyPrinter(indent=2)

    sample = {
        'first_name': 'TestFirst',
        'last_name': 'TestLast',
        'date_of_birth': '1980-01-01',
        'phone_primary': '555-0100',
        'email': 'test@example.com',
        'gender': 'Other',
        'address_street': '123 Test St',
        'address_city': 'Testville',
        'address_state': 'TS',
        'address_zip': '00000',
        'emergency_contact_name': 'EC Name',
        'emergency_contact_phone': '555-9999',
        'insurance_provider': 'TestIns',
        'policy_number': 'P-TEST-1',
        'patient_status': 'Active',
        'facility_assignment': None,
    }

    print('Creating onboarding record...')
    onboarding_id = database.create_onboarding_workflow_instance(sample, None)
    print('onboarding_id =', onboarding_id)

    # Populate onboarding checkbox/clinical fields
    checkbox_data = {
        'appointment_contact_name': 'Appt Contact',
        'appointment_contact_phone': '555-0200',
        'appointment_contact_email': 'appts@test.com',
        'medical_contact_name': 'Med Contact',
        'medical_contact_phone': '555-0300',
        'medical_contact_email': 'med@test.com',
        'primary_care_provider': 'Dr. PCP',
        'pcp_last_seen': '2024-05-01',
        'active_specialist': 'Dr. Specialist',
        'specialist_last_seen': '2024-06-15',
        'chronic_conditions_onboarding': 'Hypertension;Diabetes',
        'mh_depression': 1,
        'mh_anxiety': 0,
        'medical_records_requested': 1,
    }

    database.update_onboarding_checkbox_data(onboarding_id, checkbox_data)

    print('\nOnboarding row (before transfer):')
    ob = database.get_onboarding_patient_details(onboarding_id)
    pp.pprint(ob)

    print('\nTransferring onboarding to patients...')
    try:
        patient_id = database.transfer_onboarding_to_patient_table(onboarding_id)
        print('transfer returned patient_id =', patient_id)
    except Exception as e:
        print('Transfer failed:', e)
        cleanup(onboarding_id, None)
        return

    print('\nPatient row (after transfer):')
    p = database.get_patient_details_by_id(patient_id)
    pp.pprint(dict(p) if p else p)

    # Cleanup: remove test patient and onboarding records
    cleanup(onboarding_id, patient_id)

def cleanup(onboarding_id, patient_id):
    print('\nCleaning up test data...')
    conn = database.get_db_connection()
    cur = conn.cursor()
    try:
        if patient_id:
            cur.execute('DELETE FROM patients WHERE patient_id = ?', (patient_id,))
            print('Deleted patient', patient_id)
        # delete onboarding tasks and onboarding record
        cur.execute('DELETE FROM onboarding_tasks WHERE onboarding_id = ?', (onboarding_id,))
        cur.execute('DELETE FROM onboarding_patients WHERE onboarding_id = ?', (onboarding_id,))
        conn.commit()
        print('Deleted onboarding and tasks for', onboarding_id)
    except Exception as e:
        print('Cleanup error:', e)
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    main()
