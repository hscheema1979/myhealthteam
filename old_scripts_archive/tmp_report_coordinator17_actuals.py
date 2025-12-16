import sqlite3, json, sys
from collections import defaultdict, Counter

DB_PATH = 'production.db'
TARGET_COORDINATOR_ID = 17  # numeric user_id


def get_tables(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND (
            name LIKE 'coordinator_tasks%'
            OR name='coordinator_tasks'
            OR name='coordinator_tasks_archive'
        )
        ORDER BY name
    """)
    return [r[0] for r in cur.fetchall()]


def load_patients_assigned_to(conn, coordinator_user_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT patient_id, last_name, first_name, date_of_birth
        FROM patients
        WHERE assigned_coordinator_id = ?
    """, (coordinator_user_id,))
    rows = cur.fetchall()
    patients = [
        {
            'patient_id': r[0],
            'last_name': r[1],
            'first_name': r[2],
            'date_of_birth': r[3]
        }
        for r in rows
    ]
    return patients


def build_user_name_map(conn):
    cur = conn.cursor()
    cur.execute("SELECT user_id, COALESCE(full_name, username) FROM users")
    return {str(r[0]): r[1] for r in cur.fetchall()}


def build_staff_code_to_user_map(conn):
    cur = conn.cursor()
    # Staff mapping might only have staff_code + user_id in production
    cur.execute("PRAGMA table_info(staff_code_mapping)")
    cols = {r[1] for r in cur.fetchall()}
    if not {'staff_code', 'user_id'}.issubset(cols):
        return {}, {}
    cur.execute("SELECT TRIM(UPPER(staff_code)), CAST(user_id AS TEXT) FROM staff_code_mapping")
    code_to_user = {}
    for code, uid in cur.fetchall():
        code_to_user[code] = uid
    # No staff_name column present; return empty dict for optional fallback
    return code_to_user, {}


def resolve_name(coordinator_id_value, user_name_map, code_to_user_map, code_to_staff_name):
    # coordinator_id_value may be numeric string (user_id) or staff_code like 'ChaZu000'
    if coordinator_id_value is None:
        return None
    cid = str(coordinator_id_value).strip()
    # Try direct user_id
    if cid.isdigit() and cid in user_name_map:
        return user_name_map[cid]
    # Try staff_code -> user_id -> user name
    code_key = cid.upper()
    uid = code_to_user_map.get(code_key)
    if uid and uid in user_name_map:
        return user_name_map[uid]
    # Fallback: if coordinator_name was present in row, caller will use it; if not, None
    return None


def collect_task_coordinators_for_patients(conn, tables, patient_ids):
    user_name_map = build_user_name_map(conn)
    code_to_user_map, code_to_staff_name = build_staff_code_to_user_map(conn)

    per_patient = defaultdict(lambda: Counter())
    overall = Counter()
    unmapped_examples = defaultdict(set)

    cur = conn.cursor()
    pid_tuple = tuple(patient_ids)
    if not pid_tuple:
        return {'overall': overall, 'per_patient': per_patient, 'unmapped_examples': {}, 'tables_scanned': tables}
    for tbl in tables:
        # Identify columns present for robustness
        cur.execute(f"PRAGMA table_info({tbl})")
        cols = [r[1] for r in cur.fetchall()]
        has_patient_id = 'patient_id' in cols
        # Coordinator id may be 'coordinator_id' or 'staff_code' depending on transformation
        id_col = 'coordinator_id' if 'coordinator_id' in cols else ('staff_code' if 'staff_code' in cols else None)
        name_col = 'coordinator_name' if 'coordinator_name' in cols else None
        if not has_patient_id or not id_col:
            continue
        # Query tasks for our patients
        placeholders = ','.join(['?'] * len(pid_tuple))
        q = f"SELECT patient_id, {id_col} AS coord_id" + (f", {name_col} AS coord_name" if name_col else "") + f" FROM {tbl} WHERE patient_id IN ({placeholders})"
        cur.execute(q, pid_tuple)
        for r in cur.fetchall():
            pid = r[0]
            coord_id_val = r[1]
            coord_name_val = r[2] if name_col else None
            # Resolve name defensively
            resolved = resolve_name(coord_id_val, user_name_map, code_to_user_map, code_to_staff_name) or coord_name_val
            key = None
            if resolved:
                key = resolved
            else:
                # record unmapped
                unmapped_examples[str(coord_id_val)].add(tbl)
                key = f"Unknown ({coord_id_val})"
            per_patient[str(pid)][key] += 1
            overall[key] += 1

    # Convert sets to sorted lists for JSON
    unmapped_examples = {k: sorted(list(v)) for k, v in unmapped_examples.items()}
    return {'overall': overall, 'per_patient': per_patient, 'unmapped_examples': unmapped_examples}


def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        patients = load_patients_assigned_to(conn, TARGET_COORDINATOR_ID)
        patient_ids = [p['patient_id'] for p in patients]
        tables = get_tables(conn)
        data = collect_task_coordinators_for_patients(conn, tables, patient_ids)
        # Format counters nicely
        overall = [{'coordinator': k, 'task_count': int(v)} for k, v in sorted(data['overall'].items(), key=lambda x: (-x[1], x[0]))]
        per_patient = []
        for p in patients:
            pid = str(p['patient_id'])
            counts = data['per_patient'].get(pid, Counter())
            per_patient.append({
                'patient_id': p['patient_id'],
                'patient_name': f"{p['last_name']}, {p['first_name']}",
                'date_of_birth': p['date_of_birth'],
                'coordinator_task_counts': [{'coordinator': k, 'task_count': int(v)} for k, v in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
            })
        result = {
            'input': {
                'assigned_coordinator_user_id': TARGET_COORDINATOR_ID,
                'patient_count': len(patients),
            },
            'overall_coordinators_for_tasks_on_these_patients': overall,
            'per_patient_breakdown': per_patient,
            'unmapped_coordinator_id_examples': data['unmapped_examples'],
            'tables_scanned': tables,
        }
        print(json.dumps(result, indent=2))
    finally:
        conn.close()

if __name__ == '__main__':
    main()