import sqlite3

DB='production.db'
conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
cur=conn.cursor()

print('patients_count=', cur.execute('SELECT COUNT(*) FROM patients').fetchone()[0])
print('facilities_count=', cur.execute('SELECT COUNT(*) FROM facilities').fetchone()[0])
print('patients_with_facility_field_set=', cur.execute("SELECT COUNT(*) FROM patients WHERE current_facility_id IS NOT NULL AND current_facility_id != ''").fetchone()[0])
print('patients_with_no_matching_facility=', cur.execute("SELECT COUNT(*) FROM patients p LEFT JOIN facilities f ON p.current_facility_id = f.facility_id WHERE (p.current_facility_id IS NOT NULL AND p.current_facility_id != '') AND f.facility_id IS NULL").fetchone()[0])

print('\nSample unmatched (patients with facility_id but no matching facility):')
rows=cur.execute("SELECT p.patient_id, p.first_name, p.last_name, p.current_facility_id FROM patients p LEFT JOIN facilities f ON p.current_facility_id = f.facility_id WHERE (p.current_facility_id IS NOT NULL AND p.current_facility_id != '') AND f.facility_id IS NULL LIMIT 20").fetchall()
for r in rows:
    print(dict(r))

print('\nSample facilities:')
for r in cur.execute('SELECT facility_id, facility_name FROM facilities LIMIT 50'):
    print(dict(r))

print('\nDistinct current_facility_id sample:')
for r in cur.execute('SELECT DISTINCT current_facility_id FROM patients LIMIT 50'):
    print(repr(r[0]))

conn.close()
