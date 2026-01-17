#!/usr/bin/env python3
"""
Compare Active and Hospice patients between production.db and ZMO_MAIN.csv

This script:
1. Reads ZMO_MAIN.csv to get Active/Hospice patients
2. Reads production.db patient_panel for Active/Hospice patients
3. Creates a comprehensive comparison showing matches and differences
"""

import sqlite3
import csv
import sys
from pathlib import Path
from collections import defaultdict

# Paths
DB_PATH = "production.db"
CSV_PATH = "scripts/downloads/ZMO_MAIN.csv"
OUTPUT_PATH = "active_hospice_comparison_report.csv"


def normalize_dob(dob_str):
    """Normalize DOB to YYYY-MM-DD format."""
    if not dob_str:
        return ""
    dob_clean = dob_str.strip().replace('/', '-').strip()
    parts = dob_clean.split('-')
    if len(parts) != 3:
        return dob_clean
    if len(parts[0]) == 4:
        return dob_clean
    month, day, year = parts
    if len(month) == 1:
        month = '0' + month
    if len(day) == 1:
        day = '0' + day
    if len(year) == 2:
        year = '19' + year
    return f"{year}-{month}-{day}"


def read_zmo_main_csv(csv_path):
    """Read ZMO_MAIN.csv and extract Active/Hospice patients."""
    zmo_patients = {}

    with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        rows = list(reader)

        if not rows:
            return zmo_patients

        # Find header row
        header_idx = 0
        for i, row in enumerate(rows):
            if row and 'Pt Status' in str(row[0]):
                header_idx = i
                break

        header = rows[header_idx]
        data_rows = rows[header_idx + 1:]

        # Column indices based on the header analysis
        # 0: Pt Status, 3: Last, 4: First, 5: DOB, 12: Fac
        # 20: Recommended Reg Prov, 21: Assigned Reg Prov, 22: Assigned CM
        for row in data_rows:
            if not row or len(row) < 23:
                continue

            # Get patient status
            pt_status = row[0] if len(row) > 0 else ""
            pt_status = pt_status.strip().strip('"').upper() if pt_status else ""

            # Filter for Active and Hospice
            if not ('ACTIVE' in pt_status or 'HOSPICE' in pt_status):
                continue

            # Get patient info
            last_name = row[3] if len(row) > 3 else ""
            first_name = row[4] if len(row) > 4 else ""
            dob_raw = row[5] if len(row) > 5 else ""
            facility = row[12] if len(row) > 12 else ""
            provider_recommended = row[20] if len(row) > 20 else ""
            provider_assigned = row[21] if len(row) > 21 else ""
            cm = row[22] if len(row) > 22 else ""

            # Normalize
            last_name_clean = last_name.strip().strip('"').upper()
            first_name_clean = first_name.strip().strip('"').upper()
            dob_normalized = normalize_dob(dob_raw.strip().strip('"'))

            # Use assigned provider, fall back to recommended
            provider = provider_assigned.strip().strip('"') if provider_assigned.strip().strip('"') else provider_recommended.strip().strip('"')

            patient_key = f"{last_name_clean}_{first_name_clean}_{dob_normalized}"

            zmo_patients[patient_key] = {
                'status': pt_status,
                'last_name': last_name_clean,
                'first_name': first_name_clean,
                'dob': dob_normalized,
                'facility': facility.strip().strip('"'),
                'provider': provider,
                'coordinator': cm.strip().strip('"'),
                'source': 'ZMO_MAIN.csv'
            }

    return zmo_patients


