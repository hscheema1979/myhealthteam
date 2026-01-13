"""
Populate task_billing_codes table with the approved limited billing code set.

This script sets up the billing codes table with:
- 11 ENABLED codes for active use
- 3 DISABLED codes (marked as "do not use this for now")

Matrix: 3 Locations (Home, Telehealth, Office) × Patient Types (New, Follow Up, Acute, TCM, Cognitive)
"""

import sqlite3
import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

DB_PATH = os.path.join(project_root, 'production.db')

def get_connection():
    return sqlite3.connect(DB_PATH)

def setup_billing_codes_table(conn):
    """Ensure table has the required columns for is_active tracking."""
    cursor = conn.cursor()
    
    # Check if is_active column exists
    cursor.execute("PRAGMA table_info(task_billing_codes)")
    columns = {col[1] for col in cursor.fetchall()}
    
    if 'is_active' not in columns:
        cursor.execute("ALTER TABLE task_billing_codes ADD COLUMN is_active INTEGER DEFAULT 1")
        print("  Added is_active column")
    
    if 'note' not in columns:
        cursor.execute("ALTER TABLE task_billing_codes ADD COLUMN note TEXT")
        print("  Added note column")
    
    conn.commit()

def populate_billing_codes(conn):
    """Populate the task_billing_codes table with all approved codes."""
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM task_billing_codes")
    print("  Cleared existing billing codes")
    
    today = '2026-01-01'
    
    # ENABLED CODES (is_active = 1) - 11 codes
    enabled_codes = [
        # Home visits
        ('NEW HOME VISIT', 'New', 'Home', 'New', '99345', 
         'New patient home visit - 75 min', today),
        ('FOLLOW UP HOME VISIT', 'Follow Up', 'Home', 'Follow Up', '99350', 
         'Established patient home visit - 60 min', today),
        
        # Telehealth visits
        ('NEW TELEVISIT VISIT', 'New', 'Telehealth', 'New', '99204', 
         'New patient telehealth visit - 45 min', today),
        ('FOLLOW UP TELE VISIT', 'Follow Up', 'Telehealth', 'Follow Up', '99214', 
         'Established patient telehealth visit - 30 min', today),
        ('ACUTE TELE VISIT', 'Acute', 'Telehealth', 'Acute', '99213', 
         'Acute telehealth visit - 15 min', today),
        
        # Office visits
        ('NEW OFFICE VISIT', 'New', 'Office', 'New', '99204', 
         'New patient office visit - 45 min', today),
        ('FOLLOW UP OFFICE VISIT', 'Follow Up', 'Office', 'Follow Up', '99214', 
         'Established patient office visit - 30 min', today),
        ('ACUTE OFFICE VISIT', 'Acute', 'Office', 'Acute', '99213', 
         'Acute office visit - 15 min', today),
        
        # TCM and Cognitive (Office only)
        ('TCM-7d', 'TCM-7', 'Office', 'TCM', '99496', 
         'Transitional Care Management 7-day', today),
        ('TCM-14d', 'TCM-14', 'Office', 'TCM', '99495', 
         'Transitional Care Management 14-day', today),
        ('Cog A+B', 'Cognitive', 'Office', 'Cognitive', '96138+96132', 
         'Cognitive assessment and testing', today),
    ]
    
    cursor.executemany("""
        INSERT INTO task_billing_codes 
        (task_description, service_type, location_type, patient_type, 
         billing_code, description, effective_date, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    """, enabled_codes)
    
    print(f"  Inserted {len(enabled_codes)} enabled codes")
    
    # DISABLED CODES (is_active = 0) - 3 codes
    disabled_codes = [
        ('FOLLOW UP HOME VISIT', 'Follow Up', 'Home', 'Follow Up', '99349', 
         'Established patient home visit - 40 min', today, 
         0, 'do not use this for now'),
        ('NEW OFFICE VISIT', 'New', 'Office', 'New', '99205', 
         'New patient office visit - 60 min', today, 
         0, 'do not use this for now'),
        ('FOLLOW UP OFFICE VISIT', 'Follow Up', 'Office', 'Follow Up', '99215', 
         'Established patient office visit - 45 min', today, 
         0, 'do not use this for now'),
    ]
    
    cursor.executemany("""
        INSERT INTO task_billing_codes 
        (task_description, service_type, location_type, patient_type, 
         billing_code, description, effective_date, is_active, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, disabled_codes)
    
    print(f"  Inserted {len(disabled_codes)} disabled codes")
    
    conn.commit()
    
    # Report
    cursor.execute("SELECT COUNT(*) FROM task_billing_codes")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM task_billing_codes WHERE is_active = 1")
    active = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM task_billing_codes WHERE is_active = 0")
    disabled = cursor.fetchone()[0]
    
    print(f"\n✓ Billing codes population complete!")
    print(f"  Total codes: {total}")
    print(f"  Active codes: {active}")
    print(f"  Disabled codes: {disabled}")
    
    # Breakdown by location
    print(f"\n  Breakdown by Location:")
    cursor.execute("""
        SELECT location_type, COUNT(*) as count 
        FROM task_billing_codes 
        WHERE is_active = 1
        GROUP BY location_type 
        ORDER BY location_type
    """)
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]} codes")
    
    return total

def main():
    print("=" * 60)
    print("Billing Codes Population Script")
    print("=" * 60)
    
    conn = get_connection()
    
    try:
        setup_billing_codes_table(conn)
        populate_billing_codes(conn)
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
