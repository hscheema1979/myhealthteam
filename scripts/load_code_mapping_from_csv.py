#!/usr/bin/env python3
import sqlite3
import os
import csv

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB = os.path.join(ROOT, 'production.db')
REPORT_DIR = os.path.join(os.path.dirname(__file__), 'outputs', 'reports')
PROV_CSV = os.path.join(REPORT_DIR, 'provider_code_candidates.csv')
COORD_CSV = os.path.join(REPORT_DIR, 'coordinator_code_candidates.csv')

def load_provider(cur):
    if not os.path.exists(PROV_CSV):
        return 0
    updated = 0
    with open(PROV_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            code = (r.get('provider_code_norm') or '').strip().upper()
            uid = (r.get('candidate_user_id') or '').strip()
            if not code or not uid or not uid.isdigit():
                continue
            cur.execute('INSERT INTO provider_code_map(provider_code_norm, user_id) VALUES(?, ?) ON CONFLICT(provider_code_norm) DO UPDATE SET user_id=excluded.user_id', (code, int(uid)))
            updated += 1
    return updated

def load_coordinator(cur):
    if not os.path.exists(COORD_CSV):
        return 0
    updated = 0
    with open(COORD_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            code = (r.get('staff_code_norm') or '').strip().upper()
            uid = (r.get('candidate_user_id') or '').strip()
            if not code or not uid or not uid.isdigit():
                continue
            cur.execute('INSERT INTO coordinator_code_map(staff_code_norm, user_id) VALUES(?, ?) ON CONFLICT(staff_code_norm) DO UPDATE SET user_id=excluded.user_id', (code, int(uid)))
            updated += 1
    return updated

def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('PRAGMA foreign_keys = OFF')
    prov = load_provider(cur)
    coord = load_coordinator(cur)
    conn.commit()
    conn.close()
    print(f'provider_updates={prov} coordinator_updates={coord}')

if __name__ == '__main__':
    main()