#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3

print("=== Checking workflow_instances Table Structure ===")

conn = sqlite3.connect('production.db')
cursor = conn.cursor()

# Get the complete structure of workflow_instances table
cursor.execute("PRAGMA table_info(workflow_instances)")
columns = cursor.fetchall()

print("Complete workflow_instances table structure:")
for col in columns:
    print(f"  {col[1]} ({col[2]}) - {col[3] and 'NOT NULL' or 'NULL'}")

print("\n=== Sample workflow data ===")
cursor.execute("SELECT * FROM workflow_instances WHERE workflow_status = 'Active' LIMIT 3")
sample_data = cursor.fetchall()

if sample_data:
    print("Sample active workflow:")
    for i, row in enumerate(sample_data):
        print(f"\nWorkflow {i+1}:")
        for j, col in enumerate(columns):
            print(f"  {col[1]}: {row[j]}")

# Check for step/date related columns specifically
date_columns = [col[1] for col in columns if 'date' in col[1].lower() or 'updated' in col[1].lower() or 'created' in col[1].lower()]
step_columns = [col[1] for col in columns if 'step' in col[1].lower()]

print(f"\n=== Date/Time Related Columns ===")
for col in date_columns:
    print(f"  {col}")

print(f"\n=== Step Related Columns ===")
for col in step_columns:
    print(f"  {col}")

# Check what the most recent workflow looks like
cursor.execute("SELECT * FROM workflow_instances ORDER BY updated_at DESC LIMIT 1")
recent_workflow = cursor.fetchone()

if recent_workflow:
    print("\n=== Most Recent Workflow ===")
    for j, col in enumerate(columns):
        print(f"  {col[1]}: {recent_workflow[j]}")

conn.close()

print("\n=== Analysis Complete ===")