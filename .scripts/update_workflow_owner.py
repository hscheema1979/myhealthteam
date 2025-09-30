import sqlite3
import os
import sys
import json
import shutil
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), '..', 'production.db')
DB = os.path.abspath(DB)

def get_matches(conn):
    cur = conn.execute("SELECT step_id, template_id, step_order, task_name, owner FROM workflow_steps WHERE task_name LIKE '%CP Reviews results%' OR task_name LIKE '%CP Reviews result%' OR task_name = 'CP Reviews results' OR task_name LIKE '%CP Reviews%'")
    return [dict(row) for row in cur.fetchall()]

def backup_db(db_path):
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backups_dir = os.path.join(os.path.dirname(db_path), 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    dest = os.path.join(backups_dir, f'production_backup_{ts}.db')
    shutil.copy2(db_path, dest)
    return dest

if __name__ == '__main__':
    apply_changes = '--apply' in sys.argv
    print('DB path:', DB)
    if not os.path.exists(DB):
        print('ERROR: DB not found at', DB)
        sys.exit(1)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    try:
        matches = get_matches(conn)
        print('Found matches:')
        print(json.dumps(matches, indent=2))
        if not matches:
            print('No matching steps found. Exiting.')
            sys.exit(0)
        if apply_changes:
            backup = backup_db(DB)
            print('Backup created at', backup)
            cur = conn.execute("UPDATE workflow_steps SET owner = 'CM' WHERE task_name LIKE '%CP Reviews results%' OR task_name LIKE '%CP Reviews result%' OR task_name = 'CP Reviews results' OR task_name LIKE '%CP Reviews%'")
            conn.commit()
            print('Rows updated:', conn.total_changes)
            matches_after = get_matches(conn)
            print('Remaining matches after update (should be 0):')
            print(json.dumps(matches_after, indent=2))
        else:
            print('\nRun with --apply to perform the update and create a DB backup.')
    finally:
        conn.close()
