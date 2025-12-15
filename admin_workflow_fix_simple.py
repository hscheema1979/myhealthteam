#!/usr/bin/env python3
"""
Simplified workflow reassignment that assumes admin access since tab is visible
"""

import streamlit as st
import pandas as pd
from src import database as db

def get_workflows_for_reassignment_admin():
    """
    Get ALL workflows for reassignment - assumes admin access since tab is visible
    No role checking needed - if you can see the tab, you can see all workflows!
    """
    try:
        conn = db.get_db_connection()
        
        # Simple query - get ALL active workflows for reassignment
        query = """
            SELECT 
                instance_id,
                template_name as workflow_type,
                patient_name,
                patient_id,
                coordinator_id,
                coordinator_name,
                workflow_status,
                current_step,
                priority,
                created_at,
                (
                    SELECT COUNT(*) 
                    FROM workflow_steps ws 
                    WHERE ws.template_id = wi.template_id
                ) as total_steps
            FROM workflow_instances wi
            WHERE workflow_status = 'Active'
            ORDER BY created_at DESC
        """
        
        workflows = conn.execute(query).fetchall()
        conn.close()
        
        if not workflows:
            return pd.DataFrame()
        
        # Convert to DataFrame
        workflows_data = []
        for wf in workflows:
            wf_dict = dict(wf)
            workflows_data.append({
                'instance_id': wf_dict['instance_id'],
                'workflow_type': wf_dict['workflow_type'],
                'patient_name': wf_dict['patient_name'],
                'patient_id': wf_dict['patient_id'],
                'coordinator_name': wf_dict.get('coordinator_name', 'Unknown'),
                'coordinator_id': wf_dict.get('coordinator_id', 'Unknown'),
                'workflow_status': wf_dict['workflow_status'],
                'current_step': wf_dict.get('current_step', 1),
                'total_steps': wf_dict.get('total_steps', 1),
                'priority': wf_dict.get('priority', 'Normal'),
                'created_date': wf_dict['created_at'][:10] if wf_dict['created_at'] else 'N/A'
            })
        
        return pd.DataFrame(workflows_data)
        
    except Exception as e:
        print(f"Error getting workflows for reassignment: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def simple_workflow_reassignment_section(user_id):
    """
    Simplified workflow reassignment section that assumes admin access
    """
    
    st.subheader("🔧 Workflow Reassignment")
    st.markdown("Admin-level workflow management with bulk reassignment capabilities")
    
    # Get workflows - no role checking needed since tab is visible
    workflows_df = get_workflows_for_reassignment_admin()
    
    if workflows_df.empty:
        st.info("No active workflows available for reassignment.")
        return
    
    # Success - show the workflows
    st.success(f"Found {len(workflows_df)} workflows for reassignment")
    
    # Show summary
    from src.utils.workflow_utils import get_reassignment_summary
    summary = get_reassignment_summary(workflows_df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Workflows", summary['total_workflows'])
    with col2:
        unique_coordinators = len(summary['by_coordinator'])
        st.metric("Active Coordinators", unique_coordinators)
    with col3:
        avg_steps = summary['avg_steps']
        st.metric("Average Step", f"{avg_steps:.1f}")
    
    # Show the reassignment table
    from src.utils.workflow_reassignment_ui import show_workflow_reassignment_table
    
    st.subheader("📋 Workflows Available for Reassignment")
    
    selected_instance_ids, should_rerun = show_workflow_reassignment_table(
        workflows_df=workflows_df,
        user_id=user_id,
        table_key="admin_workflow",
        show_search_filter=True
    )
    
    if should_rerun:
        st.success("Workflow reassignment completed successfully!")
        st.experimental_rerun()

# Test it
if __name__ == "__main__":
    import streamlit as st
    st.title("Simple Workflow Reassignment Test")
    simple_workflow_reassignment_section(12)  # Harpreet's user_id