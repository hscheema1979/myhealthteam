import pandas as pd
import argparse
import os
import csv
import re

def merge_google_headers(rows):
    """
    Detects and merges multi-line headers from Google Sheets CSV export.
    Returns: (merged_headers, first_data_row_idx)
    """
    if not rows:
        return [], 0

    # Find the row with maximum columns (likely the real header row)
    max_cols = 0
    max_row_idx = 0
    for i, row in enumerate(rows[:10]):  # Check first 10 rows
        if len(row) > max_cols:
            max_cols = len(row)
            max_row_idx = i

    # If first row has the most columns, it's likely already proper headers
    if max_row_idx == 0:
        return rows[0], 1

    # Initialize header_parts with empty strings up to max_cols
    header_parts = [''] * max_cols

    # Merge each row's data into the headers
    for i in range(max_row_idx + 1):
        row = rows[i]
        for j, field in enumerate(row):
            if j >= max_cols:
                break
            # Merge field text
            existing = header_parts[j] if j < len(header_parts) else ""
            new_text = str(field).strip()
            if existing:
                # Combine: remove overlapping parts and clean whitespace
                combined = f"{existing} {new_text}" if new_text and new_text not in existing else existing
                header_parts[j] = combined
            else:
                header_parts[j] = new_text

    # Clean merged headers: remove embedded newlines, extra spaces
    final_headers = []
    for h in header_parts:
        if h:
            cleaned = re.sub(r'\s+', ' ', str(h))  # Collapse whitespace
            cleaned = cleaned.replace('\n', ' ').replace('\r', ' ')  # Remove newlines
            cleaned = cleaned.strip()
            final_headers.append(cleaned)
        else:
            final_headers.append(f"Unnamed_{len(final_headers)}")

    return final_headers, max_row_idx + 1

def clean_csv(input_file, output_file=None, max_columns=None, skip_empty_columns=True):
    """
    Clean a CSV file by removing unnamed columns, empty columns, and optionally limiting column count.

    Args:
        input_file (str): Path to input CSV file
        output_file (str): Path to output CSV file (if None, overwrites input file)
        max_columns (int): Maximum number of columns to keep (if None, keep all valid columns)
        skip_empty_columns (bool): Whether to remove completely empty columns
    """
    try:
        if not os.path.exists(input_file):
            print(f"Error: Input file '{input_file}' does not exist.")
            return False

        # Read raw CSV to handle Google Sheets multi-line headers
        rows = []
        with open(input_file, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                rows.append(row)

        if not rows:
            print("Error: No data found in file")
            return False

        # Merge multi-line headers
        headers, first_data_idx = merge_google_headers(rows)

        # Get data rows
        data_rows = rows[first_data_idx:]

        # Create DataFrame with merged headers
        df = pd.DataFrame(data_rows, columns=headers)
        print(f"Original CSV: {len(df)} rows, {len(df.columns)} columns")

        original_cols = len(df.columns)

        # Remove columns with 'Unnamed:' in the name
        df = df.loc[:, ~df.columns.str.contains('^Unnamed:', na=False)]
        print(f"Removed {original_cols - len(df.columns)} unnamed columns")

        # Remove completely empty columns if requested
        if skip_empty_columns:
            before_empty_removal = len(df.columns)
            df = df.dropna(axis=1, how='all')
            empty_cols_removed = before_empty_removal - len(df.columns)
            if empty_cols_removed > 0:
                print(f"Removed {empty_cols_removed} empty columns")

        # Limit number of columns if specified
        if max_columns and len(df.columns) > max_columns:
            df = df.iloc[:, :max_columns]
            print(f"Limited to first {max_columns} columns")

        # Use input file as output if no output file specified
        if output_file is None:
            output_file = input_file

        # Save the cleaned CSV
        df.to_csv(output_file, index=False)
        print(f"Cleaned CSV: {len(df)} rows, {len(df.columns)} columns")
        print(f"Saved to: {output_file}")

        return True

    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean CSV file by removing unnamed and empty columns.")
    parser.add_argument("input_file", help="Path to input CSV file")
    parser.add_argument("-o", "--output", help="Path to output CSV file (if not provided, overwrites input file)")
    parser.add_argument("--max-columns", type=int, help="Maximum number of columns to keep")
    parser.add_argument("--keep-empty-columns", action="store_true", 
                       help="Keep empty columns (default: remove empty columns)")
    
    args = parser.parse_args()
    
    skip_empty = not args.keep_empty_columns
    
    success = clean_csv(
        input_file=args.input_file,
        output_file=args.output,
        max_columns=args.max_columns,
        skip_empty_columns=skip_empty
    )
    
    if not success:
        exit(1)