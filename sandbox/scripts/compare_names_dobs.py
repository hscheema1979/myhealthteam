import sqlite3
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / 'production.db'
FILTERED_FILE = ROOT / 'scripts' / 'names_dobs_from_tables_filtered.txt'
COMPARISON_OUTPUT = ROOT / 'scripts' / 'comparison_results.txt'

def parse_dob(dob_str):
    """Parse DOB string and return standardized format"""
    try:
        # Handle various date formats
        if '/' in dob_str:
            parts = dob_str.split('/')
        elif '-' in dob_str:
            parts = dob_str.split('-')
        else:
            return None
            
        if len(parts) != 3:
            return None
            
        mm, dd, yy = int(parts[0]), int(parts[1]), int(parts[2])
        if yy < 100:
            yy = 2000 + yy if yy <= (datetime.now().year % 100) else 1900 + yy
        return datetime(yy, mm, dd).strftime('%m/%d/%Y')
    except:
        return None

def normalize_name(name):
    """Normalize name for comparison"""
    # Convert to uppercase and remove extra spaces
    name = re.sub(r'\s+', ' ', name.upper().strip())
    # Remove trailing punctuation
    name = name.rstrip('.,;:')
    return name

def load_filtered_names():
    """Load filtered names+DOBs from the text file"""
    names_dobs = set()
    if not FILTERED_FILE.exists():
        print(f"ERROR: Filtered file not found at {FILTERED_FILE}")
        return names_dobs
        
    with open(FILTERED_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    # Skip first line (count header)
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) != 2:
            continue
        name, dob = parts[0], parts[1]
        normalized_name = normalize_name(name)
        normalized_dob = parse_dob(dob)
        if normalized_name and normalized_dob:
            names_dobs.add((normalized_name, normalized_dob))
    return names_dobs

def load_patients_names():
    """Load names+DOBs from the patients table"""
    names_dobs = set()
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        return names_dobs
        
    conn = sqlite3.connect(str(DB_PATH))
    try:
        # Query patients table for name and DOB
        cur = conn.execute("SELECT first_name, last_name, date_of_birth FROM patients")
        for row in cur.fetchall():
            first_name, last_name, dob = row[0], row[1], row[2]
            if not first_name or not last_name or not dob:
                continue
            # Combine first and last name
            full_name = f"{last_name} {first_name}"
            normalized_name = normalize_name(full_name)
            normalized_dob = parse_dob(dob)
            if normalized_name and normalized_dob:
                names_dobs.add((normalized_name, normalized_dob))
    finally:
        conn.close()
    return names_dobs

def compare_sets(source_set, patients_set):
    """Compare the two sets and return results"""
    matches = source_set.intersection(patients_set)
    missing_from_patients = source_set.difference(patients_set)
    extra_in_patients = patients_set.difference(source_set)
    return matches, missing_from_patients, extra_in_patients

def write_results(matches, missing_from_patients, extra_in_patients):
    """Write comparison results to file"""
    with open(COMPARISON_OUTPUT, 'w', encoding='utf-8') as f:
        f.write("COMPARISON RESULTS\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Total entries in source data: {len(missing_from_patients) + len(matches)}\n")
        f.write(f"Total entries in patients table: {len(extra_in_patients) + len(matches)}\n")
        f.write(f"Matches (in both): {len(matches)}\n")
        f.write(f"Missing from patients table: {len(missing_from_patients)}\n")
        f.write(f"Extra in patients table: {len(extra_in_patients)}\n\n")
        
        f.write("MATCHES (in both source and patients table):\n")
        f.write("-" * 40 + "\n")
        for name, dob in sorted(matches):
            f.write(f"{name}\t{dob}\n")
        f.write("\n")
        
        f.write("MISSING FROM PATIENTS TABLE (in source but not in patients):\n")
        f.write("-" * 40 + "\n")
        for name, dob in sorted(missing_from_patients):
            f.write(f"{name}\t{dob}\n")
        f.write("\n")
        
        f.write("EXTRA IN PATIENTS TABLE (in patients but not in source):\n")
        f.write("-" * 40 + "\n")
        for name, dob in sorted(extra_in_patients):
            f.write(f"{name}\t{dob}\n")
        f.write("\n")

def main():
    print("Loading filtered names+DOBs from source data...")
    source_names = load_filtered_names()
    print(f"Loaded {len(source_names)} unique names+DOBs from source data")
    
    print("Loading names+DOBs from patients table...")
    patients_names = load_patients_names()
    print(f"Loaded {len(patients_names)} unique names+DOBs from patients table")
    
    print("Comparing sets...")
    matches, missing_from_patients, extra_in_patients = compare_sets(source_names, patients_names)
    
    print("Writing results...")
    write_results(matches, missing_from_patients, extra_in_patients)
    
    print(f"Comparison complete. Results written to {COMPARISON_OUTPUT}")
    print(f"Matches: {len(matches)}")
    print(f"Missing from patients: {len(missing_from_patients)}")
    print(f"Extra in patients: {len(extra_in_patients)}")

if __name__ == '__main__':
    main()