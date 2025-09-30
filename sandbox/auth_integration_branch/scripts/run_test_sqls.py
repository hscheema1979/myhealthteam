import sqlite3
import pathlib

DB = 'production.db'
BASE = pathlib.Path('src/sql')
SCRIPTS = ['test_patient_simple.sql', 'test_patient_column_mapping.sql']

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

for script in SCRIPTS:
    path = BASE / script
    print('\n' + '='*60)
    print(f'Running {path}...')
    sql = path.read_text(encoding='utf-8')
    try:
        rows = cur.execute(sql).fetchall()
        print(f'Returned {len(rows)} rows (showing up to 10):')
        for r in rows[:10]:
            print(dict(r))
    except Exception as e:
        print(f'Error executing {script}: {e}')

conn.close()
print('\nDone')
