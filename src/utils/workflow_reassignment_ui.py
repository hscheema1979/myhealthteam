"""
workflow_reassignment_ui.py
Shared UI components for workflow reassignment across all dashboards.
Eliminates code duplication between admin and coordinator dashboards.
"""

import streamlit as st
import pandas as pd
from typing import List, Dict, Optional, Tuple
from src.utils.workflow_utils import execute_workflow_reassignment, get_available_coordinators


def show_workflow_reassignment_table(
    workflows_df: pd.DataFrame,
    user_id: int,
    table_key: str = "workflow_reassignment",
    show_search_filter: bool = True,
    debug_mode: bool = False,
    coordinators_preloaded: List[Dict] = None
) -> Tuple[List[int], bool]:
    """
    Display a unified workflow reassignment table with search/filter functionality.
    
    Args:
        workflows_df: DataFrame containing workflow data
        user_id: ID of the current user performing reassignment
        table_key: Unique key for the Streamlit component
        show_search_filter: Whether to show search and filter controls
        
    Returns:
        Tuple of (selected_instance_ids, should_rerun) where:
        - selected_instance_ids: List of selected workflow instance IDs
        - should_rerun: Whether to rerun the Streamlit app (after successful reassignment)
    """
    
    if workflows_df.empty:
        st.info("No workflows available for reassignment.")
        return [], False
    
    # Add search and filter functionality
    filtered_workflows_df = workflows_df.copy()
    
    if show_search_filter:
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            # Patient search
            search_query = st.text_input("Search patients", placeholder="Enter patient name or ID...", key=f"{table_key}_search")
        
        with col_filter2:
            # Coordinator filter
            coordinator_names = ['All Coordinators'] + sorted(workflows_df['coordinator_name'].unique().tolist())
            selected_coordinator = st.selectbox("Filter by coordinator", coordinator_names, key=f"{table_key}_filter")
        
        # Apply filters
        if search_query.strip():
            query = search_query.lower().strip()
            filtered_workflows_df = filtered_workflows_df[
                filtered_workflows_df['patient_name'].str.lower().str.contains(query, na=False) |
                filtered_workflows_df['patient_id'].str.lower().str.contains(query, na=False)
            ]
        
        # Filter by coordinator
        if selected_coordinator != "All Coordinators":
            filtered_workflows_df = filtered_workflows_df[
                filtered_workflows_df['coordinator_name'] == selected_coordinator
            ]
        
        # Show filter results
        if len(filtered_workflows_df) != len(workflows_df):
            st.info(f"Showing {len(filtered_workflows_df)} of {len(workflows_df)} workflows")
    
    # Use preloaded coordinator data if available, otherwise fetch it
    if coordinators_preloaded:
        available_coordinators = coordinators_preloaded
        if debug_mode:
            st.write("DEBUG: Using preloaded coordinator data")
    else:
        available_coordinators = get_available_coordinators()
        if debug_mode:
            st.write("DEBUG: Fetched coordinator data")
    
    coordinator_options = {coord['full_name']: coord['user_id'] for coord in available_coordinators}
    
    if available_coordinators and not filtered_workflows_df.empty:
        # Prepare data for table display
        display_df = filtered_workflows_df.copy()
        
        # Add selection column
        display_df['Select'] = False
        
        # Reorder columns for better display - use only available columns
        available_columns = [col for col in ['workflow_type', 'patient_name', 'coordinator_name', 'workflow_status', 'current_step', 'created_date'] if col in filtered_workflows_df.columns]
        column_order = ['Select'] + available_columns
        display_df = display_df[column_order]
        
        # Show the table
        st.markdown("**Select workflows for reassignment:**")
        
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
                "workflow_type": st.column_config.TextColumn("Workflow Type"),
                "patient_name": st.column_config.TextColumn("Patient Name"),
                "coordinator_name": st.column_config.TextColumn("Assigned Coordinator"),
                "workflow_status": st.column_config.TextColumn("Status"),
                "current_step": st.column_config.NumberColumn("Current Step"),
                "created_date": st.column_config.TextColumn("Created Date")
            },
            key=f"{table_key}_editor",
            height=500
        )
        
        # Process selections - use proper indexing
        selected_workflows = edited_df[edited_df['Select'] == True].index.tolist()
        
        # Debug info
        if debug_mode:
            st.write(f"DEBUG: Selected workflow indices: {selected_workflows}")
            st.write(f"DEBUG: Filtered DataFrame length: {len(filtered_workflows_df)}")
            st.write(f"DEBUG: Edited DataFrame length: {len(edited_df)}")
        
        # Use .loc with the selected indices to get instance_ids
        if selected_workflows:
            try:
                selected_instance_ids = filtered_workflows_df.loc[selected_workflows, 'instance_id'].tolist()
            except KeyError as e:
                # Fallback: iterate through indices
                selected_instance_ids = []
                for idx in selected_workflows:
                    if idx in filtered_workflows_df.index:
                        selected_instance_ids.append(filtered_workflows_df.loc[idx, 'instance_id'])
        else:
            selected_instance_ids = []
        
        # Show coordinator dropdown from the beginning (preloaded for instant availability)
        st.subheader("🎯 Reassignment Options")
        target_coordinator = st.selectbox(
            "Select target coordinator:",
            options=list(coordinator_options.keys()),
            key=f"{table_key}_target",
            help="Choose a coordinator to reassign selected workflows to"
        )
        
        # Show selection status and enable reassignment button only when workflows are selected
        if selected_instance_ids:
            st.success(f"**{len(selected_instance_ids)} workflows selected**")
            
            if st.button("🔄 Reassign Selected Workflows", type="primary", key=f"{table_key}_button"):
                if target_coordinator:
                    target_user_id = coordinator_options[target_coordinator]
                    try:
                        success_count = execute_workflow_reassignment(selected_instance_ids, target_user_id, user_id)
                        if success_count > 0:
                            st.success(f"✅ Successfully reassigned {success_count} workflows to {target_coordinator}")
                            return selected_instance_ids, True  # Should rerun
                        else:
                            # Provide specific error messages based on the situation
                            if not selected_instance_ids:
                                st.error("❌ No workflows selected for reassignment")
                            elif not target_user_id:
                                st.error("❌ Invalid target coordinator selected")
                            else:
                                st.error(f"❌ Failed to reassign workflows. No workflows were successfully processed.")
                                st.info("Common issues: workflows may already be assigned to the target coordinator, or there may be database permission issues.")
                            return selected_instance_ids, False
                    except ValueError as ve:
                        st.error(f"❌ Validation error: {str(ve)}")
                        st.info("Please ensure the target coordinator is a valid active coordinator with proper permissions.")
                        return selected_instance_ids, False
                    except Exception as e:
                        st.error(f"❌ Error during reassignment: {str(e)}")
                        st.info("Please check that you have proper permissions and the workflows are valid.")
                        return selected_instance_ids, False
                else:
                    st.warning("Please select a target coordinator")
                    return selected_instance_ids, False
            else:
                return selected_instance_ids, False
        else:
            st.info("Select workflows from the table above to reassign them")
            return [], False
    else:
        if filtered_workflows_df.empty:
            st.warning("No workflows match your current filters")
        else:
            st.warning("No coordinators available for reassignment")
        return [], False