def read_db_patients(db_path):
    """Read production.db for Active/Hospice patients."""
    db_patients = {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT
        patient_id,
        first_name,
        last_name,
        date_of_birth,
        status,
        facility,
        provider_name,
        coordinator_name,
        care_provider_name,
        care_coordinator_name
    FROM patient_panel
    WHERE LOWER(status) LIKE '%active%'
       OR LOWER(status) LIKE '%hospice%'
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    for row in rows:
        status = (row['status'] or '').strip().upper()

        last_name_clean = (row['last_name'] or '').strip().upper()
        first_name_clean = (row['first_name'] or '').strip().upper()
        dob_clean = (row['date_of_birth'] or '').strip()

        patient_key = f"{last_name_clean}_{first_name_clean}_{dob_clean}"

        provider = (row['provider_name'] or row['care_provider_name'] or '').strip()
        coordinator = (row['coordinator_name'] or row['care_coordinator_name'] or '').strip()

        db_patients[patient_key] = {
            'patient_id': (row['patient_id'] or '').strip(),
            'status': status,
            'last_name': last_name_clean,
            'first_name': first_name_clean,
            'dob': dob_clean,
            'facility': (row['facility'] or '').strip(),
            'provider': provider,
            'coordinator': coordinator,
            'source': 'production.db'
        }

    conn.close()

    return db_patients


def compare_patients(zmo_patients, db_patients):
    """Compare patients from both sources."""
    comparison = []

    all_keys = set(zmo_patients.keys()) | set(db_patients.keys())

    for key in sorted(all_keys):
        zmo = zmo_patients.get(key)
        db = db_patients.get(key)

        if zmo and db:
            comparison.append({
                'match_type': 'IN_BOTH',
                'last_name': zmo['last_name'],
                'first_name': zmo['first_name'],
                'dob': zmo['dob'],
                'zmo_status': zmo['status'],
                'db_status': db['status'],
                'zmo_facility': zmo['facility'],
                'db_facility': db['facility'],
                'zmo_provider': zmo['provider'],
                'db_provider': db['provider'],
                'zmo_coordinator': zmo['coordinator'],
                'db_coordinator': db['coordinator'],
                'db_patient_id': db.get('patient_id', ''),
                'provider_match': zmo['provider'].strip().lower() == db['provider'].strip().lower() if zmo['provider'] and db['provider'] else None,
                'coordinator_match': zmo['coordinator'].strip().lower() == db['coordinator'].strip().lower() if zmo['coordinator'] and db['coordinator'] else None,
            })
        elif zmo:
            comparison.append({
                'match_type': 'ONLY_IN_ZMO',
                'last_name': zmo['last_name'],
                'first_name': zmo['first_name'],
                'dob': zmo['dob'],
                'zmo_status': zmo['status'],
                'db_status': '',
                'zmo_facility': zmo['facility'],
                'db_facility': '',
                'zmo_provider': zmo['provider'],
                'db_provider': '',
                'zmo_coordinator': zmo['coordinator'],
                'db_coordinator': '',
                'db_patient_id': '',
                'provider_match': None,
                'coordinator_match': None,
            })
        else:
            comparison.append({
                'match_type': 'ONLY_IN_DB',
                'last_name': db['last_name'],
                'first_name': db['first_name'],
                'dob': db['dob'],
                'zmo_status': '',
                'db_status': db['status'],
                'zmo_facility': '',
                'db_facility': db['facility'],
                'zmo_provider': '',
                'db_provider': db['provider'],
                'zmo_coordinator': '',
                'db_coordinator': db['coordinator'],
                'db_patient_id': db.get('patient_id', ''),
                'provider_match': None,
                'coordinator_match': None,
            })

    return comparison


def print_summary(zmo_patients, db_patients, comparison):
    """Print summary statistics."""
    print("\n" + "=" * 80)
    print("PATIENT COMPARISON SUMMARY")
    print("=" * 80)

    print(f"\nZMO_MAIN.csv Active/Hospice Patients: {len(zmo_patients)}")
    print(f"production.db Active/Hospice Patients: {len(db_patients)}")

    # Count match types
    in_both = sum(1 for c in comparison if c['match_type'] == 'IN_BOTH')
    only_zmo = sum(1 for c in comparison if c['match_type'] == 'ONLY_IN_ZMO')
    only_db = sum(1 for c in comparison if c['match_type'] == 'ONLY_IN_DB')

    print(f"\n--- Match Summary ---")
    print(f"Patients in BOTH sources: {in_both}")
    print(f"Patients ONLY in ZMO_MAIN.csv: {only_zmo}")
    print(f"Patients ONLY in production.db: {only_db}")

    # Count by status
    zmo_active = sum(1 for p in zmo_patients.values() if 'ACTIVE' in p['status'])
    zmo_hospice = sum(1 for p in zmo_patients.values() if 'HOSPICE' in p['status'])
    db_active = sum(1 for p in db_patients.values() if 'ACTIVE' in p['status'])
    db_hospice = sum(1 for p in db_patients.values() if 'HOSPICE' in p['status'])

    print(f"\n--- By Status ---")
    print(f"ZMO_MAIN.csv - Active: {zmo_active}, Hospice: {zmo_hospice}")
    print(f"production.db - Active: {db_active}, Hospice: {db_hospice}")

    # Count assignment mismatches
    provider_mismatch = 0
    coordinator_mismatch = 0
    missing_provider_in_zmo = 0
    missing_provider_in_db = 0
    missing_coordinator_in_zmo = 0
    missing_coordinator_in_db = 0

    for c in comparison:
        if c['match_type'] == 'IN_BOTH':
            zmo_prov = c['zmo_provider'].strip().lower()
            db_prov = c['db_provider'].strip().lower()

            if zmo_prov and db_prov:
                if zmo_prov != db_prov:
                    provider_mismatch += 1
            elif not zmo_prov and db_prov:
                missing_provider_in_zmo += 1
            elif zmo_prov and not db_prov:
                missing_provider_in_db += 1

            zmo_cm = c['zmo_coordinator'].strip().lower()
            db_cm = c['db_coordinator'].strip().lower()

            if zmo_cm and db_cm:
                if zmo_cm != db_cm:
                    coordinator_mismatch += 1
            elif not zmo_cm and db_cm:
                missing_coordinator_in_zmo += 1
            elif zmo_cm and not db_cm:
                missing_coordinator_in_db += 1

    print(f"\n--- Assignment Comparison (for {in_both} patients in both sources) ---")
    print(f"Provider mismatches: {provider_mismatch}")
    print(f"  - Missing provider in ZMO: {missing_provider_in_zmo}")
    print(f"  - Missing provider in DB: {missing_provider_in_db}")
    print(f"Coordinator mismatches: {coordinator_mismatch}")
    print(f"  - Missing coordinator in ZMO: {missing_coordinator_in_zmo}")
    print(f"  - Missing coordinator in DB: {missing_coordinator_in_db}")


def write_comparison_csv(comparison, output_path):
    """Write comparison to CSV file."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Match Type',
            'Last Name',
            'First Name',
            'DOB',
            'ZMO Status',
            'DB Status',
            'ZMO Facility',
            'DB Facility',
            'ZMO Provider',
            'DB Provider',
            'Provider Match',
            'ZMO Coordinator',
            'DB Coordinator',
            'Coordinator Match',
            'DB Patient ID'
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for c in comparison:
            # Determine provider/coordinator match status
            prov_match = ''
            if c['match_type'] == 'IN_BOTH':
                if c['zmo_provider'] and c['db_provider']:
                    prov_match = 'MATCH' if c['zmo_provider'].lower() == c['db_provider'].lower() else 'MISMATCH'
                elif c['zmo_provider'] and not c['db_provider']:
                    prov_match = 'ONLY_IN_ZMO'
                elif not c['zmo_provider'] and c['db_provider']:
                    prov_match = 'ONLY_IN_DB'
                else:
                    prov_match = 'BOTH_EMPTY'

            coord_match = ''
            if c['match_type'] == 'IN_BOTH':
                if c['zmo_coordinator'] and c['db_coordinator']:
                    coord_match = 'MATCH' if c['zmo_coordinator'].lower() == c['db_coordinator'].lower() else 'MISMATCH'
                elif c['zmo_coordinator'] and not c['db_coordinator']:
                    coord_match = 'ONLY_IN_ZMO'
                elif not c['zmo_coordinator'] and c['db_coordinator']:
                    coord_match = 'ONLY_IN_DB'
                else:
                    coord_match = 'BOTH_EMPTY'

            writer.writerow({
                'Match Type': c['match_type'],
                'Last Name': c['last_name'],
                'First Name': c['first_name'],
                'DOB': c['dob'],
                'ZMO Status': c['zmo_status'],
                'DB Status': c['db_status'],
                'ZMO Facility': c['zmo_facility'],
                'DB Facility': c['db_facility'],
                'ZMO Provider': c['zmo_provider'],
                'DB Provider': c['db_provider'],
                'Provider Match': prov_match,
                'ZMO Coordinator': c['zmo_coordinator'],
                'DB Coordinator': c['db_coordinator'],
                'Coordinator Match': coord_match,
                'DB Patient ID': c['db_patient_id']
            })

    print(f"\nComparison report written to: {output_path}")


def main():
    print("Reading ZMO_MAIN.csv...")
    zmo_patients = read_zmo_main_csv(CSV_PATH)
    print(f"Found {len(zmo_patients)} Active/Hospice patients in ZMO_MAIN.csv")

    print("\nReading production.db...")
    db_patients = read_db_patients(DB_PATH)
    print(f"Found {len(db_patients)} Active/Hospice patients in production.db")

    print("\nComparing patients...")
    comparison = compare_patients(zmo_patients, db_patients)

    print_summary(zmo_patients, db_patients, comparison)

    write_comparison_csv(comparison, OUTPUT_PATH)


if __name__ == "__main__":
    main()
