import sqlite3

DB='production.db'
check_tables = [
    'SOURCE_PATIENT_DATA',
    'patients',
    'patients_backup',
    'patients_snapshot_pre_migration',
    'facilities',
    'patient_assignments',
    'user_patient_assignments',
    'dashboard_patient_assignment_summary',
    'dashboard_region_patient_assignment_summary',
    'dashboard_patient_county_map',
    'dashboard_patient_zip_map',
    'patient_region_mapping',
    'users',
    'user_roles',
    'staff_code_mapping',
    'care_plans',
    'onboarding_patients',
    'providers',
    'regions'
]

conn = sqlite3.connect(DB)
try:
    cur = conn.cursor()
    existing = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in check_tables:
        print('---')
        if t in existing:
            cols = [r[1] for r in cur.execute(f"PRAGMA table_info('{t}')").fetchall()]
            print(f"Table: {t} (columns: {len(cols)})")
            for c in cols:
                print(f"  - {c}")
        else:
            print(f"Table: {t}  -- MISSING")
    # Also show any other patient-related tables found
    print('\n---\nAll tables that contain "patient" in the name:')
    pat_tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name) LIKE '%patient%'").fetchall()]
    for t in pat_tables:
        print(f"  - {t}")
finally:
    conn.close()
