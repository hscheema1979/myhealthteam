#!/usr/bin/env python3
"""
Test October 2025 billing weeks to debug the weekly view error
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database import get_db_connection
import pandas as pd

def get_billing_weeks_list(selected_year=None, selected_month=None):
    """Get list of available billing weeks from provider_tasks including partitioned tables."""
    conn = get_db_connection()
    
    if selected_year and selected_month:
        # Check if we need to query partitioned table for 2025 months
        if selected_year == 2025 and selected_month in [10, 11]:
            if selected_month == 10:
                table_name = 'provider_tasks_2025_10'
            elif selected_month == 11:
                table_name = 'provider_tasks_2025_11'
            
            query = f"""
            SELECT 
                strftime('%Y-%W', task_date) as billing_week,
                strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
                strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
            FROM {table_name}
            WHERE strftime('%Y', task_date) = ? 
            AND strftime('%m', task_date) = ?
            AND task_date IS NOT NULL
            GROUP BY strftime('%Y-%W', task_date)
            ORDER BY billing_week DESC
            """
            df = pd.read_sql_query(query, conn, params=[str(selected_year), f"{selected_month:02d}"])
        else:
            query = """
            SELECT 
                strftime('%Y-%W', task_date) as billing_week,
                strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
                strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
            FROM provider_tasks
            WHERE strftime('%Y', task_date) = ? 
            AND strftime('%m', task_date) = ?
            AND task_date IS NOT NULL
            GROUP BY strftime('%Y-%W', task_date)
            ORDER BY billing_week DESC
            """
            df = pd.read_sql_query(query, conn, params=[str(selected_year), f"{selected_month:02d}"])
    else:
        query = """
        SELECT 
            strftime('%Y-%W', task_date) as billing_week,
            strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
            strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
        FROM provider_tasks
        WHERE task_date IS NOT NULL
        GROUP BY strftime('%Y-%W', task_date)
        ORDER BY billing_week DESC
        """
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df

def test_get_provider_billing_details(billing_week):
    """Get detailed billing information for a specific week."""
    conn = get_db_connection()
    
    # Parse billing week to determine which table to query
    if '-' in billing_week:
        year, week = billing_week.split('-')
        year = int(year)
        
        if year == 2025:
            # Try October first - using strftime for week calculation instead of billing_week column
            query_oct = """
            SELECT 
                provider_task_id,
                provider_id,
                provider_name,
                patient_name,
                task_date,
                ? as billing_week
            FROM provider_tasks_2025_10
            WHERE strftime('%Y-%W', task_date) = ?
            AND task_date IS NOT NULL
            ORDER BY provider_name, task_date
            """
            df = pd.read_sql_query(query_oct, conn, params=[billing_week, billing_week])
            
            # If no data found in October, try November
            if df.empty:
                query_nov = """
                SELECT 
                    provider_task_id,
                    provider_id,
                    provider_name,
                    patient_name,
                    task_date,
                    ? as billing_week
                FROM provider_tasks_2025_11
                WHERE strftime('%Y-%W', task_date) = ?
                AND task_date IS NOT NULL
                ORDER BY provider_name, task_date
                """
                df = pd.read_sql_query(query_nov, conn, params=[billing_week, billing_week])
        else:
            query = """
            SELECT 
                provider_task_id,
                provider_id,
                provider_name,
                patient_name,
                task_date,
                billing_week
            FROM provider_tasks
            WHERE billing_week = ?
            AND task_date IS NOT NULL
            ORDER BY provider_name, task_date
            """
            df = pd.read_sql_query(query, conn, params=[billing_week])
    else:
        query = """
        SELECT 
            provider_task_id,
            provider_id,
            provider_name,
            patient_name,
            task_date,
            billing_week
        FROM provider_tasks
        WHERE billing_week = ?
        AND task_date IS NOT NULL
        ORDER BY provider_name, task_date
        """
        df = pd.read_sql_query(query, conn, params=[billing_week])
    
    conn.close()
    return df

def main():
    print('TESTING OCTOBER 2025 BILLING WEEKS')
    print('=' * 60)
    
    # Test getting weeks for October 2025
    print('\n1. Testing get_billing_weeks_list for October 2025:')
    oct_weeks = get_billing_weeks_list(2025, 10)
    print(f'Found {len(oct_weeks)} billing weeks for October 2025')
    
    if not oct_weeks.empty:
        for _, week in oct_weeks.iterrows():
            print(f'  - Week {week["billing_week"]}: {week["week_start_date"]} to {week["week_end_date"]}')
        
        # Test getting details for each October week
        print('\n2. Testing get_provider_billing_details for October weeks:')
        for _, week in oct_weeks.iterrows():
            billing_week = week['billing_week']
            print(f'\nTesting week {billing_week}:')
            
            try:
                details = test_get_provider_billing_details(billing_week)
                print(f'  Found {len(details)} tasks')
                
                if not details.empty:
                    print(f'  Sample record:')
                    print(f'    Provider: {details.iloc[0]["provider_name"]}')
                    print(f'    Patient: {details.iloc[0]["patient_name"]}')
                    print(f'    Date: {details.iloc[0]["task_date"]}')
                else:
                    print(f'  No details found for week {billing_week}')
                    
            except Exception as e:
                print(f'  ERROR getting details for week {billing_week}: {e}')
    else:
        print('  No billing weeks found for October 2025')
    
    # Test November as comparison
    print('\n3. Testing get_billing_weeks_list for November 2025:')
    nov_weeks = get_billing_weeks_list(2025, 11)
    print(f'Found {len(nov_weeks)} billing weeks for November 2025')
    
    if not nov_weeks.empty:
        for _, week in nov_weeks.iterrows():
            print(f'  - Week {week["billing_week"]}: {week["week_start_date"]} to {week["week_end_date"]}')

if __name__ == '__main__':
    main()