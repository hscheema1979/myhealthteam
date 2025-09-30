import pandas as pd
import sqlite3
import os
import argparse

def csv_to_sql(csv_filepath, sql_filepath=None, table_name=None, append_to_existing=False, skip_empty_columns=False, columns_to_keep=None):
    """
    Converts a CSV file to an SQL table.

    Args:
        csv_filepath (str): The path to the CSV file.
        sql_filepath (str, optional): The path to the SQLite database file.
                                      If None, a new database file with the
                                      same name as the CSV file is created
                                      in the same directory.
        table_name (str, optional): The name of the SQL table to create or
                                    append to. If None, the table name will
                                    be the same as the CSV file name (without extension).
        append_to_existing (bool): If True, the data will be appended to an
                                   existing table. If False, the table will
                                   be replaced if it already exists.
        skip_empty_columns (bool): If True, drops any columns that are entirely
                                   empty or have unnamed headers (e.g., "Unnamed: 0").
        columns_to_keep (list, optional): A list of specific column names to keep.
                                         If provided, only these columns will be imported.
    """
    try:
        # Check if pandas is installed
        pd
    except NameError:
        print("Error: pandas library not found.")
        print("Please install it using: pip install pandas")
        return

    # Determine the default SQL file path and table name if not provided
    if sql_filepath is None:
        base_name, _ = os.path.splitext(os.path.basename(csv_filepath))
        sql_filepath = os.path.join(os.path.dirname(csv_filepath), f"{base_name}.db")
        if table_name is None:
            table_name = base_name
    elif table_name is None:
        table_name, _ = os.path.splitext(os.path.basename(csv_filepath))

    print(f"Reading data from '{csv_filepath}'...")
    try:
        df = pd.read_csv(csv_filepath, on_bad_lines='skip')
        print(f"Data read successfully. Loaded {len(df)} rows.")
    except FileNotFoundError:
        print(f"Error: The file '{csv_filepath}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return

    if columns_to_keep:
        print(f"Filtering for specific columns: {', '.join(columns_to_keep)}...")
        # Get the columns that exist in both the DataFrame and the list to keep
        existing_columns = [col for col in columns_to_keep if col in df.columns]
        df = df[existing_columns]
        print("Columns filtered.")
    
    if skip_empty_columns:
        print("Skipping empty and unnamed columns...")
        # Drop columns where all values are NaN
        df.dropna(axis=1, how='all', inplace=True)
        # Drop columns with names like "Unnamed: 0"
        df.drop(df.columns[df.columns.str.contains('Unnamed:', case=False)], axis=1, inplace=True, errors='ignore')
        print("Empty and unnamed columns removed.")


    # Create a connection to the SQLite database
    conn = sqlite3.connect(sql_filepath)
    print(f"Connected to database '{sql_filepath}'.")

    # Always drop the table before import (unless appending)
    if not append_to_existing:
        try:
            conn.execute(f"DROP TABLE IF EXISTS [{table_name}];")
            print(f"Dropped table '{table_name}' if it existed.")
        except Exception as e:
            print(f"Warning: Could not drop table '{table_name}': {e}")

    # Set the 'if_exists' parameter based on the append_to_existing flag
    if append_to_existing:
        if_exists_mode = 'append'
        print(f"Appending data to table '{table_name}'...")
    else:
        if_exists_mode = 'replace'
        print(f"Creating/replacing table '{table_name}'...")

    try:
        # Write the DataFrame to the SQL table
        df.to_sql(table_name, conn, if_exists=if_exists_mode, index=False)
        print(f"Successfully wrote data to table '{table_name}'.")
    except Exception as e:
        print(f"An error occurred while writing to the SQL table: {e}")
    finally:
        # Close the database connection
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert CSV file(s) to an SQLite table(s).")
    parser.add_argument("csv_filepath", nargs='?', type=str, help="Path to a single source CSV file.")
    parser.add_argument("-f", "--folder", type=str, help="Path to a folder containing multiple CSV files to process.")
    parser.add_argument("-s", "--sql-filepath", type=str, help="Path to the destination SQLite database file. If not provided, a new database is created with the same name as the folder or CSV file.", default=None)
    parser.add_argument("-t", "--table-name", type=str, help="Name of the table to create. Only used for single CSV file conversion. If not provided, the table name is the same as the CSV file name.", default=None)
    parser.add_argument("-T", "--single-table-name", type=str, default="combined_data", help="Name of the single table to create when processing a folder. Defaults to 'combined_data'.")
    parser.add_argument("-a", "--append", action="store_true", help="Append data to the table(s) instead of replacing them. The table(s) must already exist.", default=False)
    parser.add_argument("--skip-empty-columns", action="store_true", help="Skip any empty or unnamed columns in the CSV files.", default=False)
    parser.add_argument("--columns-to-keep", type=str, help="A comma-separated list of column headers to keep. Only these columns will be imported.", default=None)

    args = parser.parse_args()

    # Split the columns to keep string into a list
    columns_to_keep_list = None
    if args.columns_to_keep:
        columns_to_keep_list = [col.strip() for col in args.columns_to_keep.split(',')]

    # If a folder is specified, process all CSVs within it
    if args.folder:
        if not os.path.isdir(args.folder):
            print(f"Error: Folder '{args.folder}' does not exist.")
            exit()

        # Default SQL filepath to the folder name
        if args.sql_filepath is None:
            folder_name = os.path.basename(args.folder.rstrip(os.sep))
            args.sql_filepath = os.path.join(args.folder, f"{folder_name}.db")

        print(f"Processing all CSV files in folder: '{args.folder}'...")
        print(f"All data will be combined into a single table '{args.single_table_name}' in database: '{args.sql_filepath}'")

        first_file = True
        for filename in os.listdir(args.folder):
            if filename.endswith(".csv"):
                full_path = os.path.join(args.folder, filename)
                
                # Check if we should append. We only replace on the very first file if --append isn't used.
                append_to_existing = args.append or not first_file
                
                print("\n" + "="*50)
                csv_to_sql(full_path, sql_filepath=args.sql_filepath, table_name=args.single_table_name, append_to_existing=append_to_existing, skip_empty_columns=args.skip_empty_columns, columns_to_keep=columns_to_keep_list)
                
                first_file = False

    # If a single CSV is specified, process that file
    elif args.csv_filepath:
        csv_to_sql(
            csv_filepath=args.csv_filepath,
            sql_filepath=args.sql_filepath,
            table_name=args.table_name,
            append_to_existing=args.append,
            skip_empty_columns=args.skip_empty_columns,
            columns_to_keep=columns_to_keep_list
        )
    else:
        parser.print_help()
