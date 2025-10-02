import sqlite3

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Check patients table if it exists
if 'patients' in tables:
    cursor.execute("PRAGMA table_info(patients)")
    columns = cursor.fetchall()
    print("Patients table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
else:
    print("No patients table found")

conn.close()