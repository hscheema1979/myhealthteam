#!/usr/bin/env python3

import sqlite3

def check_september_november_names():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    print("CHECKING SEPTEMBER AND NOVEMBER NAME FORMATS")
    print("=" * 60)
    
    # Check September coordinator tasks
    print("\nSEPTEMBER 2025 COORDINATOR TASKS:")
    cursor.execute('SELECT DISTINCT coordinator_id FROM coordinator_tasks_2025_09 ORDER BY coordinator_id')
    sept_coordinators = cursor.fetchall()
    print(f"Found {len(sept_coordinators)} unique coordinator IDs:")
    for row in sept_coordinators:
        coordinator_id = row[0]
        cursor.execute('SELECT COUNT(*) FROM coordinator_tasks_2025_09 WHERE coordinator_id = ?', (coordinator_id,))
        task_count = cursor.fetchone()[0]
        print(f"  - {coordinator_id}: {task_count} tasks")
    
    # Check November coordinator tasks  
    print("\nNOVEMBER 2025 COORDINATOR TASKS:")
    cursor.execute('SELECT DISTINCT coordinator_id FROM coordinator_tasks_2025_11 ORDER BY coordinator_id')
    nov_coordinators = cursor.fetchall()
    print(f"Found {len(nov_coordinators)} unique coordinator IDs:")
    for row in nov_coordinators:
        coordinator_id = row[0]
        cursor.execute('SELECT COUNT(*) FROM coordinator_tasks_2025_11 WHERE coordinator_id = ?', (coordinator_id,))
        task_count = cursor.fetchone()[0]
        print(f"  - {coordinator_id}: {task_count} tasks")
    
    # Check if numeric IDs correspond to user_ids in users table
    print("\nCHECKING IF NUMERIC IDs ARE USER_IDs:")
    numeric_ids = []
    for row in sept_coordinators:
        if str(row[0]).isdigit():
            numeric_ids.append(row[0])
    
    for row in nov_coordinators:
        if str(row[0]).isdigit():
            numeric_ids.append(row[0])
    
    numeric_ids = list(set(numeric_ids))  # Remove duplicates
    
    if numeric_ids:
        print(f"Found {len(numeric_ids)} unique numeric IDs: {numeric_ids}")
        
        # Check if they exist in users table
        for user_id in numeric_ids:
            cursor.execute('SELECT full_name FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                print(f"  User ID {user_id} -> {result[0]}")
            else:
                print(f"  User ID {user_id} -> NOT FOUND in users table")
    else:
        print("No numeric IDs found!")
    
    conn.close()

if __name__ == "__main__":
    check_september_november_names()