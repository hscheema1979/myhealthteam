# CMLog Data Import Script
# Priority: P0 - URGENT
# Purpose: Import CMLog data from downloads/cmlog.csv into coordinator_tasks table

Write-Host "========================================="
Write-Host "  CMLOG DATA IMPORT TO COORDINATOR_TASKS"
Write-Host "========================================="

# Check if we're in the correct directory
if (!(Test-Path "production.db")) {
    Write-Host "ERROR: production.db not found. Make sure you're running from the root Streamlit directory." -ForegroundColor Red
    exit 1
}

# Check if CMLog data file exists
if (!(Test-Path "downloads\cmlog.csv")) {
    Write-Host "ERROR: downloads\cmlog.csv not found. Please ensure the CMLog data has been downloaded." -ForegroundColor Red
    exit 1
}

try {
    # Step 1: Clear existing coordinator tasks
    Write-Host "Clearing existing coordinator_tasks data..." -ForegroundColor Yellow
    python -c @"
import sqlite3
try:
    conn = sqlite3.connect('production.db')
    cursor = conn.cursor()
    
    # Get current counts before clearing
    task_count = cursor.execute('SELECT COUNT(*) FROM coordinator_tasks').fetchone()[0]
    summary_count = cursor.execute('SELECT COUNT(*) FROM coordinator_monthly_summary').fetchone()[0]
    
    print(f'Current coordinator_tasks records: {task_count}')
    print(f'Current coordinator_monthly_summary records: {summary_count}')
    
    # Clear existing data
    cursor.execute('DELETE FROM coordinator_tasks')
    cursor.execute('DELETE FROM coordinator_monthly_summary')
    conn.commit()
    
    print('Successfully cleared existing data')
    
except Exception as e:
    print(f'ERROR clearing data: {e}')
    exit(1)
finally:
    if 'conn' in locals():
        conn.close()
"@

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to clear existing data" -ForegroundColor Red
        exit 1
    }

    Write-Host "✓ Existing data cleared successfully" -ForegroundColor Green

    # Step 2: Import CMLog data
    Write-Host "Importing CMLog data..." -ForegroundColor Yellow
    Write-Host "This may take several minutes for large datasets..." -ForegroundColor Cyan
    
    python -c @"
import pandas as pd
import sqlite3
from datetime import datetime
import sys

