import sqlite3
DB_PATH = r'D:\Git\myhealthteam2\Streamlit\production.db'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
row = cur.execute(
    """
    SELECT patient_id, first_name, last_name, date_of_birth
    FROM patients
    WHERE UPPER(first_name)='BIANCHI' AND UPPER(last_name)='SANCHEZ'
    ORDER BY created_date DESC
    LIMIT 5
    """
).fetchone()
print('PATIENTS TABLE RECORD:', dict(row) if row else 'none')
conn.close()