#!/usr/bin/env python3

import time
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import get_ongoing_workflows
import pandas as pd

print("=== Debugging Workflow Performance ===")

# Test the performance step by step
user_id = 14  # Jan's user_id
user_role_ids = [36, 40]  # CC and CM roles

print("1. Testing get_ongoing_workflows performance...")
start_time = time.time()

try:
    workflows_data = get_ongoing_workflows(user_id, user_role_ids)
    
    end_time = time.time()
    print(f"   ✅ get_ongoing_workflows() took {end_time - start_time:.3f} seconds")
    print(f"   Found {len(workflows_data)} workflows")
    
    if workflows_data:
        print("2. Testing DataFrame conversion performance...")
        df_start = time.time()
        workflows_df = pd.DataFrame(workflows_data)
        df_end = time.time()
        print(f"   ✅ DataFrame conversion took {df_end - df_start:.3f} seconds")
        print(f"   DataFrame shape: {workflows_df.shape}")
        
        print("3. Testing column operations performance...")
        col_start = time.time()
        
        # Test the operations that happen in the dashboard
        display_df = workflows_df.copy()
        display_df['Select'] = False
        
        # Test column mapping
        column_mapping = {
            'workflow_type': 'Workflow Type',
            'patient_name': 'Patient Name',
            'coordinator_name': 'Assigned Coordinator',
            'workflow_status': 'Status',
            'current_step': 'Current Step',
            'created_date': 'Created Date',
            'updated_at': 'Last Updated'
        }
        
        available_columns = [col for col in display_df.columns if col in column_mapping.keys()]
        display_df = display_df[available_columns].copy()
        display_df = display_df.rename(columns=column_mapping)
        
        col_end = time.time()
        print(f"   ✅ Column operations took {col_end - col_start:.3f} seconds")
        
        print("4. Testing individual operations...")
        
        # Test unique coordinators
        unique_start = time.time()
        unique_coordinators = len(display_df['Assigned Coordinator'].unique())
        unique_end = time.time()
        print(f"   ✅ Unique coordinators count took {unique_end - unique_start:.3f} seconds")
        
        # Test mean calculation
        mean_start = time.time()
        avg_steps = display_df['Current Step'].mean() if 'Current Step' in display_df.columns else 0
        mean_end = time.time()
        print(f"   ✅ Average step calculation took {mean_end - mean_start:.3f} seconds")
        
        print("\n5. Database query analysis...")
        print("   The query gets ALL active workflows for CM role - this could be slow with large datasets")
        print(f"   Current query returns {len(workflows_data)} rows")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n=== Performance Analysis Complete ===")