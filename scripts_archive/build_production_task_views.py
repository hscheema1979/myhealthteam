#!/usr/bin/env python3
import sqlite3
import os

DB = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'production.db'))
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'outputs', 'generated_production_task_views.sql'))

def get_tables(cur, prefix):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (prefix + '%',))
    return [r[0] for r in cur.fetchall()]

def get_cols(cur, table):
    cur.execute(f"PRAGMA table_info({table})")
    return {row[1].lower() for row in cur.fetchall()}

def normalize_expr(col):
    base = f"TRIM(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(TRIM(REPLACE({col}, ',', ' ')), 'ZEN-', ''), 'PM-', ''), 'ZMN-', ''), 'BlessedCare-', ''), 'BLESSEDCARE-', ''), 'BleessedCare-', ''), 'BLEESSEDCARE-', ''), '3PR-', ''), '3PR -', ''))"
    return base

def provider_select(table, cols):
    # patient_id
    pid_col = None
    for c in ['patient_id','patient_name_raw','patient_name','patient']:
        if c in cols:
            pid_col = c
            break
    if pid_col is None:
        return None
    # activity_date
    date_col = None
    for c in ['activity_date','task_date','dos','date']:
        if c in cols:
            date_col = c
            break
    if date_col is None:
        return None
    # service
    service_expr = 'COALESCE(service, billing_code, notes, "")'
    if 'service' in cols:
        service_expr = 'service'
    elif 'billing_code' in cols:
        service_expr = 'billing_code'
    elif 'notes' in cols:
        service_expr = 'notes'
    # provider code/id
    prov_expr = 'UPPER(TRIM(provider_code))' if 'provider_code' in cols else 'UPPER(TRIM(CAST(provider_id AS TEXT)))' if 'provider_id' in cols else "''"
    return (
        f"SELECT {normalize_expr(pid_col)} AS patient_id, "
        f"{date_col} AS activity_date, "
        f"{prov_expr} AS provider_code_norm, "
        f"{service_expr} AS service FROM {table} WHERE {date_col} IS NOT NULL"
    )

def coordinator_select(table, cols):
    # patient_id
    pid_col = None
    for c in ['patient_id','pt_name','patient']:
        if c in cols:
            pid_col = c
            break
    if pid_col is None:
        return None
    # activity_date
    date_col = None
    for c in ['activity_date','task_date','date_only','date']:
        if c in cols:
            date_col = c
            break
    if date_col is None:
        return None
    # staff code
    staff_col = 'staff_code' if 'staff_code' in cols else (
        'coordinator_id' if 'coordinator_id' in cols else 'staff')
    # task type
    task_expr = 'task_type' if 'task_type' in cols else (
        'service' if 'service' in cols else 'notes' if 'notes' in cols else "''")
    return (
        f"SELECT {normalize_expr(pid_col)} AS patient_id, "
        f"{date_col} AS activity_date, "
        f"UPPER(TRIM({staff_col})) AS staff_code_norm, "
        f"TRIM({task_expr}) AS task_type FROM {table} WHERE {date_col} IS NOT NULL"
    )

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    prov_tables = get_tables(cur, 'provider_tasks_')
    coord_tables = get_tables(cur, 'coordinator_tasks_')

    prov_selects = []
    for t in prov_tables:
        cols = get_cols(cur, t)
        sel = provider_select(t, cols)
        if sel:
            prov_selects.append(sel)
    coord_selects = []
    for t in coord_tables:
        cols = get_cols(cur, t)
        sel = coordinator_select(t, cols)
        if sel:
            coord_selects.append(sel)

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write("CREATE VIEW IF NOT EXISTS P_PROVIDER_TASKS_EQUIV AS\n")
        if prov_selects:
            f.write("\nUNION ALL\n".join(prov_selects) + ";\n\n")
        else:
            f.write("SELECT '' AS patient_id, NULL AS activity_date, '' AS provider_code_norm, '' AS service WHERE 0;\n\n")
        f.write("CREATE VIEW IF NOT EXISTS P_COORDINATOR_TASKS_EQUIV AS\n")
        if coord_selects:
            f.write("\nUNION ALL\n".join(coord_selects) + ";\n")
        else:
            f.write("SELECT '' AS patient_id, NULL AS activity_date, '' AS staff_code_norm, '' AS task_type WHERE 0;\n")
    conn.close()

if __name__ == '__main__':
    main()