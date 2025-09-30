"""Backup existing task_billing_codes and replace with a curated set for Primary Care Visit.
Run: python scripts/backup_and_seed_task_billing_codes.py
"""
import sqlite3
from datetime import datetime
DB = 'production.db'

SEED_ROWS = [
    # service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate
    ("Primary Care Visit","Home","New Patient",70,80,"99345","Home New Patient 70-80",0),
    ("Primary Care Visit","Home","Established Patient",50,60,"99349","Home Established Patient 50-60",0),
    ("Primary Care Visit","Home","Established Patient",60,70,"99350","Home Established Patient 60-70",0),
    ("Primary Care Visit","Office","New Patient",40,50,"99204","Office New Patient 40-50",0),
    ("Primary Care Visit","Telehealth","New Patient",40,50,"99204","Telehealth New Patient 40-50",0),
    ("Primary Care Visit","Office","New Patient",60,70,"99205","Office New Patient 60-70",0),
    ("Primary Care Visit","Telehealth","New Patient",60,70,"99205","Telehealth New Patient 60-70",0),
    ("Primary Care Visit","Office","Established Patient",40,50,"99215","Office Established Patient 40-50",0),
    ("Primary Care Visit","Telehealth","Established Patient",40,50,"99215","Telehealth Established Patient 40-50",0),
    ("Primary Care Visit","Office","Established Patient",30,40,"99214","Office Established Patient 30-40",0),
    ("Primary Care Visit","Telehealth","Established Patient",30,40,"99214","Telehealth Established Patient 30-40",0),
    ("Primary Care Visit","Office","Established Patient",20,30,"99213","Office Established Patient 20-30",0),
]

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Backup existing table
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_table = f"task_billing_codes_backup_{timestamp}"
cur.execute(f"CREATE TABLE IF NOT EXISTS {backup_table} AS SELECT * FROM task_billing_codes;")
print(f"Created backup table {backup_table}")

# Clear existing rows
cur.execute("DELETE FROM task_billing_codes;")

# Insert seed rows
for row in SEED_ROWS:
    cur.execute("INSERT INTO task_billing_codes (task_description, service_type, location_type, patient_type, min_minutes, max_minutes, billing_code, description, rate, effective_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
                (f"{row[0]} - {row[2]} - {row[5]}", row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7]))

conn.commit()
conn.close()
print("Seed completed")
