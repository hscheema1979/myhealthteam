#!/usr/bin/env python3
"""
Simple fix for admin dashboard workflow reassignment
"""

def simple_workflow_section():
    """Simple, clean workflow reassignment section"""
    
    # --- TAB: Workflow Reassignment (Bianchi's Special View) ---
    with tab_workflow:
        st.subheader("🔧 Workflow Reassignment")
        st.markdown("Admin-level workflow management with bulk reassignment capabilities")
        
        debug_mode = st.session_state.get('admin_debug_session', False)
        
        try:
            # Simple approach - get all active workflows directly
            conn = db.get_db_connection()
            result = conn.execute("""
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
            """)
            
            workflows = result.fetchall()
            conn.close()
            
            if workflows:
                # Convert to DataFrame
                df_data = []
                for wf in workflows:
                    wf_dict = dict(wf)
                    df_data.append({
                        'instance_id': wf_dict['instance_id'],
                        'workflow_type': wf_dict['workflow_type'],
                        'patient_name': wf_dict['patient_name'],
                        'patient_id': wf_dict['patient_id'],
                        'coordinator_name': wf_dict.get('coordinator_name', 'Unknown'),
                        'workflow_status': wf_dict['workflow_status'],
                        'current_step': wf_dict.get('current_step', 1),
                        'total_steps': wf_dict.get('total_steps', 1),
                        'priority': wf_dict.get('priority', 'Normal'),
                        'created_date': wf_dict['created_at'][:10] if wf_dict['created_at'] else 'N/A'
                    })
                
                workflows_df = pd.DataFrame(df_data)
            else:
                workflows_df = pd.DataFrame()
            
            if debug_mode:
                st.write(f"**DEBUG:** Found {len(workflows_df)} workflows")
            
        except Exception as e:
            st.error(f"Error loading workflows: {e}")
            workflows_df = pd.DataFrame()
        
        # Show results
        if workflows_df.empty:
            st.info("No active workflows available for reassignment.")
        else:
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
            
            # Show reassignment table
            from src.utils.workflow_reassignment_ui import show_workflow_reassignment_table
            
            st.subheader("📋 Workflows Available for Reassignment")
            selected_instance_ids, should_rerun = show_workflow_reassignment_table(
                workflows_df=workflows_df,
                user_id=user_id,
                table_key="admin_workflow",
                show_search_filter=True
            )
            
            if should_rerun:
                st.rerun()

if __name__ == "__main__":
    import streamlit as st
    import pandas as pd
    from src import database as db
    
    simple_workflow_section()