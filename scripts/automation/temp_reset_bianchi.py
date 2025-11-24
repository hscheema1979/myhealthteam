import sqlite3
DB_PATH = r'D:\Git\myhealthteam2\Streamlit\production.db'
ONBOARDING_ID = 18  # Bianchi Sanchez
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
# Show before
row = cur.execute("SELECT onboarding_id, first_name, last_name, patient_id, patient_status, stage4_complete, stage5_complete, completed_date FROM onboarding_patients WHERE onboarding_id=?", (ONBOARDING_ID,)).fetchone()
print('BEFORE:', dict(row) if row else 'not found')
# Reset patient_status to Active, clear completed_date, set stage5_complete=0
cur.execute("""
    UPDATE onboarding_patients
    SET patient_status = 'Active',
        stage5_complete = 0,
        completed_date = NULL,
        updated_date = datetime('now')
    WHERE onboarding_id = ?
""", (ONBOARDING_ID,))
# If patient_id exists, mark stage4_complete = 1 to enable Stage 5 flow
cur.execute("""
    UPDATE onboarding_patients
    SET stage4_complete = 1,
        updated_date = datetime('now')
    WHERE onboarding_id = ? AND patient_id IS NOT NULL
""", (ONBOARDING_ID,))
conn.commit()
row = cur.execute("SELECT onboarding_id, first_name, last_name, patient_id, patient_status, stage4_complete, stage5_complete, completed_date FROM onboarding_patients WHERE onboarding_id=?", (ONBOARDING_ID,)).fetchone()
print('AFTER:', dict(row) if row else 'not found')
conn.close()