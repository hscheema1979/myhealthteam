import sqlite3, os
DB='production.db'
print('Using DB:', os.path.abspath(DB))
conn = sqlite3.connect(DB)
cur = conn.cursor()

def print_table(name):
    print('\nPRAGMA table_info(%s):' % name)
    try:
        rows = cur.execute(f"PRAGMA table_info('{name}')").fetchall()
        if not rows:
            print('  <table not found or no columns>')
        for r in rows:
            print(' ', r)
    except Exception as e:
        print('  Error reading table info:', e)

print_table('workflow_instances')
print_table('onboarding_patients')

# Attempt a safe insert (rolled back) into onboarding_patients
try:
    conn.execute('BEGIN')
    cur = conn.execute("""
        INSERT INTO onboarding_patients (first_name, last_name, date_of_birth, patient_status)
        VALUES (?, ?, ?, ?)
    """, ('Automated', 'Test', '1980-01-01', 'Active'))
    rowid = cur.lastrowid
    print('\nInserted onboarding_id (will rollback):', rowid)
    conn.rollback()
    print('Transaction rolled back; no changes persisted.')
except Exception as e:
    print('\nError performing insert:', e)
finally:
    conn.close()
