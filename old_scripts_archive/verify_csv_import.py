import sqlite3
import pandas as pd

staging_db = 'scripts/sheets_data.db'

print("=" * 80)
print("DETAILED CSV IMPORT VERIFICATION - OCTOBER 2025")
print("=" * 80)

conn = sqlite3.connect(staging_db)

print("\n1. COORDINATOR TASKS - SOURCE_CM_TASKS_2025_10")
print("-" * 80)
print("First 10 rows from SOURCE table:")
query = """
SELECT "Date Only", "Pt Name", Type, "Mins B", Staff 
FROM SOURCE_CM_TASKS_2025_10 
LIMIT 10
"""
result = pd.read_sql_query(query, conn)
print(result.to_string())

print("\n\nDate distribution in SOURCE_CM_TASKS_2025_10:")
query = """
SELECT "Date Only", COUNT(*) as count
FROM SOURCE_CM_TASKS_2025_10
GROUP BY "Date Only"
ORDER BY "Date Only"
LIMIT 20
"""
result = pd.read_sql_query(query, conn)
print(result.to_string(index=False))

print("\n\n2. PROVIDER TASKS - SOURCE_PSL_TASKS_2025_10")
print("-" * 80)
print("First 10 rows from SOURCE table:")
query = """
SELECT DOS, "Patient Last, First DOB", Service, Minutes, Prov
FROM SOURCE_PSL_TASKS_2025_10
LIMIT 10
"""
result = pd.read_sql_query(query, conn)
print(result.to_string())

print("\n\nDOS distribution in SOURCE_PSL_TASKS_2025_10:")
query = """
SELECT DOS, COUNT(*) as count
FROM SOURCE_PSL_TASKS_2025_10
GROUP BY DOS
ORDER BY DOS
"""
result = pd.read_sql_query(query, conn)
print(result.to_string(index=False))

print("\n\n3. STAGING COORDINATOR TASKS - After Normalization")
print("-" * 80)
query = """
SELECT activity_date, patient_name_raw, task_type, minutes_raw, staff_code
FROM staging_coordinator_tasks
WHERE year_month = '2025_10'
LIMIT 10
"""
result = pd.read_sql_query(query, conn)
print(result.to_string())

print("\n\nActivity date distribution in staging_coordinator_tasks (2025_10):")
query = """
SELECT activity_date, COUNT(*) as count
FROM staging_coordinator_tasks
WHERE year_month = '2025_10'
GROUP BY activity_date
ORDER BY activity_date
LIMIT 20
"""
result = pd.read_sql_query(query, conn)
print(result.to_string(index=False))

print("\n\n4. STAGING PROVIDER TASKS - After Normalization")
print("-" * 80)
query = """
SELECT activity_date, patient_name_raw, service, minutes_raw, provider_code
FROM staging_provider_tasks
WHERE year_month = '2025_10'
LIMIT 10
"""
result = pd.read_sql_query(query, conn)
print(result.to_string())

print("\n\nActivity date distribution in staging_provider_tasks (2025_10):")
query = """
SELECT activity_date, COUNT(*) as count
FROM staging_provider_tasks
WHERE year_month = '2025_10'
GROUP BY activity_date
ORDER BY activity_date
"""
result = pd.read_sql_query(query, conn)
print(result.to_string(index=False))

print("\n\n5. CHECK FOR PLACEHOLDER ROWS")
print("-" * 80)
print("Coordinator tasks with NULL or empty dates:")
query = """
SELECT COUNT(*) as null_dates, 
       COUNT(CASE WHEN "Pt Name" IS NULL OR "Pt Name" = '' THEN 1 END) as null_patients
FROM SOURCE_CM_TASKS_2025_10
WHERE "Date Only" IS NULL OR "Date Only" = ''
"""
result = pd.read_sql_query(query, conn)
print(result.to_string(index=False))

print("\nProvider tasks with NULL or empty DOS:")
query = """
SELECT COUNT(*) as null_dos,
       COUNT(CASE WHEN "Patient Last, First DOB" IS NULL OR "Patient Last, First DOB" = '' THEN 1 END) as null_patients
FROM SOURCE_PSL_TASKS_2025_10
WHERE DOS IS NULL OR DOS = ''
"""
result = pd.read_sql_query(query, conn)
print(result.to_string(index=False))

conn.close()

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
