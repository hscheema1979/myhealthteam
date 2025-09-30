"""
Run onboarding -> patients transfer test against a temporary copy of production.db
to avoid locking the live DB. This copies DB to `backups/temp_transfer_test.db`,
points `src.database.DB_PATH` to it, runs the transfer, prints results, and removes the copy.
"""
import shutil
import pathlib
import tempfile
import os
import runpy
import sys

REPO_ROOT = pathlib.Path.cwd()
PROD_DB = REPO_ROOT / 'production.db'
BACKUP_DIR = REPO_ROOT / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)
TEMP_DB = BACKUP_DIR / 'temp_transfer_test.db'

def main():
    print('Creating temp DB copy at', TEMP_DB)
    shutil.copyfile(str(PROD_DB), str(TEMP_DB))

    # Run the test script but ensure repo root is on sys.path
    sys.path.insert(0, str(REPO_ROOT))

    # Import src.database and override DB_PATH
    import src.database as database
    database.DB_PATH = str(TEMP_DB)

    try:
        # Reuse logic from test_transfer_onboarding but operate here to avoid import ordering
        sample = {
            'first_name': 'TempTestFirst',
            'last_name': 'TempTestLast',
            'date_of_birth': '1980-01-01',
            'phone_primary': '555-0100',
            'email': 'temp-test@example.com',
            'gender': 'Other',
            'address_street': '123 Temp St',
            'address_city': 'Tempville',
            'address_state': 'TS',
            'address_zip': '00000',
            'emergency_contact_name': 'EC Name',
            'emergency_contact_phone': '555-9999',
            'insurance_provider': 'TempIns',
            'policy_number': 'P-TEMP-1',
            'patient_status': 'Active',
            'facility_assignment': None,
        }

        print('Creating onboarding record in temp DB...')
        onboarding_id = database.create_onboarding_workflow_instance(sample, None)
        print('onboarding_id =', onboarding_id)

        checkbox_data = {
            'appointment_contact_name': 'Temp Appt Contact',
            'appointment_contact_phone': '555-0200',
            'appointment_contact_email': 'appts-temp@test.com',
            'medical_contact_name': 'Temp Med Contact',
            'medical_contact_phone': '555-0300',
            'medical_contact_email': 'med-temp@test.com',
            'primary_care_provider': 'Dr. Temp PCP',
            'pcp_last_seen': '2024-05-01',
            'active_specialist': 'Dr. Temp Specialist',
            'specialist_last_seen': '2024-06-15',
            'chronic_conditions_onboarding': 'Hypertension;Diabetes',
            'mh_depression': 1,
            'mh_anxiety': 0,
            'medical_records_requested': 1,
        }

        database.update_onboarding_checkbox_data(onboarding_id, checkbox_data)

        print('\nOnboarding row (before transfer):')
        ob = database.get_onboarding_patient_details(onboarding_id)
        print(ob)

        print('\nTransferring onboarding to patients...')
        patient_id = database.transfer_onboarding_to_patient_table(onboarding_id)
        print('transfer returned patient_id =', patient_id)

        print('\nPatient row (after transfer):')
        p = database.get_patient_details_by_id(patient_id)
        print(dict(p) if p else p)

    finally:
        # Remove temp DB
        try:
            os.remove(TEMP_DB)
            print('\nRemoved temp DB', TEMP_DB)
        except Exception as e:
            print('Could not remove temp DB:', e)

if __name__ == '__main__':
    main()
