import sqlite3
DB_PATH = r'D:\Git\myhealthteam2\Streamlit\production.db'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
name_variants = [
    ('BIANCHI','SANCHEZ'),
    ('SANCHEZ','BIANCHI'),
]
results = []
for first,last in name_variants:
    rows = cur.execute(
        """
        SELECT onboarding_id, first_name, last_name, patient_id, patient_status,
               stage1_complete, stage2_complete, stage3_complete, stage4_complete, stage5_complete,
               completed_date, updated_date
        FROM onboarding_patients
        WHERE UPPER(first_name)=? AND UPPER(last_name)=?
        ORDER BY updated_date DESC
        """,
        (first,last)
    ).fetchall()
    results.extend(rows)
rows_like = cur.execute(
    """
    SELECT onboarding_id, first_name, last_name, patient_id, patient_status,
           stage1_complete, stage2_complete, stage3_complete, stage4_complete, stage5_complete,
           completed_date, updated_date
    FROM onboarding_patients
    WHERE UPPER(first_name||' '||last_name) LIKE ?
    ORDER BY updated_date DESC
    """,
    ('%BIANCHI%SANCHEZ%',)
).fetchall()
results.extend(rows_like)
# Deduplicate
seen = set()
final = []
for r in results:
    if r['onboarding_id'] not in seen:
        seen.add(r['onboarding_id'])
        final.append(r)
print('FOUND', len(final), 'records for name variants:')
for r in final:
    print({
        'onboarding_id': r['onboarding_id'],
        'name': f"{r['first_name']} {r['last_name']}",
        'patient_id': r['patient_id'],
        'patient_status': r['patient_status'],
        'stage1_complete': r['stage1_complete'],
        'stage2_complete': r['stage2_complete'],
        'stage3_complete': r['stage3_complete'],
        'stage4_complete': r['stage4_complete'],
        'stage5_complete': r['stage5_complete'],
        'completed_date': r['completed_date'],
        'updated_date': r['updated_date'],
    })
conn.close()