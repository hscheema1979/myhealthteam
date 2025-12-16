import sqlite3

DB_FILE = 'production.db'

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

def cols(table):
    try:
        cur.execute(f"PRAGMA table_info({table});")
        return [r[1] for r in cur.fetchall()]
    except Exception as e:
        return f"ERROR: {e}"

print('patients_cols=', cols('patients'))
print('onboarding_patients_cols=', cols('onboarding_patients'))

conn.close()
