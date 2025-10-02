#!/usr/bin/env python3
"""
Migrate billing information from notes to billing_notes column
"""

import sqlite3
import re
from datetime import datetime

def main():
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # First, let's see what we're working with
    print("Analyzing billing information in notes...")
    
    # Find all records with billing information in notes but empty billing_notes
    query = '''
    SELECT 
        provider_task_id,
        notes,
        billing_notes,
        billing_status,
        is_paid
    FROM provider_tasks 
    WHERE (notes LIKE '%paid by zen%' OR notes LIKE '%billing%' OR notes LIKE '%paid%')
    AND (billing_notes IS NULL OR billing_notes = '')
    '''
    
    cursor.execute(query)
    records = cursor.fetchall()
    
    print(f"Found {len(records)} records with billing info in notes but empty billing_notes")
    
    if len(records) == 0:
        print("No records to migrate.")
        conn.close()
        return
    
    # Show first few examples
    print("\nFirst 5 examples:")
    for i, record in enumerate(records[:5]):
        task_id, notes, billing_notes, billing_status, is_paid = record
        print(f"Task {task_id}: '{notes}' -> billing_notes: {billing_notes}")
    
    # Ask for confirmation
    response = input(f"\nDo you want to migrate billing information for {len(records)} records? (y/N): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        conn.close()
        return
    
    # Perform the migration
    updated_count = 0
    
    for record in records:
        task_id, notes, billing_notes, billing_status, is_paid = record
        
        # Extract billing information from notes
        billing_info = extract_billing_info(notes)
        
        if billing_info:
            # Update billing_notes with the extracted information
            update_query = '''
            UPDATE provider_tasks 
            SET billing_notes = ?,
                updated_date = CURRENT_TIMESTAMP
            WHERE provider_task_id = ?
            '''
            
            cursor.execute(update_query, (billing_info, task_id))
            updated_count += 1
            
            # Also update billing status if it contains "paid by zen"
            if "paid by zen" in notes.lower():
                # Update billing status and is_paid flag
                status_update_query = '''
                UPDATE provider_tasks 
                SET billing_status = 'Paid',
                    is_paid = 1,
                    paid_date = CURRENT_TIMESTAMP,
                    updated_date = CURRENT_TIMESTAMP
                WHERE provider_task_id = ?
                '''
                cursor.execute(status_update_query, (task_id,))
    
    # Commit the changes
    conn.commit()
    print(f"\nMigration completed! Updated {updated_count} records.")
    
    # Show summary of changes
    print("\nVerifying changes...")
    verify_query = '''
    SELECT 
        COUNT(*) as total_with_billing_notes,
        COUNT(CASE WHEN billing_status = 'Paid' THEN 1 END) as paid_status_count
    FROM provider_tasks 
    WHERE billing_notes IS NOT NULL AND billing_notes != ''
    '''
    
    cursor.execute(verify_query)
    result = cursor.fetchone()
    print(f"Records with billing_notes: {result[0]}")
    print(f"Records with 'Paid' status: {result[1]}")
    
    conn.close()

def extract_billing_info(notes):
    """Extract billing-related information from notes"""
    if not notes:
        return None
    
    notes_lower = notes.lower()
    billing_keywords = ['paid by zen', 'billing', 'paid', 'invoice', 'claim']
    
    # Check if any billing keywords are present
    has_billing_info = any(keyword in notes_lower for keyword in billing_keywords)
    
    if has_billing_info:
        # Return the original notes as billing information
        # In a more sophisticated version, you could parse and clean this
        return notes.strip()
    
    return None

if __name__ == "__main__":
    main()