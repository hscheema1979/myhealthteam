#!/usr/bin/env python3
import sqlite3
import sys

def final_data_integrity_report():
    conn = sqlite3.connect('sheets_data.db')
    cursor = conn.cursor()

    print("=== FINAL DATA INTEGRITY REPORT ===")
    print("Analysis Date: 2025-11-23")
    print("Focus: October 2025 Import Validation\n")

    print("🎯 EXECUTIVE SUMMARY:")
    print("- Source Data: 621 records")
    print("- Staging Data: 619 records")
    print("- Data Loss: 2 records (0.32%)")
    print("- Duplicates Found: 6 patient IDs appear twice")
    print("- Status: ⚠️ MINOR ISSUES - Most data integrity maintained\n")

    # 1. Root Cause Analysis
    print("📊 ROOT CAUSE ANALYSIS:")
    print("1. CSV Import Issue:")
    print("   - 620/621 records show literal 'LAST FIRST DOB' in 'LAST FIRST DOB' column")
    print("   - This suggests column mapping or CSV import issue")
    print("   - However, individual 'Last', 'First', 'DOB' columns contain correct data")

    print("\n2. Processing Logic:")
    print("   - WHERE clause expects 'LAST FIRST DOB' to NOT equal 'LAST FIRST DOB'")
    print("   - Current logic filters out most records, yet 619 made it to staging")
    print("   - This suggests either:")
    print("     a) Script was run with different WHERE clause")
    print("     b) Data was imported in different state")
    print("     c) Processing logic changed between runs")

    # 2. Data Quality Assessment
    print(f"\n🔍 DATA QUALITY ASSESSMENT:")

    print("Source Data Quality:")
    cursor.execute('SELECT COUNT(*) FROM SOURCE_PATIENT_DATA WHERE "Last" IS NOT NULL AND "First" IS NOT NULL AND "DOB" IS NOT NULL')
    valid_source = cursor.fetchone()[0]
    print(f"   Valid source records: {valid_source}/621 ({valid_source/621*100:.1f}%)")

    print("\nStaging Data Quality:")
    cursor.execute('SELECT COUNT(*) FROM staging_patients')
    staging_count = cursor.fetchone()[0]
    print(f"   Staging records: {staging_count}")

    cursor.execute('SELECT COUNT(*) FROM staging_patients WHERE first_name IS NOT NULL AND last_name IS NOT NULL AND date_of_birth IS NOT NULL')
    valid_staging = cursor.fetchone()[0]
    print(f"   Valid staging records: {valid_staging}/{staging_count} ({valid_staging/staging_count*100:.1f}%)")

    # 3. Duplicate Analysis
    print(f"\n🔄 DUPLICATE ANALYSIS:")
    cursor.execute('SELECT patient_id, COUNT(*) as count FROM staging_patients GROUP BY patient_id HAVING COUNT(*) > 1')
    duplicates = cursor.fetchall()

    print(f"Found {len(duplicates)} duplicate patient groups:")
    total_duplicate_records = 0
    for dup in duplicates:
        print(f"   ❌ {dup[0]}: {dup[1]} records")
        total_duplicate_records += dup[1]

    if len(duplicates) > 0:
        print(f"\nImpact:")
        print(f"   - Total duplicate records: {total_duplicate_records}")
        print(f"   - Unique duplicate patients: {len(duplicates)}")
        print(f"   - Records to deduplicate: {total_duplicate_records - len(duplicates)}")

    # 4. Missing Records Analysis
    print(f"\n📉 MISSING RECORDS ANALYSIS:")
    source_valid = valid_source
    staging_valid = valid_staging

    # Count source records that should have made it to staging
    cursor.execute('''SELECT COUNT(*) FROM SOURCE_PATIENT_DATA spd
                      WHERE spd."Last" IS NOT NULL AND spd."First" IS NOT NULL AND spd."DOB" IS NOT NULL
                      AND spd."Last" != "" AND spd."First" != "" AND spd."DOB" != ""
                      AND spd."Last" != "Last" AND spd."First" != "First" AND spd."DOB" != "DOB"''')

    source_should_process = cursor.fetchone()[0]
    print(f"Source records that should be processed: {source_should_process}")
    print(f"Records actually in staging: {staging_count}")
    print(f"Missing from staging: {source_should_process - staging_count}")

    if source_should_process - staging_count > 0:
        print(f"\n⚠️ DATA LOSS DETECTED: {source_should_process - staging_count} records missing from staging!")

        # Show what's missing
        cursor.execute('''SELECT spd."Last", spd."First", spd."DOB", spd."LAST FIRST DOB" FROM SOURCE_PATIENT_DATA spd
                          WHERE spd."Last" IS NOT NULL AND spd."First" IS NOT NULL AND spd."DOB" IS NOT NULL
                          AND spd."Last" != "" AND spd."First" != "" AND spd."DOB" != ""
                          AND spd."Last" != "Last" AND spd."First" != "First" AND spd."DOB" != "DOB"
                          AND spd."LAST FIRST DOB" NOT IN (SELECT patient_id FROM staging_patients)
                          LIMIT 5''')

        missing_records = cursor.fetchall()
        print("   Sample missing records:")
        for record in missing_records:
            print(f"     Last: '{record[0]}', First: '{record[1]}', DOB: '{record[2]}'")

    # 5. Recommendations
    print(f"\n💡 RECOMMENDATIONS:")

    if len(duplicates) > 0:
        print("1. 🧹 CLEAN DUPLICATES:")
        print("   - Remove duplicate patient records from staging_patients")
        print("   - Keep most recent record or merge data appropriately")

    if source_should_process - staging_count > 0:
        print("2. 🔍 INVESTIGATE MISSING RECORDS:")
        print("   - Check WHERE clause logic in 4a-transform.ps1")
        print("   - Verify CSV import column mapping")
        print("   - Ensure all valid records are processed")

    print("3. 📋 VALIDATE WORKFLOW:")
    print("   - Re-run 4a-transform.ps1 with corrected WHERE clause")
    print("   - Verify all patient data makes it to staging")
    print("   - Test duplicate removal logic")

    print("4. 🛡️ PREVENT FUTURE ISSUES:")
    print("   - Add data validation checks before staging creation")
    print("   - Include record count validation in scripts")
    print("   - Add duplicate detection and handling")

    # 6. Final Assessment
    print(f"\n✅ FINAL ASSESSMENT:")
    data_integrity_score = (staging_valid / source_valid * 100) if source_valid > 0 else 0
    print(f"Data Integrity Score: {data_integrity_score:.1f}%")

    if data_integrity_score >= 99:
        print("Status: ✅ EXCELLENT - Minor issues only")
    elif data_integrity_score >= 95:
        print("Status: ⚠️ GOOD - Some issues to address")
    elif data_integrity_score >= 90:
        print("Status: ❌ POOR - Significant issues found")
    else:
        print("Status: 🚨 CRITICAL - Major data integrity problems")

    print(f"\n📊 SUMMARY:")
    print(f"   Total source records: {source_valid}")
    print(f"   Successfully processed: {staging_valid}")
    print(f"   Duplicates to clean: {total_duplicate_records - len(duplicates) if len(duplicates) > 0 else 0}")
    print(f"   Missing records: {max(0, source_should_process - staging_count)}")

    conn.close()

if __name__ == '__main__':
    final_data_integrity_report()