try:
    # Read CMLog data
    print('Reading CMLog data from downloads/cmlog.csv...')
    df = pd.read_csv('downloads/cmlog.csv')
    print(f'Total rows in CMLog: {len(df)}')

    # Clean data - remove placeholder rows and invalid entries
    print('Cleaning data...')
    original_count = len(df)
    
    # Remove placeholder rows
    df = df[df['Type'] != 'Place holder.  Do not change this row data']
    
    # Remove rows with missing critical data
    df = df[df['Staff'].notna()]
    df = df[df['Pt Name'].notna()]
    
    # Remove rows with no time logged
    df = df[df['Mins B'].notna()]
    df = df[df['Mins B'] != 0]
    df = df[df['Mins B'] > 0]
    
    cleaned_count = len(df)
    print(f'Rows after cleaning: {cleaned_count} (removed {original_count - cleaned_count} invalid rows)')

    # Connect to database
    print('Connecting to database...')
    conn = sqlite3.connect('production.db')
    conn.row_factory = sqlite3.Row

    # Track statistics
    processed_count = 0
    imported_count = 0
    coordinator_matches = 0
    patient_matches = 0
    errors = []

    # Process each row
    print('Processing CMLog entries...')
    for idx, row in df.iterrows():
        try:
            processed_count += 1
            
            # Get coordinator info from staff code
            staff_query = '''
                SELECT u.user_id, u.full_name, c.coordinator_id
                FROM users u
                JOIN coordinators c ON u.user_id = c.user_id
                WHERE u.staff_code = ? OR u.full_name LIKE ?
            '''
            
            # Try exact staff code match first, then fuzzy name match
            staff_param = str(row['Staff']).strip()
            name_param = f"%{staff_param}%"
            coordinator_info = conn.execute(staff_query, (staff_param, name_param)).fetchone()

            if coordinator_info:
                coordinator_matches += 1
                user_id = coordinator_info['user_id']
                coordinator_name = coordinator_info['full_name']
                coordinator_id = coordinator_info['coordinator_id']

                # Try to match patient
                patient_id = None
                patient_name = str(row['Pt Name']).strip()
                
                if pd.notna(row.get('Last, First DOB')):
                    patient_query = '''
                        SELECT patient_id FROM patients
                        WHERE last_first_dob = ?
                    '''
                    patient_match = conn.execute(patient_query, (row['Last, First DOB'],)).fetchone()
                    if patient_match:
                        patient_id = patient_match['patient_id']
                        patient_matches += 1

                # Parse duration
                try:
                    duration = float(row['Mins B'])
                    if duration > 0:  # Only import tasks with actual time logged
                        # Insert coordinator task
                        insert_query = '''
                            INSERT INTO coordinator_tasks
                            (patient_id, patient_name, coordinator_id, user_id, coordinator_name,
                             task_date, duration_minutes, task_type, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        '''
                        
                        task_date = str(row['Date Only']).strip() if pd.notna(row['Date Only']) else None
                        task_type = str(row['Type']).strip() if pd.notna(row['Type']) else 'General'
                        notes = str(row['Notes']).strip() if pd.notna(row['Notes']) else ''

                        conn.execute(insert_query, (
                            patient_id,
                            patient_name,
                            coordinator_id,
                            user_id,
                            coordinator_name,
                            task_date,
                            int(duration),
                            task_type,
                            notes
                        ))
                        
                        imported_count += 1
                        
                except (ValueError, TypeError) as e:
                    errors.append(f'Row {idx}: Invalid duration value: {row["Mins B"]}')
                    continue
            else:
                errors.append(f'Row {idx}: No coordinator found for staff code: {staff_param}')

            # Progress reporting and periodic commits
            if processed_count % 1000 == 0:
                print(f'Processed {processed_count}/{cleaned_count} rows... (Imported: {imported_count})')
                conn.commit()

        except Exception as e:
            errors.append(f'Row {idx}: {str(e)}')
            continue

    # Final commit
    conn.commit()
    
    # Final statistics
    print(f'\\n=== IMPORT COMPLETE ===')
    print(f'Total rows processed: {processed_count}')
    print(f'Successfully imported: {imported_count}')
    print(f'Coordinator matches: {coordinator_matches}')
    print(f'Patient matches: {patient_matches}')
    print(f'Errors encountered: {len(errors)}')
    
    if errors and len(errors) <= 10:
        print(f'\\nFirst few errors:')
        for error in errors[:10]:
            print(f'  - {error}')
    elif len(errors) > 10:
        print(f'\\nFirst 10 errors (of {len(errors)}):')
        for error in errors[:10]:
            print(f'  - {error}')
    
    # Verify import
    final_count = conn.execute('SELECT COUNT(*) FROM coordinator_tasks').fetchone()[0]
    print(f'\\nFinal coordinator_tasks count: {final_count}')
    
    if final_count == 0:
        print('WARNING: No tasks were imported. Check staff code mappings and data format.')
        sys.exit(1)

except Exception as e:
    print(f'CRITICAL ERROR during import: {e}')
    sys.exit(1)
    
finally:
    if 'conn' in locals():
        conn.close()
"@

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: CMLog data import failed" -ForegroundColor Red
        exit 1
    }

    Write-Host "✓ CMLog data import completed successfully" -ForegroundColor Green

    # Step 3: Final validation
    Write-Host "Performing final validation..." -ForegroundColor Yellow
    
    python -c @"
import sqlite3

try:
    conn = sqlite3.connect('production.db')
    
    # Get final counts
    total_tasks = conn.execute('SELECT COUNT(*) FROM coordinator_tasks').fetchone()[0]
    unique_coordinators = conn.execute('SELECT COUNT(DISTINCT coordinator_id) FROM coordinator_tasks').fetchone()[0]
    unique_patients = conn.execute('SELECT COUNT(DISTINCT patient_id) FROM coordinator_tasks WHERE patient_id IS NOT NULL').fetchone()[0]
    total_minutes = conn.execute('SELECT SUM(duration_minutes) FROM coordinator_tasks').fetchone()[0]
    
    print(f'=== FINAL VALIDATION ===')
    print(f'Total tasks imported: {total_tasks}')
    print(f'Unique coordinators: {unique_coordinators}')
    print(f'Matched patients: {unique_patients}')
    print(f'Total minutes logged: {total_minutes}')
    
    if total_tasks == 0:
        print('ERROR: No tasks were imported!')
        exit(1)
    
    print('✓ Import validation successful')
    
except Exception as e:
    print(f'ERROR during validation: {e}')
    exit(1)
finally:
    conn.close()
"@

    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Import validation failed" -ForegroundColor Red
        exit 1
    }

    Write-Host "✓ All validations passed" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================="
    Write-Host "  CMLOG IMPORT COMPLETED SUCCESSFULLY"
    Write-Host "========================================="
    Write-Host ""
    Write-Host "Next step: Run 6_generate_coordinator_summaries.ps1" -ForegroundColor Cyan

}
catch {
    Write-Host "CRITICAL ERROR: Script execution failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}