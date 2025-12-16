#!/usr/bin/env python3
"""
CSV vs Database Comparison Script
=================================
Verifies that data imported from CSV files matches what's in the database.
This validates the transform_production_data_v3_fixed.py script is working correctly.

Usage:
    python compare_csv_vs_database.py
"""

import glob
import os
import re
import sqlite3
from datetime import datetime

import pandas as pd

DB_PATH = "production.db"
CSV_DIR = "downloads"


def get_db_connection():
    """Get database connection with proper row factory"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_date(date_str):
    """Parse date from various formats"""
    if pd.isna(date_str) or not date_str:
        return None
    date_str = str(date_str).strip()
    if not date_str:
        return None
    formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%m/%d/%y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def normalize_patient_id(patient_str):
    """Normalize patient ID to match database format"""
    if pd.isna(patient_str) or not patient_str:
        return None

    patient_str = str(patient_str).strip()

    # Remove prefixes
    prefixes = ["ZEN-", "PM-", "ZMN-", "3PR-", "BLESSEDCARE-", "BLEESSEDCARE-"]
    for prefix in prefixes:
        if patient_str.startswith(prefix):
            patient_str = patient_str[len(prefix) :]

    # Remove commas and normalize
    patient_str = patient_str.replace(", ", " ").replace(",", " ")
    patient_str = patient_str.replace("  ", " ").strip()

    return patient_str


def extract_provider_code_from_filename(filename):
    """Extract provider code from PSL/RVZ filename"""
    match = re.search(r"(PSL|RVZ)_ZEN-([A-Z]+)", filename)
    if match:
        return match.group(2)
    return None


def compare_provider_tasks():
    """Compare PSL CSV files with provider_tasks_YYYY_MM tables"""
    print("=" * 80)
    print("COMPARING PROVIDER TASKS (PSL Files)")
    print("=" * 80)

    conn = get_db_connection()

    psl_files = glob.glob(os.path.join(CSV_DIR, "PSL_ZEN-*.csv"))

    total_csv_rows = 0
    total_db_rows = 0

    for file_path in sorted(psl_files):
        filename = os.path.basename(file_path)
        provider_code = extract_provider_code_from_filename(filename)

        if not provider_code:
            print(f"⚠️  Could not extract provider code from {filename}")
            continue

        print(f"\n📁 File: {filename}")
        print(f"   Provider Code: {provider_code}")

        # Read CSV
        try:
            df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
            csv_count = len(df)
            total_csv_rows += csv_count
            print(f"   CSV Rows: {csv_count}")
        except Exception as e:
            print(f"   ❌ Error reading CSV: {e}")
            continue

        # Group CSV rows by month
        csv_by_month = {}
        for _, row in df.iterrows():
            dos = parse_date(row.get("DOS"))
            if not dos:
                continue

            table_name = (
                f"provider_tasks_{dos[:7].replace('-', '_')}"  # YYYY-MM -> YYYY_MM
            )
            if table_name not in csv_by_month:
                csv_by_month[table_name] = 0
            csv_by_month[table_name] += 1

        # Check database counts
        for table_name, csv_month_count in csv_by_month.items():
            # Get provider ID from mapping
            cursor = conn.execute(
                "SELECT user_id FROM staff_code_mapping WHERE staff_code = ?",
                (provider_code,),
            )
            provider_row = cursor.fetchone()

            if not provider_row:
                print(f"   ❌ No mapping for {provider_code} in staff_code_mapping")
                continue

            provider_id = provider_row[0]

            # Count database rows for this provider in this month
            db_count = conn.execute(
                f"SELECT COUNT(*) as count FROM {table_name} WHERE provider_id = ?",
                (provider_id,),
            ).fetchone()[0]
            total_db_rows += db_count

            status = "✅" if csv_month_count == db_count else "❌"
            print(f"   {status} {table_name}: CSV={csv_month_count}, DB={db_count}")

    print(f"\n📊 Totals: CSV={total_csv_rows}, DB={total_db_rows}")
    conn.close()


def compare_coordinator_tasks():
    """Compare RVZ/CMLog CSV files with coordinator_tasks_YYYY_MM tables"""
    print("\n" + "=" * 80)
    print("COMPARING COORDINATOR TASKS (RVZ/CMLog Files)")
    print("=" * 80)

    conn = get_db_connection()

    # Process RVZ files
    rvz_files = glob.glob(os.path.join(CSV_DIR, "RVZ_ZEN-*.csv"))
    cmlog_files = glob.glob(os.path.join(CSV_DIR, "CMLog_*.csv"))

    total_csv_rows = 0
    total_db_rows = 0

    for file_path in sorted(rvz_files + cmlog_files):
        filename = os.path.basename(file_path)

        # Determine staff code
        rvz_match = re.search(r"RVZ_ZEN-([A-Z]+)", filename)
        cmlog_match = re.search(r"CMLog_([A-Za-z0-9]+)\.csv", filename)

        if rvz_match:
            staff_code = rvz_match.group(1)
            file_type = "RVZ"
        elif cmlog_match:
            staff_code = cmlog_match.group(1)
            file_type = "CMLog"
        else:
            continue

        print(f"\n📁 File: {filename}")
        print(f"   File Type: {file_type}")
        print(f"   Staff Code: {staff_code}")

        # Read CSV
        try:
            df = pd.read_csv(file_path, encoding="utf-8", on_bad_lines="skip")
            # Filter out placeholder rows
            df = df[
                ~df.astype(str)
                .apply(
                    lambda x: x.str.contains("Place holder|Last, First DOB", case=False)
                )
                .any(axis=1)
            ]
            csv_count = len(df)
            total_csv_rows += csv_count
            print(f"   CSV Rows: {csv_count}")
        except Exception as e:
            print(f"   ❌ Error reading CSV: {e}")
            continue

        # Group CSV rows by month
        csv_by_month = {}
        col_date = (
            "Date Only" if file_type == "RVZ" else "Date Only"
        )  # Both use same column name

        for _, row in df.iterrows():
            dos = parse_date(row.get(col_date))
            if not dos:
                continue

            table_name = f"coordinator_tasks_{dos[:7].replace('-', '_')}"
            if table_name not in csv_by_month:
                csv_by_month[table_name] = 0
            csv_by_month[table_name] += 1

        # Check database counts
        for table_name, csv_month_count in csv_by_month.items():
            # Get coordinator ID from mapping
            # Handle ZEN-xxx format for RVZ files
            lookup_code = (
                f"ZEN-{staff_code}"
                if file_type == "RVZ" and not staff_code.startswith("ZEN-")
                else staff_code
            )

            cursor = conn.execute(
                "SELECT user_id FROM staff_code_mapping WHERE staff_code = ?",
                (lookup_code,),
            )
            coord_row = cursor.fetchone()

            if not coord_row:
                print(f"   ❌ No mapping for {lookup_code} in staff_code_mapping")
                continue

            coordinator_id = coord_row[0]

            # Count database rows for this coordinator in this month
            db_count = conn.execute(
                f"SELECT COUNT(*) as count FROM {table_name} WHERE coordinator_id = ?",
                (coordinator_id,),
            ).fetchone()[0]
            total_db_rows += db_count

            status = "✅" if csv_month_count == db_count else "❌"
            print(f"   {status} {table_name}: CSV={csv_month_count}, DB={db_count}")

    print(f"\n📊 Totals: CSV={total_csv_rows}, DB={total_db_rows}")
    conn.close()


def compare_staff_code_mappings():
    """Verify all staff codes in CSV files have database mappings"""
    print("\n" + "=" * 80)
    print("VERIFYING STAFF CODE MAPPINGS")
    print("=" * 80)

    # Collect all staff codes from CSV filenames
    csv_staff_codes = set()

    psl_files = glob.glob(os.path.join(CSV_DIR, "PSL_ZEN-*.csv"))
    rvz_files = glob.glob(os.path.join(CSV_DIR, "RVZ_ZEN-*.csv"))
    cmlog_files = glob.glob(os.path.join(CSV_DIR, "CMLog_*.csv"))

    for file_path in psl_files + rvz_files:
        filename = os.path.basename(file_path)

        rvz_match = re.search(r"RVZ_ZEN-([A-Z]+)", filename)
        psl_match = re.search(r"PSL_ZEN-([A-Z]+)", filename)

        if rvz_match:
            csv_staff_codes.add(f"ZEN-{rvz_match.group(1)}")
        elif psl_match:
            csv_staff_codes.add(f"ZEN-{psl_match.group(1)}")

    for file_path in cmlog_files:
        filename = os.path.basename(file_path)
        cmlog_match = re.search(r"CMLog_([A-Za-z0-9]+)\.csv", filename)
        if cmlog_match:
            csv_staff_codes.add(cmlog_match.group(1))

    print(f"Found {len(csv_staff_codes)} staff codes in CSV filenames:")

    # Check against database
    conn = get_db_connection()

    unmapped_codes = []
    for staff_code in sorted(csv_staff_codes):
        cursor = conn.execute(
            "SELECT user_id, mapping_type, confidence_level FROM staff_code_mapping WHERE staff_code = ?",
            (staff_code,),
        )
        row = cursor.fetchone()

        if row:
            print(
                f"   ✅ {staff_code} → user_id: {row[0]}, type: {row[1]}, confidence: {row[2]}"
            )
        else:
            print(f"   ❌ {staff_code} → NO MAPPING FOUND")
            unmapped_codes.append(staff_code)

    conn.close()

    if unmapped_codes:
        print(f"\n⚠️  {len(unmapped_codes)} unmapped staff codes:")
        for code in unmapped_codes:
            print(f"   - {code}")
    else:
        print("\n✅ All staff codes are properly mapped!")


def compare_patient_counts():
    """Compare ZMO patient count with database"""
    print("\n" + "=" * 80)
    print("COMPARING PATIENT COUNTS (ZMO_MAIN.csv)")
    print("=" * 80)

    zmo_file = os.path.join(CSV_DIR, "ZMO_MAIN.csv")

    if not os.path.exists(zmo_file):
        print("❌ ZMO_MAIN.csv not found")
        return

    # Count CSV rows (excluding header)
    try:
        df = pd.read_csv(zmo_file, encoding="utf-8", on_bad_lines="skip")
        # Filter out empty rows based on required columns
        df = df.dropna(subset=["Last", "First", "DOB"])
        csv_count = len(df)
        print(f"CSV Patients: {csv_count}")
    except Exception as e:
        print(f"❌ Error reading ZMO_MAIN.csv: {e}")
        return

    # Count database patients
    conn = get_db_connection()
    db_count = conn.execute("SELECT COUNT(*) as count FROM patients").fetchone()[0]
    print(f"DB Patients: {db_count}")

    status = "✅" if csv_count == db_count else "❌"
    print(f"{status} Patient count match: CSV={csv_count}, DB={db_count}")

    # Check for missing patients by name
    print("\nChecking for missing patients...")
    csv_patients = set()
    for _, row in df.iterrows():
        patient_id = normalize_patient_id(
            f"{row.get('Last', '')} {row.get('First', '')} {row.get('DOB', '')}"
        )
        if patient_id:
            csv_patients.add(patient_id)

    missing_count = 0
    for patient_id in csv_patients:
        exists = conn.execute(
            "SELECT 1 FROM patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()
        if not exists:
            missing_count += 1
            if missing_count <= 5:  # Show first 5
                print(f"   ❌ Missing: {patient_id}")

    if missing_count > 5:
        print(f"   ... and {missing_count - 5} more missing patients")
    elif missing_count == 0:
        print("   ✅ All patients found in database")

    conn.close()


def main():
    """Main comparison function"""
    print("\n" + "=" * 80)
    print("CSV vs DATABASE COMPARISON REPORT")
    print("Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)

    # Verify database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found: {DB_PATH}")
        return

    # Verify downloads directory exists
    if not os.path.exists(CSV_DIR):
        print(f"❌ Downloads directory not found: {CSV_DIR}")
        return

    # Run comparisons
    compare_staff_code_mappings()
    compare_patient_counts()
    compare_provider_tasks()
    compare_coordinator_tasks()

    print("\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
