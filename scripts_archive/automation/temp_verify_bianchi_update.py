import sqlite3
DB_PATH = r'D:\Git\myhealthteam2\Streamlit\production.db'
patient_id_str = 'SANCHEZ BIANCHI 03/11/1992'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

def cols(table):
    return {r['name'] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()}

print('--- Onboarding record for Bianchi Sanchez ---')
onb = cur.execute(
    """
    SELECT onboarding_id, first_name, last_name, patient_id, patient_status,
           stage4_complete, stage5_complete, completed_date, updated_date,
           tv_date, tv_time, assigned_provider_user_id, assigned_coordinator_user_id, initial_tv_provider
    FROM onboarding_patients
    WHERE UPPER(first_name)='BIANCHI' AND UPPER(last_name)='SANCHEZ'
    ORDER BY updated_date DESC
    LIMIT 1
    """
).fetchone()
print(dict(onb) if onb else 'none')

print('\n--- Patients table (available columns) ---')
pat_cols = cols('patients')
print(sorted(pat_cols))
sel = [c for c in ['patient_id','first_name','last_name','date_of_birth','facility','current_facility_id','provider_id','provider_name','coordinator_id','coordinator_name','initial_tv_provider','created_date','updated_date'] if c in pat_cols]
q = f"SELECT {', '.join(sel)} FROM patients WHERE patient_id = ?"
pat = cur.execute(q, (patient_id_str,)).fetchone()
print(dict(pat) if pat else 'none')

print('\n--- Patient assignments (active) ---')
assignments = cur.execute(
    """
    SELECT pa.patient_id, pa.provider_id, pu.full_name AS provider_name,
           pa.coordinator_id, cu.full_name AS coordinator_name, pa.status, pa.assignment_type, pa.created_date
    FROM patient_assignments pa
    LEFT JOIN users pu ON pa.provider_id = pu.user_id
    LEFT JOIN users cu ON pa.coordinator_id = cu.user_id
    WHERE pa.patient_id = ? AND pa.status = 'active'
    """,
    (patient_id_str,)
).fetchall()
print([dict(r) for r in assignments])

print('\n--- Patient panel (available columns) ---')
panel_cols = cols('patient_panel')
print(sorted(panel_cols))
sel2 = [c for c in ['patient_id','provider_id','coordinator_id','provider_name','coordinator_name','facility','current_facility_id','initial_tv_provider','tv_date','tv_time','updated_date'] if c in panel_cols]
q2 = f"SELECT {', '.join(sel2)} FROM patient_panel WHERE patient_id = ?"
panel = cur.execute(q2, (patient_id_str,)).fetchone()
print(dict(panel) if panel else 'none')
conn.close()