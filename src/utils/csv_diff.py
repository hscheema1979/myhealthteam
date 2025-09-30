# csv_diff.py
"""
Compare two CSV files and output the diff (new/changed rows in the new file).
Usage:
    python csv_diff.py <old_csv> <new_csv> <key_columns> <output_diff_csv>

- <key_columns> is a comma-separated list of columns that form the unique key (e.g., 'ID' or 'PatientID,Date')
- Only rows that are new or changed in <new_csv> (compared to <old_csv>) are output to <output_diff_csv>

Example:
    python csv_diff.py exports/coordinator_tasks_2025_09.csv downloads/cmlog.csv "ID,Date" exports/coordinator_tasks_diff.csv
"""
import sys
import pandas as pd

if len(sys.argv) != 5:
    print("Usage: python csv_diff.py <old_csv> <new_csv> <key_columns> <output_diff_csv>")
    sys.exit(1)

old_csv = sys.argv[1]
new_csv = sys.argv[2]
key_cols = [col.strip() for col in sys.argv[3].split(",")]
outfile = sys.argv[4]

# Read CSVs
old_df = pd.read_csv(old_csv, dtype=str)
new_df = pd.read_csv(new_csv, dtype=str)

# Set index to key columns
old_df.set_index(key_cols, inplace=True)
new_df.set_index(key_cols, inplace=True)

# Find new or changed rows
# 1. Rows in new_df not in old_df (new rows)
new_rows = new_df.loc[~new_df.index.isin(old_df.index)]
# 2. Rows with same key but different data (changed rows)
common_idx = new_df.index.intersection(old_df.index)
changed_rows = new_df.loc[common_idx][(new_df.loc[common_idx] != old_df.loc[common_idx]).any(axis=1)]

# Combine
diff_df = pd.concat([new_rows, changed_rows])
diff_df.reset_index(inplace=True)
diff_df.to_csv(outfile, index=False)
print(f"Diff rows written to {outfile}: {len(diff_df)}")
