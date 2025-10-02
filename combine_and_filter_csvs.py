import pandas as pd
import os
import glob
import re
from datetime import datetime

def normalize_date(date_str):
    """
    Normalize date to YYYY-MM-DD format
    Handles MM/DD/YYYY, MM/DD/YY, and existing YYYY-MM-DD formats
    """
    if not date_str or pd.isna(date_str):
        return None
        
    date_str = str(date_str).strip()
    
    # Handle MM/DD/YYYY format
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        parts = date_str.split('/')
        month, day, year = parts[0].zfill(2), parts[1].zfill(2), parts[2]
        return f"{year}-{month}-{day}"
    
    # Handle MM/DD/YY format
    if re.match(r'^\d{1,2}/\d{1,2}/\d{2}$', date_str):
        parts = date_str.split('/')
        month, day, year = parts[0].zfill(2), parts[1].zfill(2), f"20{parts[2]}"
        return f"{year}-{month}-{day}"
    
    # Already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
        
    return None

def normalize_patient_name(patient_name):
    """
    Normalize patient name by removing ZEN- prefix and cleaning up formatting
    """
    if not patient_name or pd.isna(patient_name):
        return None
    
    normalized = str(patient_name).strip()
    
    # Remove ZEN- prefix (case insensitive)
    normalized = re.sub(r'^ZEN-', '', normalized, flags=re.IGNORECASE)
    
    # Remove extra commas and spaces
    normalized = normalized.replace(', ', ' ')
    normalized = normalized.replace(',', ' ')
    
    # Replace multiple spaces with single space
    while '  ' in normalized:
        normalized = normalized.replace('  ', ' ')
    
    return normalized.strip()

def apply_data_normalization(df, file_type):
    """
    Apply data normalization based on file type
    """
    # Common date columns that need normalization
    date_columns = ['Date', 'Task Date', 'Completion Date', 'Created Date', 'Modified Date', 'DOS']
    
    # Normalize date columns
    for col in date_columns:
        if col in df.columns:
            print(f"  Normalizing date column: {col}")
            df[col] = df[col].apply(normalize_date)
    
    # File-type specific normalizations
    if file_type == 'ZMO':
        # Patient name normalization for ZMO files
        patient_name_columns = ['Patient Name', 'PatientName', 'Name', 'Patient', 'Patient Last, First DOB']
        for col in patient_name_columns:
            if col in df.columns:
                print(f"  Normalizing patient names in column: {col}")
                df[col] = df[col].apply(normalize_patient_name)
    
    elif file_type == 'CMLog':
        # Coordinator task specific normalizations
        if 'Task Date' in df.columns:
            print(f"  Normalizing CMLog Task Date")
            df['Task Date'] = df['Task Date'].apply(normalize_date)
    
    elif file_type in ['PSL', 'RVZ']:
        # Provider task specific normalizations
        if 'DOS' in df.columns:
            print(f"  Normalizing {file_type} DOS (Date of Service) column")
            df['DOS'] = df['DOS'].apply(normalize_date)
        
        # Patient name normalization for provider files
        patient_name_columns = ['Patient Name', 'PatientName', 'Name', 'Patient', 'Patient Last, First DOB']
        for col in patient_name_columns:
            if col in df.columns:
                print(f"  Normalizing patient names in {file_type} column: {col}")
                df[col] = df[col].apply(normalize_patient_name)
    
    return df

