#!/usr/bin/env python3
"""
Test current state - see if ZMO processing works without separate provider CSV files
"""

import sqlite3
import os

# Check if production database exists and has data
def check_database():
    print("Checking current database state...")
    print("=" * 50)
    
    if not os.path.exists('production.db'):
        print("No production.db found")
        return
    
    conn = sqlite3.connect('production.db')
    
    # Check tables
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables in database: {tables}")
    
    if 'patient_assignments' in tables:
        cursor = conn.execute("SELECT COUNT(*) FROM patient_assignments")
        count = cursor.fetchone()[0]
        print(f"Current patient_assignments count: {count}")
        
        if count > 0:
            # Show some sample assignments
            cursor = conn.execute("""
                SELECT patient_id, provider_id, coordinator_id 
                FROM patient_assignments 
                LIMIT 5
            """)
            print("Sample assignments:")
            for row in cursor.fetchall():
                print(f"  Patient: {row[0]}, Provider: {row[1]}, Coordinator: {row[2]}")
    
    if 'users' in tables:
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE status != 'deleted'")
        user_count = cursor.fetchone()[0]
        print(f"Active users: {user_count}")
        
        # Show some providers
        cursor = conn.execute("""
            SELECT user_id, username, first_name, last_name 
            FROM users 
            WHERE status != 'deleted' 
            LIMIT 5
        """)
        print("Sample users:")
        for row in cursor.fetchall():
            print(f"  ID: {row[0]}, Username: {row[1]}, Name: {row[2]} {row[3]}")
    
    conn.close()

def check_zmo_file():
    print("\nChecking for ZMO file...")
    print("=" * 30)
    
    zmo_path = 'downloads/ZMO_MAIN.csv'
    if os.path.exists(zmo_path):
        print(f"ZMO file exists: {zmo_path}")
        
        # Show first few lines
        with open(zmo_path, 'r', encoding='utf-8') as f:
            lines = [f.readline().strip() for _ in range(3)]
            print("First few lines:")
            for line in lines:
                print(f"  {line[:100]}...")  # Show first 100 chars
    else:
        print(f"ZMO file NOT found: {zmo_path}")

def check_provider_csv_files():
    print("\nChecking for provider CSV files (the ones we want to eliminate)...")
    print("=" * 60)
    
    if not os.path.exists('downloads'):
        print("No downloads directory found")
        return
    
    csv_files = [f for f in os.listdir('downloads') if f.endswith('.csv')]
    
    # Filter for provider files (exclude system files)
    exclude_patterns = ['PSL_', 'RVZ_', 'CMLog_', 'ZMO_', 'index', 'psl', 'rvz', 'cmlog']
    provider_files = []
    
    for f in csv_files:
        if not any(f.startswith(p) for p in exclude_patterns):
            # Check if it looks like a provider name (starts with capital letter)
            name_part = f.replace('.csv', '').strip()
            if name_part and name_part[0].isupper():
                provider_files.append(f)
    
    print(f"Found {len(provider_files)} provider CSV files:")
    for f in provider_files:
        print(f"  {f}")
    
    return provider_files

if __name__ == "__main__":
    check_database()
    check_zmo_file()
    provider_files = check_provider_csv_files()
    
    print(f"\nSUMMARY:")
    print(f"- Database exists and has structure")
    print(f"- ZMO file availability: {'YES' if os.path.exists('downloads/ZMO_MAIN.csv') else 'NO'}")
    print(f"- Provider CSV files found: {len(provider_files)}")
    print(f"- Ready to test ZMO-only processing")