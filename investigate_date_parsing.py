import sqlite3

conn = sqlite3.connect('scripts/sheets_data.db')
cursor = conn.cursor()

print("=" * 80)
print("INVESTIGATING COORDINATOR DATE PARSING FAILURE")
print("=" * 80)

print("\n1. Sample 'Date Only' values from SOURCE_CM_TASKS_2025_10:")
cursor.execute('SELECT "Date Only" FROM SOURCE_CM_TASKS_2025_10 WHERE "Date Only" IS NOT NULL LIMIT 10')
for row in cursor.fetchall():
    val = row[0]
    print(f"  Value: '{val}' | Length: {len(val)} | Type: {type(val)}")

print("\n2. Test date parsing logic from staging_coordinator_tasks.sql:")
query = """
SELECT 
    "Date Only",
    "Date Only" GLOB '??/??/????',
    "Date Only" GLOB '??/??/??',
    CASE
        WHEN "Date Only" GLOB '??/??/????' THEN 'Format 1: MM/DD/YYYY'
        WHEN "Date Only" GLOB '??/??/??' THEN 'Format 2: MM/DD/YY'
        ELSE 'NO MATCH'
    END as detected_format,
    -- Try to parse it
    CASE
        WHEN "Date Only" GLOB '??/??/????' THEN 
            substr("Date Only", 7, 4) || '-' || printf('%02d', CAST(substr("Date Only", 1, 2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only", 4, 2) AS INTEGER))
        WHEN "Date Only" GLOB '??/??/??' THEN 
            '20' || substr("Date Only", 7, 2) || '-' || printf('%02d', CAST(substr("Date Only", 1, 2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only", 4, 2) AS INTEGER))
        ELSE NULL
    END AS parsed_date
FROM SOURCE_CM_TASKS_2025_10
WHERE "Date Only" IS NOT NULL
LIMIT 10
"""
cursor.execute(query)
print("\nDate Only | GLOB ????  | GLOB ?? | Format | Parsed")
print("-" * 80)
for row in cursor.fetchall():
    print(f"{row[0]:12} | {str(row[1]):10} | {str(row[2]):7} | {row[3]:20} | {row[4]}")

print("\n3. Check source_coordinator_tasks_history (the combined table):")
cursor.execute('SELECT "Date Only" FROM source_coordinator_tasks_history WHERE "Date Only" IS NOT NULL LIMIT 10')
print("\nSample dates from source_coordinator_tasks_history:")
for row in cursor.fetchall():
    print(f"  '{row[0]}'")

print("\n4. Distribution of date formats:")
query = """
SELECT 
    CASE
        WHEN "Date Only" IS NULL THEN 'NULL'
        WHEN "Date Only" GLOB '??/??/????' THEN 'MM/DD/YYYY'
        WHEN "Date Only" GLOB '??/??/??' THEN 'MM/DD/YY'
        ELSE 'OTHER: ' || substr("Date Only", 1, 20)
    END as format,
    COUNT(*) as count
FROM source_coordinator_tasks_history
GROUP BY format
ORDER BY count DESC
"""
cursor.execute(query)
print("\nFormat Distribution in source_coordinator_tasks_history:")
for row in cursor.fetchall():
    print(f"  {row[0]:30} | {row[1]:,}")

conn.close()

print("\n" + "=" * 80)
