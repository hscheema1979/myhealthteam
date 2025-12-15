#!/usr/bin/env python3

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.workflow_utils import get_ongoing_workflows
import streamlit as st

print("=== Copying Exact Coordinator Filtering Logic ===")

# Copy EXACTLY what the coordinator dashboard does for filtering
user_id = 14  # Jan's user_id
user_role_ids = [36, 40]  # CC and CM roles

print("Copying coordinator dashboard filtering logic...")

# Get workflows using existing infrastructure
workflows_data = get_ongoing_workflows(user_id, user_role_ids)

if workflows_data:
    import pandas as pd
    workflows_df = pd.DataFrame(workflows_data)
    
    print(f"Found {len(workflows_df)} workflows")
    
    # COPY EXACTLY the coordinator dashboard filtering logic
    print("Copying coordinator filtering module...")
    
    # EXACT same as coordinator dashboard - copy line by line
    # from show_coordinator_patient_list() function
    
    # --- Add Search and Filter UI at the top (EXACT COPY) ---
    st.markdown("#### Search and Filter Workflows")
    
    # Create filter columns (EXACT COPY)
    col_search, col_filter = st.columns([2, 1])
    
    with col_search:
        # EXACT same search input as coordinator dashboard
        search_query = st.text_input(
            "Search by workflow patient name or ID",
            key="workflow_search",
            placeholder="Enter patient name or workflow ID..."
        )
    
    with col_filter:
        # EXACT same coordinator filter as coordinator dashboard
        try:
            all_coordinators = database.get_users_by_role(36)  # 36 = Care Coordinator role
            coordinator_options = ["All Coordinators"]
            
            for coord in all_coordinators:
                coord_name = f"{coord.get('full_name', coord.get('username', 'Unknown'))}"
                coordinator_options.append(coord_name)
            
            # Default to showing only the logged-in user's workflows
            current_user_name = None
            try:
                current_user = database.get_user_by_id(user_id)
                if current_user:
                    full_name = current_user.get('full_name')
                    username = current_user.get('username')
                    current_user_name = full_name if full_name else username if username else "Unknown User"
            except Exception:
                pass
            
            # Set default selection - only current user if found
            default_selection = [current_user_name] if current_user_name and current_user_name in coordinator_options else ["All Coordinators"]
            
            selected_coordinators = st.multiselect(
                "Filter by Coordinator(s)",
                coordinator_options,
                key="workflow_coordinator_filter",
                default=default_selection,
                help="Select one or more coordinators to view their workflows. Default shows your workflows."
            )
            
        except Exception as e:
            st.error(f"Error loading coordinator filter: {e}")
            selected_coordinators = ["All Coordinators"]
    
    print("✅ Coordinator filtering logic copied successfully!")
    
    # Now apply the filtering to workflows EXACTLY like coordinator dashboard does for patients
    print("Applying filtering to workflows...")
    
    # Filter workflows based on search and coordinator selection (EXACT same logic)
    filtered_workflows = []
    
    for workflow in workflows_data:
        # Check search filter (similar to patient search)
        workflow_patient = workflow.get('patient_name', '')
        workflow_id = str(workflow.get('instance_id', ''))
        
        # Search filter logic (EXACT same as coordinator dashboard)
        if search_query:
            search_lower = search_query.lower()
            if (search_lower not in workflow_patient.lower() and 
                search_lower not in workflow_id.lower()):
                continue
        
        # Coordinator filter logic (EXACT same as coordinator dashboard)
        if "All Coordinators" not in selected_coordinators:
            coordinator_name = workflow.get('coordinator_name', 'Unknown')
            if coordinator_name not in selected_coordinators:
                continue
        
        filtered_workflows.append(workflow)
    
    print(f"After filtering: {len(filtered_workflows)} workflows")
    
    # Create filtered DataFrame (EXACT same as coordinator dashboard)
    if filtered_workflows:
        filtered_df = pd.DataFrame(filtered_workflows)
        
        print("Creating workflow table with EXACT same styling as coordinator dashboard...")
        
        # EXACT same table formatting as coordinator dashboard
        filtered_df['Select'] = False
        
        # Same column mapping as coordinator dashboard
        column_mapping = {
            'workflow_type': 'Workflow Type',
            'patient_name': 'Patient Name',
            'coordinator_name': 'Assigned Coordinator',
            'workflow_status': 'Status',
            'current_step': 'Current Step',
            'created_date': 'Created Date'
        }
        
        display_df = filtered_df[list(column_mapping.keys()) + ['Select']].copy()
        display_df = display_df.rename(columns=column_mapping)
        
        # EXACT same st.data_editor call as coordinator dashboard
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
                "Workflow Type": st.column_config.TextColumn("Workflow Type"),
                "Patient Name": st.column_config.TextColumn("Patient Name"),
                "Assigned Coordinator": st.column_config.TextColumn("Assigned Coordinator"),
                "Status": st.column_config.TextColumn("Status"),
                "Current Step": st.column_config.NumberColumn("Current Step"),
                "Created Date": st.column_config.TextColumn("Created Date")
            },
            key="workflow_reassignment_table",
            height=500
        )
        
        print("✅ Workflow table created with EXACT coordinator dashboard styling!")
        
        # Handle selections (similar to coordinator dashboard)
        if len(edited_df[edited_df['Select'] == True]) > 0:
            selected_workflows = edited_df[edited_df['Select'] == True]
            st.success(f"**{len(selected_workflows)} workflows selected**")
            
            # Coordinator selection for reassignment (similar to coordinator dashboard patient reassignment)
            if len(selected_workflows) > 0:
                col_target, col_action = st.columns([2, 1])
                with col_target:
                    target_coordinator_name = st.selectbox(
                        "Reassign to Coordinator:",
                        options=list(coordinator_options.keys()),
                        key="target_workflow_coordinator"
                    )
                
                with col_action:
                    st.markdown("&nbsp;")
                    if st.button("🚀 Execute Reassignment", type="primary"):
                        if target_coordinator_name and target_coordinator_name != "All Coordinators":
                            # Execute reassignment using existing database functions
                            target_user_id = [coord['user_id'] for coord in all_coordinators if f"{coord.get('full_name', coord.get('username', 'Unknown'))}" == target_coordinator_name][0]
                            
                            # Use existing database update functions
                            success_count = 0
                            for idx in selected_workflows.index:
                                instance_id = selected_workflows.iloc[idx]['Instance ID']
                                current_coordinator = selected_workflows.iloc[idx]['Assigned Coordinator']
                                
                                try:
                                    conn = database.get_db_connection()
                                    conn.execute(
                                        """UPDATE workflow_instances 
                                           SET coordinator_id = ?, coordinator_name = ?, updated_at = CURRENT_TIMESTAMP 
                                           WHERE instance_id = ?""",
                                        (target_user_id, target_coordinator_name, instance_id)
                                    )
                                    conn.commit()
                                    conn.close()
                                    success_count += 1
                                except Exception as e:
                                    st.error(f"Error reassigning workflow {instance_id}: {e}")
                            
                            if success_count > 0:
                                st.success(f"✅ Successfully reassigned {success_count} workflows to {target_coordinator_name}")
                                st.rerun()
                        else:
                            st.warning("Please select a target coordinator")
        else:
            st.info("Select workflows from the table above to enable reassignment")
    else:
        st.info("No workflows match the current filters")

else:
    st.info("No active workflows available for reassignment.")

print("\n=== Coordinator Dashboard Filtering Module Copied Successfully ===")