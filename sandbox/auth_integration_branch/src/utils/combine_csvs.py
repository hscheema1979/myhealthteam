import pandas as pd
import os
import argparse

def combine_csvs(folder_path, output_filepath, columns_to_keep=None, skip_empty_columns=False):
    """
    Combines all CSV files in a folder into a single CSV file,
    with options to filter columns and skip empty ones.

    Args:
        folder_path (str): The path to the folder containing the CSV files.
        output_filepath (str): The path to the output CSV file.
        columns_to_keep (list, optional): A list of specific column names to keep.
                                         If provided, only these columns will be included.
        skip_empty_columns (bool): If True, drops any columns that are entirely
                                   empty or have unnamed headers (e.g., "Unnamed: 0").
    """
    try:
        pd
    except NameError:
        print("Error: pandas library not found.")
        print("Please install it using: pip install pandas")
        return

    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' does not exist.")
        return

    all_dataframes = []
    print(f"Processing all CSV files in folder: '{folder_path}'...")

    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            full_path = os.path.join(folder_path, filename)
            print(f"Reading file '{filename}'...")

            try:
                df = pd.read_csv(full_path)
                
                # --- NEW: Clean up column names to handle spaces and newlines ---
                df.columns = df.columns.str.strip().str.replace('\n', ' ')
                
                # Apply column filtering if specified
                if columns_to_keep:
                    existing_columns = [col for col in columns_to_keep if col in df.columns]
                    df = df[existing_columns]
                    print(f"Filtered for columns: {', '.join(existing_columns)}")

                # Apply empty column skipping if specified
                if skip_empty_columns:
                    # Drop columns where all values are NaN
                    df.dropna(axis=1, how='all', inplace=True)
                    # Drop columns with names like "Unnamed: 0"
                    df.drop(df.columns[df.columns.str.contains('Unnamed:', case=False)], axis=1, inplace=True, errors='ignore')
                    print("Empty and unnamed columns removed.")

                all_dataframes.append(df)
            except Exception as e:
                print(f"An error occurred while processing '{filename}': {e}")
                continue
    
    if not all_dataframes:
        print("No CSV files found to combine.")
        return

    # Combine all dataframes into a single one
    print("\nCombining all dataframes...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)

    # Save the combined dataframe to a single CSV file
    try:
        combined_df.to_csv(output_filepath, index=False)
        print(f"Successfully combined data into '{output_filepath}'.")
    except Exception as e:
        print(f"An error occurred while writing the output file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine multiple CSV files from a folder into a single CSV file.")
    parser.add_argument("folder_path", type=str, help="The path to the folder containing the CSV files.")
    parser.add_argument("-o", "--output", type=str, help="The name or path for the output CSV file. If not provided, a file with the folder's name will be created inside the folder.", default=None)
    parser.add_argument("--skip-empty-columns", action="store_true", help="Skip any empty or unnamed columns in the CSV files.", default=False)
    parser.add_argument("--columns-to-keep", type=str, help="A comma-separated list of column headers to keep. Only these columns will be imported.", default=None)

    args = parser.parse_args()

    output_file = args.output
    if not output_file:
        folder_name = os.path.basename(args.folder_path.rstrip(os.sep))
        output_file = os.path.join(args.folder_path, f"{folder_name}.csv")

    columns_to_keep_list = None
    if args.columns_to_keep:
        columns_to_keep_list = [col.strip() for col in args.columns_to_keep.split(',')]

    combine_csvs(
        folder_path=args.folder_path,
        output_filepath=output_file,
        columns_to_keep=columns_to_keep_list,
        skip_empty_columns=args.skip_empty_columns
    )
