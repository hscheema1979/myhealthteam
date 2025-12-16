#!/usr/bin/env python3
import sqlite3
import os
import csv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB = os.path.join(ROOT, 'production.db')
OUT_DIR = os.path.join(os.path.dirname(__file__), 'outputs', 'reports')
PROV_OUT = os.path.join(OUT_DIR, 'provider_code_candidates.csv')
COORD_OUT = os.path.join(OUT_DIR, 'coordinator_code_candidates.csv')

def ensure_dirs():
    os.makedirs(OUT_DIR, exist_ok=True)

def write_csv(path, headers, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)

def main():
    ensure_dirs()
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    # Provider code norms from staging
    cur.execute("""
        SELECT UPPER(TRIM(provider_code)) AS provider_code_norm, COUNT(*) AS cnt
        FROM staging_provider_tasks
        WHERE provider_code IS NOT NULL AND TRIM(provider_code) <> ''
        GROUP BY UPPER(TRIM(provider_code))
        ORDER BY cnt DESC, provider_code_norm ASC
    """)
    prov_rows = cur.fetchall()
    # Coordinator staff code norms from staging (strip trailing .0)
    cur.execute("""
        SELECT UPPER(TRIM(REPLACE(CAST(staff_code AS TEXT), '.0', ''))) AS staff_code_norm, COUNT(*) AS cnt
        FROM staging_coordinator_tasks
        WHERE staff_code IS NOT NULL AND TRIM(CAST(staff_code AS TEXT)) <> ''
        GROUP BY UPPER(TRIM(REPLACE(CAST(staff_code AS TEXT), '.0', '')))
        ORDER BY cnt DESC, staff_code_norm ASC
    """)
    coord_rows = cur.fetchall()
    # Write candidates
    write_csv(PROV_OUT, ['provider_code_norm','count','candidate_user_id'], [(r[0], r[1], '') for r in prov_rows])
    write_csv(COORD_OUT, ['staff_code_norm','count','candidate_user_id'], [(r[0], r[1], '') for r in coord_rows])
    conn.close()

if __name__ == '__main__':
    main()