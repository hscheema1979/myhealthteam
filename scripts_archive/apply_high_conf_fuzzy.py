#!/usr/bin/env python3
import sqlite3
import csv
import os

DB = 'production.db'
CSV = 'outputs/assigned_cm_fuzzy_suggestions.csv'

def read_high_conf(csv_path):
    rows = []
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            conf = (r.get('confidence') or '').strip().lower()
            assigned_cm = (r.get('assigned_cm') or '').strip()
            user_id = (r.get('user_id') or '').strip()
            if conf == 'high' and assigned_cm and user_id:
                rows.append((assigned_cm, int(user_id)))
    return rows

def main():
    if not os.path.exists(CSV):
        print(f"CSV not found: {CSV}")
        return
    mappings = read_high_conf(CSV)
    if not mappings:
        print("No high-confidence mappings found in CSV.")
        return

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # Snapshot current assignments
    cur.execute('DROP TABLE IF EXISTS patients_assigned_coordinator_snapshot_high')
    cur.execute('CREATE TABLE patients_assigned_coordinator_snapshot_high AS SELECT patient_id, assigned_coordinator_id FROM patients')
    conn.commit()

    summary = []
    for assigned_cm, user_id in mappings:
        # count potential targets (unassigned patients whose SOURCE Assigned CM matches this value)
        cur.execute('''
            SELECT COUNT(*) FROM patients p
            JOIN SOURCE_PATIENT_DATA spd ON spd."LAST FIRST DOB" = p.last_first_dob
            WHERE LOWER(TRIM(spd."Assigned CM")) = LOWER(TRIM(?))
              AND (p.assigned_coordinator_id IS NULL OR p.assigned_coordinator_id = '')
        ''', (assigned_cm,))
        potential = cur.fetchone()[0]

        # apply mapping
        cur.execute('''
            UPDATE patients
            SET assigned_coordinator_id = ?
            WHERE (assigned_coordinator_id IS NULL OR assigned_coordinator_id = '')
              AND EXISTS (
                  SELECT 1 FROM SOURCE_PATIENT_DATA spd
                  WHERE spd."LAST FIRST DOB" = patients.last_first_dob
                    AND LOWER(TRIM(spd."Assigned CM")) = LOWER(TRIM(?))
              )
        ''', (user_id, assigned_cm))
        conn.commit()

        # count how many were assigned now (compare snapshot)
        cur.execute('''
            SELECT COUNT(*) FROM patients p
            JOIN patients_assigned_coordinator_snapshot_high s ON s.patient_id = p.patient_id
            JOIN SOURCE_PATIENT_DATA spd ON spd."LAST FIRST DOB" = p.last_first_dob
            WHERE LOWER(TRIM(spd."Assigned CM")) = LOWER(TRIM(?))
              AND (s.assigned_coordinator_id IS NULL OR s.assigned_coordinator_id = '')
              AND p.assigned_coordinator_id = ?
        ''', (assigned_cm, user_id))
        assigned_now = cur.fetchone()[0]

        summary.append((assigned_cm, user_id, potential, assigned_now))

    # Report
    total_assigned = sum(r[3] for r in summary)
    print(f"applied_mappings={len(summary)}, total_assigned={total_assigned}")
    for assigned_cm, user_id, potential, assigned_now in summary:
        print(f"{assigned_cm!r}: user_id={user_id}, potential_targets={potential}, assigned_now={assigned_now}")

    conn.close()

if __name__ == '__main__':
    main()
