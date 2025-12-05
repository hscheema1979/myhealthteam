#!/usr/bin/env python3
"""
Test the updated get_available_months function to verify November dropdown is fixed
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import get_db_connection
import pandas as pd
import calendar

def get_available_months():
    """Get list of available months from provider_tasks data including partitioned tables."""
    conn = get_db_connection()
    
    # Query both main table and partitioned tables
    query = """
    SELECT 
        strftime('%Y', task_date) as year,
        strftime('%m', task_date) as month,
        'main' as source_table
    FROM provider_tasks
    WHERE task_date IS NOT NULL
    
    UNION
    
    SELECT 
        strftime('%Y', task_date) as year,
        strftime('%m', task_date) as month,
        'partitioned' as source_table
    FROM provider_tasks_2025_10
    WHERE task_date IS NOT NULL
    
    UNION
    
    SELECT 
        strftime('%Y', task_date) as year,
        strftime('%m', task_date) as month,
        'partitioned' as source_table
    FROM provider_tasks_2025_11
    WHERE task_date IS NOT NULL
    
    ORDER BY year DESC, month DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return []
    
    # Remove duplicates and convert to list of dictionaries with display names
    months_dict = {}
    for _, row in df.iterrows():
        # Skip rows with None values
        if row['year'] is None or row['month'] is None:
            continue
            
        year = int(row['year'])
        month = int(row['month'])
        key = f"{year}-{month:02d}"
        
        # Only add if not already exists
        if key not in months_dict:
            display = f"{calendar.month_name[month]} {year}"
            months_dict[key] = {
                'year': year,
                'month': month,
                'display': display
            }
    
    return list(months_dict.values())

def main():
    print('TESTING UPDATED get_available_months FUNCTION')
    print('=' * 60)
    
    months = get_available_months()
    
    print(f'Found {len(months)} available months:')
    for month in months:
        print(f'  - {month["display"]}')
    
    # Check specifically for October and November 2025
    oct_2025_found = any(m['year'] == 2025 and m['month'] == 10 for m in months)
    nov_2025_found = any(m['year'] == 2025 and m['month'] == 11 for m in months)
    
    print(f'\nSpecific checks:')
    print(f'  October 2025 found: {oct_2025_found}')
    print(f'  November 2025 found: {nov_2025_found}')
    
    if nov_2025_found:
        print('\n✅ SUCCESS: November 2025 is now available in the dropdown!')
    else:
        print('\n❌ FAILED: November 2025 is still missing from the dropdown')
    
    return nov_2025_found

if __name__ == '__main__':
    main()