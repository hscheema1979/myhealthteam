import sqlite3
DB_PATH = r'D:\Git\myhealthteam2\Streamlit\production.db'
ONBOARDING_ID = 18
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
print('Before reset:')
row = cur.execute("SELECT onboarding_id, patient_status, stage4_complete, stage5_complete, completed_date, updated_date FROM onboarding_patients WHERE onboarding_id = ?", (ONBOARDING_ID,)).fetchone()
print(dict(row) if row else 'not found')

cur.execute(
    """
    UPDATE onboarding_patients
    SET patient_status = 'Active',
        stage5_complete = 0,
        completed_date = NULL,
        updated_date = CURRENT_TIMESTAMP
    WHERE onboarding_id = ?
    """,
    (ONBOARDING_ID,)
)
conn.commit()

print('After reset:')
row2 = cur.execute("SELECT onboarding_id, patient_status, stage4_complete, stage5_complete, completed_date, updated_date FROM onboarding_patients WHERE onboarding_id = ?", (ONBOARDING_ID,)).fetchone()
print(dict(row2) if row2 else 'not found')
conn.close()