def combine_and_filter_csvs(downloads_folder, file_type, essential_columns, output_filename):
    """
    Combines CSV files of a specific type while filtering out rows with empty essential columns.
    
    Args:
        downloads_folder (str): Path to the downloads folder
        file_type (str): Type prefix (PSL, CMLog, RVZ)
        essential_columns (list): List of column names that must not be empty
        output_filename (str): Name of the output combined file
    
    Returns:
        dict: Statistics about the combination process
    """
    
    # Find all files of the specified type
    pattern = os.path.join(downloads_folder, f"{file_type}_*.csv")
    files = glob.glob(pattern)
    
    if not files:
        print(f"No {file_type} files found in {downloads_folder}")
        return None
    
    print(f"\nProcessing {len(files)} {file_type} files...")
    
    all_dataframes = []
    total_rows_before = 0
    total_rows_after = 0
    files_processed = 0
    
    for file_path in files:
        filename = os.path.basename(file_path)
        print(f"  Reading {filename}...")
        
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Clean up column names (remove newlines and extra spaces)
            df.columns = df.columns.str.strip().str.replace('\n', ' ')
            
            # Apply data normalization based on file type
            df = apply_data_normalization(df, file_type)
            
            rows_before = len(df)
            total_rows_before += rows_before
            
            # Filter out rows where essential columns are empty
            # Create a mask for rows that have non-empty values in all essential columns
            mask = pd.Series([True] * len(df))
            
            for col in essential_columns:
                if col in df.columns:
                    # Check for empty, null, or whitespace-only values
                    col_mask = (
                        df[col].notna() & 
                        (df[col].astype(str).str.strip() != '') &
                        (df[col].astype(str).str.strip() != 'nan')
                    )
                    mask = mask & col_mask
                else:
                    print(f"    Warning: Column '{col}' not found in {filename}")
            
            # Apply the filter
            df_filtered = df[mask].copy()
            rows_after = len(df_filtered)
            total_rows_after += rows_after
            
            rows_excluded = rows_before - rows_after
            print(f"    Rows before: {rows_before}, after: {rows_after}, excluded: {rows_excluded}")
            
            # Add source file column for tracking
            df_filtered['source_file'] = filename
            
            all_dataframes.append(df_filtered)
            files_processed += 1
            
        except Exception as e:
            print(f"    Error processing {filename}: {str(e)}")
            continue
    
    if not all_dataframes:
        print(f"No valid data found in {file_type} files")
        return None
    
    # Combine all dataframes
    print(f"  Combining {len(all_dataframes)} dataframes...")
    combined_df = pd.concat(all_dataframes, ignore_index=True, sort=False)
    
    # Save the combined file
    output_path = os.path.join(downloads_folder, output_filename)
    combined_df.to_csv(output_path, index=False)
    
    stats = {
        'file_type': file_type,
        'files_processed': files_processed,
        'total_files_found': len(files),
        'total_rows_before': total_rows_before,
        'total_rows_after': total_rows_after,
        'total_rows_excluded': total_rows_before - total_rows_after,
        'output_file': output_path,
        'output_filename': output_filename,
        'final_combined_rows': len(combined_df)
    }
    
    print(f"  ✓ Combined {file_type} files saved to: {output_filename}")
    print(f"  ✓ Total rows excluded: {stats['total_rows_excluded']}")
    
    return stats

def main():
    """Main function to process all three file types"""
    
    downloads_folder = "downloads"
    
    # Define essential columns for each file type
    file_configs = {
        'PSL': {
            'essential_columns': ['Prov', 'DOS', 'Patient Last, First DOB'],
            'output_filename': 'psl_combined_filtered.csv'
        },
        'CMLog': {
            'essential_columns': ['Staff', 'Date Only', 'Pt Name'],
            'output_filename': 'cmlog_combined_filtered.csv'
        },
        'RVZ': {
            'essential_columns': ['Provider', 'Date Only', 'Pt Name'],
            'output_filename': 'rvz_combined_filtered.csv'
        }
    }
    
    print("=" * 60)
    print("CSV COMBINATION AND FILTERING TOOL")
    print("=" * 60)
    print(f"Processing files from: {downloads_folder}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_stats = []
    
    # Process each file type
    for file_type, config in file_configs.items():
        stats = combine_and_filter_csvs(
            downloads_folder=downloads_folder,
            file_type=file_type,
            essential_columns=config['essential_columns'],
            output_filename=config['output_filename']
        )
        
        if stats:
            all_stats.append(stats)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    
    for stats in all_stats:
        print(f"\n{stats['file_type']} Files:")
        print(f"  Files processed: {stats['files_processed']}/{stats['total_files_found']}")
        print(f"  Rows before filtering: {stats['total_rows_before']:,}")
        print(f"  Rows after filtering: {stats['total_rows_after']:,}")
        print(f"  Rows excluded: {stats['total_rows_excluded']:,}")
        print(f"  Exclusion rate: {(stats['total_rows_excluded']/stats['total_rows_before']*100):.1f}%")
        print(f"  Output file: {stats['output_filename']}")
    
    total_excluded = sum(s['total_rows_excluded'] for s in all_stats)
    total_before = sum(s['total_rows_before'] for s in all_stats)
    
    print(f"\nOverall:")
    print(f"  Total rows excluded across all files: {total_excluded:,}")
    print(f"  Overall exclusion rate: {(total_excluded/total_before*100):.1f}%")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()