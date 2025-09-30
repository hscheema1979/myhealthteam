import pandas as pd
import argparse
import os

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
            
        # Read the CSV file
        df = pd.read_csv(input_file)
        print(f"Original CSV: {len(df)} rows, {len(df.columns)} columns")
        
        original_cols = len(df.columns)
        
        # Clean up column names to handle spaces and newlines
        df.columns = df.columns.str.strip().str.replace('\n', ' ')
        
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