import sqlite3

def check_zen():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Get all provider task tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'provider_tasks_20%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        print(f"\nChecking table: {table}")
        try:
            # Check for 'ZEN' in notes or status
            cursor.execute(f"SELECT notes, status, COUNT(*) FROM {table} WHERE notes LIKE '%ZEN%' OR status LIKE '%ZEN%' GROUP BY notes, status")
            results = cursor.fetchall()
            if results:
                for notes, status, count in results:
                    print(f"  Notes: {notes} | Status: {status} | Count: {count}")
            else:
                print("  No Zen-related records found.")
        except Exception as e:
            print(f"  Error checking table {table}: {e}")
            
    conn.close()

if __name__ == "__main__":
    check_zen()
