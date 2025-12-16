#!/usr/bin/env python3
"""
Count how many tasks have real patient names vs placeholders
"""

import sqlite3

def count_real_patient_names():
    print("Counting tasks with real patient names vs placeholders")
    print("=" * 60)
    
    conn = sqlite3.connect('production.db')
    
    # Get all task tables
    cursor = conn.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND (name LIKE 'provider_tasks_%' OR name LIKE 'coordinator_tasks_%')
        ORDER BY name
    """)
    
    task_tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(task_tables)} task tables")
    
    total_real_patients = 0
    total_placeholder_patients = 0
    total_records = 0
    
    for table_name in task_tables:
        # Check if this is a provider or coordinator table
        is_provider = 'provider_tasks' in table_name
        
        if is_provider:
            # Provider tables have patient_name column
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN patient_name LIKE 'Aaa, Aaa%' THEN 1 ELSE 0 END) as placeholder,
                    SUM(CASE WHEN patient_name LIKE 'Place holder%' THEN 1 ELSE 0 END) as placeholder2,
                    SUM(CASE WHEN patient_name = 'nan' OR patient_name IS NULL THEN 1 ELSE 0 END) as null_names,
                    SUM(CASE WHEN patient_name NOT LIKE 'Aaa, Aaa%' 
                             AND patient_name NOT LIKE 'Place holder%' 
                             AND patient_name != 'nan' 
                             AND patient_name IS NOT NULL 
                             AND TRIM(patient_name) != '' THEN 1 ELSE 0 END) as real_patients
                FROM {table_name}
            """
        else:
            # Coordinator tables only have patient_id, but we can check if it's a placeholder
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN patient_id LIKE 'Aaa, Aaa%' THEN 1 ELSE 0 END) as placeholder,
                    SUM(CASE WHEN patient_id LIKE 'Place holder%' THEN 1 ELSE 0 END) as placeholder2,
                    SUM(CASE WHEN patient_id = 'nan' OR patient_id IS NULL THEN 1 ELSE 0 END) as null_names,
                    SUM(CASE WHEN patient_id NOT LIKE 'Aaa, Aaa%' 
                             AND patient_id NOT LIKE 'Place holder%' 
                             AND patient_id != 'nan' 
                             AND patient_id IS NOT NULL 
                             AND TRIM(patient_id) != '' THEN 1 ELSE 0 END) as real_patients
                FROM {table_name}
            """
        
        try:
            cursor = conn.execute(query)
            result = cursor.fetchone()
            if result:
                total, placeholder, placeholder2, null_names, real_patients = result
                
                total_placeholders = placeholder + placeholder2 + null_names
                
                if total > 0:
                    print(f"\n{table_name}:")
                    print(f"  Total records: {total}")
                    print(f"  Real patients: {real_patients} ({real_patients/total*100:.1f}%)")
                    print(f"  Placeholders: {total_placeholders} ({total_placeholders/total*100:.1f}%)")
                    
                    total_real_patients += real_patients
                    total_placeholder_patients += total_placeholders
                    total_records += total
                    
                    # Show some examples if there are real patients
                    if real_patients > 0:
                        if is_provider:
                            example_query = f"""
                                SELECT DISTINCT patient_name 
                                FROM {table_name} 
                                WHERE patient_name NOT LIKE 'Aaa, Aaa%' 
                                AND patient_name NOT LIKE 'Place holder%' 
                                AND patient_name != 'nan' 
                                AND patient_name IS NOT NULL 
                                AND TRIM(patient_name) != ''
                                LIMIT 2
                            """
                        else:
                            example_query = f"""
                                SELECT DISTINCT patient_id 
                                FROM {table_name} 
                                WHERE patient_id NOT LIKE 'Aaa, Aaa%' 
                                AND patient_id NOT LIKE 'Place holder%' 
                                AND patient_id != 'nan' 
                                AND patient_id IS NOT NULL 
                                AND TRIM(patient_id) != ''
                                LIMIT 2
                            """
                        
                        cursor = conn.execute(example_query)
                        examples = [row[0] for row in cursor.fetchall()]
                        if examples:
                            print(f"  Real patient examples: {examples}")
        except Exception as e:
            print(f"Error processing {table_name}: {e}")
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"Total task records: {total_records}")
    print(f"Real patient names: {total_real_patients} ({total_real_patients/total_records*100:.1f}%)")
    print(f"Placeholder/invalid names: {total_placeholder_patients} ({total_placeholder_patients/total_records*100:.1f}%)")
    
    conn.close()

if __name__ == "__main__":
    count_real_patient_names()