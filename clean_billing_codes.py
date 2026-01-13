import sqlite3
import re

conn = sqlite3.connect('data/production.db')
cursor = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_%' ORDER BY name DESC"
)
tables = [row[0] for row in cursor.fetchall()]

print(f"Found {len(tables)} provider_tasks tables")

for table in tables:
    print(f"\nProcessing {table}...")
    
    cursor = conn.execute(f"SELECT provider_task_id, task_description FROM {table}")
    rows = cursor.fetchall()
    
    updates = 0
    for task_id, desc in rows:
        if desc:
            clean_desc = re.sub(r'\s*-\s*\d{5}\s*$', '', desc).strip()
            if clean_desc != desc:
                conn.execute(
                    f"UPDATE {table} SET task_description = ? WHERE provider_task_id = ?",
                    (clean_desc, task_id)
                )
                updates += 1
    
    print(f"  Updated {updates} records in {table}")

conn.commit()
conn.close()
print("\nDone!")