def show_workflow_reassignment_summary(workflows_df: pd.DataFrame) -> Dict:
    """
    Generate summary statistics for workflow reassignment.
    
    Args:
        workflows_df: DataFrame containing workflow data
        
    Returns:
        Dictionary with summary statistics
    """
    if workflows_df.empty:
        return {
            'total': 0,
            'by_status': {},
            'by_coordinator': {},
            'by_workflow_type': {}
        }
    
    summary = {
        'total': len(workflows_df),
        'by_status': workflows_df['workflow_status'].value_counts().to_dict(),
        'by_coordinator': workflows_df['coordinator_name'].value_counts().to_dict(),
        'by_workflow_type': workflows_df['workflow_type'].value_counts().to_dict()
    }
    
    return summary


def display_workflow_summary_stats(summary: Dict):
    """
    Display workflow summary statistics in a nice format.
    
    Args:
        summary: Dictionary from show_workflow_reassignment_summary
    """
    st.markdown(f"**📊 Workflow Summary: {summary['total']} total workflows**")
    
    col_summary1, col_summary2 = st.columns(2)
    
    with col_summary1:
        st.markdown("**By Status**")
        for status, count in summary['by_status'].items():
            st.markdown(f"- {status}: **{count}** workflows")
    
    with col_summary2:
        st.markdown("**By Coordinator**")
        for coord, count in list(summary['by_coordinator'].items())[:5]:  # Show top 5
            st.markdown(f"- {coord}: **{count}** workflows")
        if len(summary['by_coordinator']) > 5:
            st.markdown(f"_... and {len(summary['by_coordinator']) - 5} more_")
    
    with st.expander("View by Workflow Type"):
        for workflow_type, count in summary['by_workflow_type'].items():
            st.markdown(f"- {workflow_type}: **{count}** workflows")
