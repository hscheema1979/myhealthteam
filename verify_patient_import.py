"""
Patient Import Verification Script
Compares ZMO_Main.csv source data with database to verify import accuracy
"""
import pandas as pd
import sqlite3
import sys

def normalize_patient_id(patient_str):
    """Match the normalization in transform script"""
    if pd.isna(patient_str) or not patient_str:
        return None
    
    patient_str = str(patient_str).strip()
    
    prefixes = [
        'BLESSEDCARE-', 'BLEESSEDCARE-', 'BLESSEDCARE ', 'BLEESSEDCARE ',
        'ZEN-', 'PM-', 'ZMN-', '3PR-', '3PR '
    ]
    for prefix in prefixes:
        if patient_str.startswith(prefix):
            patient_str = patient_str[len(prefix):]
    
    patient_str = patient_str.replace(', ', ' ').replace(',', ' ')
    patient_str = patient_str.replace('  ', ' ').strip()
    
    return patient_str

print("="*70)
print("PATIENT IMPORT VERIFICATION")
print("="*70)

# Read ZMO source
print("\n1. Loading ZMO_Main.csv...")
zmo = pd.read_csv('downloads/ZMO_MAIN.csv')
print(f"   Total rows in ZMO: {len(zmo)}")

# Normalize patient IDs in ZMO
zmo['normalized_id'] = zmo['LAST FIRST DOB'].apply(normalize_patient_id)
zmo_clean = zmo[zmo['normalized_id'].notna()].copy()
print(f"   Valid patient records: {len(zmo_clean)}")
print(f"   Unique normalized IDs: {zmo_clean['normalized_id'].nunique()}")
print(f"   Duplicates in source: {len(zmo_clean) - zmo_clean['normalized_id'].nunique()}")

# Read database
print("\n2. Loading database patients...")
conn = sqlite3.connect('production.db')
db = pd.read_sql('SELECT patient_id, first_name, last_name, date_of_birth, status, facility FROM patients', conn)
print(f"   Total rows in DB: {len(db)}")

# Count verification
print("\n" + "="*70)
print("COUNT COMPARISON")
print("="*70)
print(f"ZMO valid records:        {len(zmo_clean)}")
print(f"Database patient records: {len(db)}")
print(f"Expected (with 6 dups):   {len(zmo_clean)}")
print(f"Match: {'✅ YES' if len(db) == len(zmo_clean) else '❌ NO'}")

# Sample comparison
print("\n" + "="*70)
print("SAMPLE DATA COMPARISON (First 10 records)")
print("="*70)
print("\nZMO SOURCE:")
print(zmo_clean[['normalized_id', 'First', 'Last', 'DOB', 'Pt Status']].head(10).to_string(index=False))

print("\nDATABASE:")
print(db[['patient_id', 'first_name', 'last_name', 'date_of_birth', 'status']].head(10).to_string(index=False))

# Check duplicates in database
print("\n" + "="*70)
print("DUPLICATE HANDLING VERIFICATION")
print("="*70)
duplicates = db[db['patient_id'].str.contains('-[0-9]$', regex=True, na=False)]
print(f"Found {len(duplicates)} duplicate patient_ids with suffixes:")
if len(duplicates) > 0:
    print(duplicates[['patient_id', 'first_name', 'last_name']].to_string(index=False))

# Spot check specific patients
print("\n" + "="*70)
print("SPOT CHECK: Verify specific patient data matches")
print("="*70)

# Pick first 3 patients from ZMO
for idx in range(min(3, len(zmo_clean))):
    zmo_row = zmo_clean.iloc[idx]
    norm_id = zmo_row['normalized_id']
    
    # Find in database (might have -1 suffix if duplicate)
    db_match = db[(db['patient_id'] == norm_id) | (db['patient_id'].str.startswith(norm_id + '-'))]
    
    if len(db_match) > 0:
        db_row = db_match.iloc[0]
        print(f"\n✅ Patient {idx+1}: {norm_id}")
        print(f"   ZMO: {zmo_row['First']} {zmo_row['Last']} | DOB: {zmo_row['DOB']}")
        print(f"   DB:  {db_row['first_name']} {db_row['last_name']} | DOB: {db_row['date_of_birth']}")
        
        # Check if names match
        first_match = str(zmo_row['First']).strip() == str(db_row['first_name']).strip()
        last_match = str(zmo_row['Last']).strip() == str(db_row['last_name']).strip()
        
        if first_match and last_match:
            print(f"   Names: ✅ MATCH")
        else:
            print(f"   Names: ❌ MISMATCH!")
    else:
        print(f"\n❌ Patient {idx+1}: {norm_id} NOT FOUND in database!")

# Check all 4 patient tables
print("\n" + "="*70)
print("ALL PATIENT TABLES")
print("="*70)
tables = {
    'patients': 'SELECT COUNT(*) as count FROM patients',
    'patient_panel': 'SELECT COUNT(*) as count FROM patient_panel',
    'patient_assignments': 'SELECT COUNT(*) as count FROM patient_assignments',
    'onboarding_patients': 'SELECT COUNT(*) as count FROM onboarding_patients'
}

for table_name, query in tables.items():
    count = pd.read_sql(query, conn).iloc[0]['count']
    print(f"{table_name:25} {count:6} rows")

conn.close()

print("\n" + "="*70)
print("VERIFICATION COMPLETE")
print("="*70)
