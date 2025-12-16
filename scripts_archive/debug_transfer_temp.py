import shutil, pathlib, sys
import sqlite3
REPO_ROOT = pathlib.Path.cwd()
PROD_DB = REPO_ROOT / 'production.db'
BACKUP_DIR = REPO_ROOT / 'backups'
BACKUP_DIR.mkdir(exist_ok=True)
TEMP_DB = BACKUP_DIR / 'temp_debug_transfer.db'

shutil.copyfile(str(PROD_DB), str(TEMP_DB))
sys.path.insert(0, str(REPO_ROOT))
import src.database as database
database.DB_PATH = str(TEMP_DB)

sample = {
    'first_name': 'DbgFirst', 'last_name': 'DbgLast', 'date_of_birth': '1990-01-01',
    'phone_primary': '555-1111', 'email': 'dbg@example.com', 'gender':'Other'
}

onboarding_id = database.create_onboarding_workflow_instance(sample, None)
database.update_onboarding_checkbox_data(onboarding_id, {'appointment_contact_name':'dbg appt', 'medical_records_requested':1})
pid = database.transfer_onboarding_to_patient_table(onboarding_id)

print('onboarding_id', onboarding_id, 'patient_id', pid)

conn = sqlite3.connect(str(TEMP_DB))
cur = conn.cursor()
cur.execute('SELECT * FROM patients WHERE patient_id = ?', (pid,))
row = cur.fetchone()
print('direct sqlite row:', row)

cur.execute('SELECT COUNT(*) FROM patients')
print('patients count:', cur.fetchone()[0])

conn.close()
print('Temp DB kept at', TEMP_DB)
