#!/usr/bin/env python3
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / 'production.db'

def print_rows(rows, cols):
    print('|'.join(cols))
    for r in rows:
        print('|'.join([str(r[c]) if r[c] is not None else '' for c in cols]))

def main():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Find coordinator_id for user_id=8
    cur.execute('SELECT coordinator_id, user_id, first_name, last_name, email FROM coordinators WHERE user_id = ?', (8,))
    coord = cur.fetchone()
    if coord:
        print('=== COORDINATOR ===')
        print(f"coordinator_id={coord['coordinator_id']}|user_id={coord['user_id']}|name={coord['first_name']} {coord['last_name']}|email={coord['email']}")
        coordinator_id = coord['coordinator_id']
    else:
        print('No coordinator found for user_id=8')
        return

    # List active workflow_instances for that coordinator
    cols = ['instance_id','template_name','patient_id','patient_name','coordinator_id','coordinator_name','current_step','workflow_status']
    cur.execute('SELECT ' + ','.join(cols) + ' FROM workflow_instances WHERE coordinator_id = ? AND workflow_status = ? ORDER BY created_at DESC', (coordinator_id, 'Active'))
    rows = cur.fetchall()
    print('\n=== ACTIVE WORKFLOW_INSTANCES ===')
    if rows:
        print_rows(rows, cols)
    else:
        print('No active workflow instances found for this coordinator')

    # Show any coordinator_tasks that start workflows for this coordinator
    print('\n=== COORDINATOR TASKS (WORKFLOW_START) ===')
    cur.execute("SELECT coordinator_task_id, coordinator_id, patient_id, task_date, task_type, duration_minutes, notes FROM coordinator_tasks WHERE coordinator_id = ? AND task_type LIKE 'WORKFLOW_START|%'", (coordinator_id,))
    tasks = cur.fetchall()
    if tasks:
        print_rows(tasks, ['coordinator_task_id','coordinator_id','patient_id','task_date','task_type','duration_minutes','notes'])
    else:
        print('No WORKFLOW_START coordinator_tasks for this coordinator')

    # Active workflows missing a WORKFLOW_START task
    print('\n=== ACTIVE WORKFLOWS MISSING WORKFLOW_START ===')
    cur.execute("SELECT wi.instance_id, wi.template_name, wi.patient_name FROM workflow_instances wi WHERE wi.workflow_status = 'Active' AND wi.coordinator_id = ? AND NOT EXISTS (SELECT 1 FROM coordinator_tasks ct WHERE ct.task_type = 'WORKFLOW_START|' || wi.instance_id)", (coordinator_id,))
    missing = cur.fetchall()
    if missing:
        for m in missing:
            print(m['instance_id'], m['template_name'], m['patient_name'])
    else:
        print('None')

    conn.close()

if __name__ == '__main__':
    main()
