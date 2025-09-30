import sqlite3
import os

def count_patients(db_path):
    if not os.path.exists(db_path):
        print(f"{db_path} does not exist.")
        return
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute("SELECT COUNT(*) FROM patients")
        count = cur.fetchone()[0]
        print(f"{db_path}: {count} patients")
    except Exception as e:
        print(f"{db_path}: ERROR: {e}")
    finally:
        conn.close()

count_patients('production.db')
count_patients('test_transfer.db')
