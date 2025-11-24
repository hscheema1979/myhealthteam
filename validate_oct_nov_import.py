import sqlite3
import pandas as pd
from datetime import datetime

staging_db = 'scripts/sheets_data.db'
prod_db = 'production.db'

print("=" * 70)
print("OCTOBER & NOVEMBER 2025 DATA IMPORT VALIDATION")
print("=" * 70)
print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Connect to staging
conn_staging = sqlite3.connect(staging_db)

print("1. DATE RANGE CHECK - Staging Provider Tasks")
print("-" * 70)
query = """
SELECT 
    MIN(activity_date) as earliest_date,
    MAX(activity_date) as latest_date,
    COUNT(*) as total_rows,
    COUNT(DISTINCT REPLACE(patient_name_raw, ',', '')) as unique_patients,
    COUNT(DISTINCT provider_code) as unique_providers
FROM staging_provider_tasks
WHERE activity_date >= '2025-10-01'
"""
result = pd.read_sql_query(query, conn_staging)
print(result.to_string(index=False))

print("\n2. DATE RANGE CHECK - Staging Coordinator Tasks")
print("-" * 70)
query = """
SELECT 
    MIN(activity_date) as earliest_date,
    MAX(activity_date) as latest_date,
    COUNT(*) as total_rows,
    COUNT(DISTINCT REPLACE(patient_name_raw, ',', '')) as unique_patients,
    COUNT(DISTINCT staff_code) as unique_staff
FROM staging_coordinator_tasks
WHERE activity_date >= '2025-10-01'
"""
result = pd.read_sql_query(query, conn_staging)
print(result.to_string(index=False))

print("\n3. PATIENT SAMPLE - October/November Provider Tasks")
print("-" * 70)
query = """
SELECT 
    REPLACE(patient_name_raw, 'ZEN-', '') as patient_name,
    COUNT(*) as task_count,
    MIN(activity_date) as first_visit,
    MAX(activity_date) as last_visit
FROM staging_provider_tasks
WHERE activity_date >= '2025-10-01' AND activity_date < '2025-12-01'
GROUP BY patient_name_raw
ORDER BY task_count DESC
LIMIT 10
"""
result = pd.read_sql_query(query, conn_staging)
print(result.to_string(index=False))

conn_staging.close()

print("\n4. LINKAGE CHECK - Provider Tasks vs Production Patients")
print("-" * 70)
conn_prod = sqlite3.connect(prod_db)
conn_prod.execute("ATTACH DATABASE 'scripts/sheets_data.db' AS staging;")
query = """
WITH oct_nov_patients AS (
    SELECT DISTINCT 
        UPPER(TRIM(REPLACE(REPLACE(patient_name_raw, 'ZEN-', ''), ',', ''))) as normalized_name
    FROM staging.staging_provider_tasks
    WHERE activity_date >= '2025-10-01' AND activity_date < '2025-12-01'
    AND patient_name_raw IS NOT NULL
)
SELECT 
    COUNT(*) as total_unique_patients_oct_nov,
    SUM(CASE WHEN p.patient_id IS NOT NULL THEN 1 ELSE 0 END) as found_in_production,
    ROUND(100.0 * SUM(CASE WHEN p.patient_id IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) as linkage_pct
FROM oct_nov_patients o
LEFT JOIN patients p ON UPPER(TRIM(p.patient_id)) = o.normalized_name
"""
result = pd.read_sql_query(query, conn_prod)
print(result.to_string(index=False))

print("\n5. NEW PATIENTS (Not in Production)")
print("-" * 70)
query = """
WITH oct_nov_patients AS (
    SELECT DISTINCT 
        REPLACE(patient_name_raw, 'ZEN-', '') as patient_name,
        UPPER(TRIM(REPLACE(REPLACE(patient_name_raw, 'ZEN-', ''), ',', ''))) as normalized_name
    FROM staging.staging_provider_tasks
    WHERE activity_date >= '2025-10-01' AND activity_date < '2025-12-01'
    AND patient_name_raw IS NOT NULL
)
SELECT o.patient_name
FROM oct_nov_patients o
LEFT JOIN patients p ON UPPER(TRIM(p.patient_id)) = o.normalized_name
WHERE p.patient_id IS NULL
LIMIT 15
"""
result = pd.read_sql_query(query, conn_prod)
print(f"Sample of new patients (showing first 15):\n{result.to_string(index=False)}")

conn_prod.close()

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
print("=" * 70)
