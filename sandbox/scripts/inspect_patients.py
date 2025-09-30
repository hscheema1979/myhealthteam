import sqlite3, os
DB='production.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()
print('Using DB:', os.path.abspath(DB))
rows = cur.execute("PRAGMA table_info('patients')").fetchall()
for r in rows:
    print(r)
conn.close()
