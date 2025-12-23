"""
Simple PyGWalker script to load all unified views into ONE PyGWalker instance.
Run with: python simple_pygwalker.py
"""

import sqlite3

import pandas as pd
import pygwalker as pyg

print("=" * 60)
print("Loading all unified views into PyGWalker...")
print("=" * 60)

# Connect to database
conn = sqlite3.connect("production.db")

# List of views we created
views = [
    "unified_tasks",
    "unified_tasks_with_facilities",
    "minutes_per_staff_per_month_per_facility",
    "tasks_per_month_per_facility",
    "staff_performance_summary",
    "facility_summary",
    "monthly_trends",
]

print(f"Found {len(views)} views to load:")
for i, view in enumerate(views, 1):
    print(f"  {i}. {view}")

# Load all views into a single DataFrame
all_data_frames = []

for view in views:
    print(f"\nLoading: {view}")
    try:
        # Load the view (limit to reasonable size for performance)
        df = pd.read_sql_query(f"SELECT * FROM {view} LIMIT 5000", conn)

        # Add view name as a column
        df["_view_name"] = view

        all_data_frames.append(df)
        print(f"  ✓ {len(df)} rows, {len(df.columns)} columns")

    except Exception as e:
        print(f"  ✗ Error: {e}")

conn.close()

if not all_data_frames:
    print("\nERROR: No data loaded!")
    print("Check that the views exist in the database.")
    exit(1)

# Combine all DataFrames
print(f"\nCombining {len(all_data_frames)} datasets...")
combined_df = pd.concat(all_data_frames, ignore_index=True)

print(
    f"\n✅ Total combined data: {len(combined_df):,} rows, {len(combined_df.columns)} columns"
)
print(f"   Unique views: {combined_df['_view_name'].nunique()}")
print()

print("=" * 60)
print("Starting PyGWalker...")
print("=" * 60)
print("\nTips:")
print("1. Use the '_view_name' column to filter by dataset")
print("2. Drag and drop columns to create visualizations")
print("3. Use filters in the right panel")
print("4. Close browser window when done")
print("\nOpening browser...")

# Start PyGWalker
pyg.walk(
    combined_df,
    spec="./pygwalker_config.json",
    debug=False,
    show_cloud_tool=False,
)
