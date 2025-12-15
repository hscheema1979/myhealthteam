# ENHANCED WORKFLOW REASSIGNMENT SECTION for admin_dashboard.py
# Replace lines 3123-3201 in admin_dashboard.py with this code:

# --- TAB: Workflow Reassignment (Enhanced Debug Version) ---
    with tab_workflow:
        st.subheader("🔧 Workflow Reassignment")
        st.markdown("Admin-level workflow management with bulk reassignment capabilities")
        
        # Add debug info in development
        if st.session_state.get('debug_mode', False):
            with st.expander("🐛 Debug Information"):
                st.write(f"User ID: {user_id}")
                st.write(f"User Role IDs: {user_role_ids}")
                st.write(f"Is Admin: {34 in user_role_ids}")
                st.write(f"Is Coordinator Manager: {40 in user_role_ids}")
        
        try:
            # Get workflows with enhanced error handling
            workflows_df = get_workflows_for_reassignment(user_id, user_role_ids)
            
            if workflows_df.empty:
                # Enhanced debugging for empty DataFrame
                st.info("No active workflows available for reassignment.")
                
                # Add detailed debug info in development
                if st.session_state.get('debug_mode', False):
                    with st.expander("🔍 Debug: Why no workflows?"):
                        # Check database directly
                        conn = db.get_db_connection()
                        try:
                            result = conn.execute("SELECT COUNT(*) as count FROM workflow_instances WHERE workflow_status = 'Active'")
                            db_count = result.fetchone()['count']
                            st.write(f"Active workflows in database: {db_count}")
                            
                            if db_count > 0:
                                st.warning(f"Database has {db_count} workflows, but get_workflows_for_reassignment returned 0")
                                st.write("This suggests a filtering or permission issue.")
                                
                                # Show what the admin query should return
                                if 34 in user_role_ids or 40 in user_role_ids:
                                    admin_query = """
                                        SELECT instance_id, template_name, patient_name, coordinator_name, workflow_status
                                        FROM workflow_instances 
                                        WHERE workflow_status = 'Active'
                                        LIMIT 5
                                    """
                                    samples = conn.execute(admin_query).fetchall()
                                    st.write("Sample workflows that should be visible:")
                                    for sample in samples:
                                        st.write(f"  - {dict(sample)}")
                        finally:
                            conn.close()
            else:
                st.success(f"Found {len(workflows_df)} workflows for reassignment")
                
                # Show summary
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
                
                # Show workflow distribution
                with st.expander("📊 Assignment Distribution", expanded=False):
                    col_summary1, col_summary2 = st.columns(2)
                    with col_summary1:
                        st.markdown("**By Coordinator**")
                        for coord, count in summary['by_coordinator'].items():
                            st.markdown(f"- {coord}: **{count}** workflows")
                    
                    with col_summary2:
                        st.markdown("**By Workflow Type**")
                        for workflow_type, count in summary['by_workflow_type'].items():
                            st.markdown(f"- {workflow_type}: **{count}** workflows")
                
                # Import and use the workflow reassignment UI
                from src.utils.workflow_reassignment_ui import (
                    show_workflow_reassignment_table,
                    display_workflow_summary_stats
                )
                
                st.subheader("📋 Workflows Available for Reassignment")
                
                # Use shared workflow reassignment table
                selected_instance_ids, should_rerun = show_workflow_reassignment_table(
                    workflows_df, 
                    user_id, 
                    table_key="admin_workflow_reassignment",
                    show_search_filter=True
                )
                
                if should_rerun:
                    st.success("Workflow reassignment completed successfully!")
                    st.experimental_rerun()
        
        except Exception as e:
            st.error(f"Error loading workflows: {e}")
            st.write("**Debug Info:**")
            st.write(f"- user_id: {user_id}")
            st.write(f"- user_role_ids: {user_role_ids}")
            st.write(f"- Error type: {type(e).__name__}")
            
            # Set empty DataFrame on error (original behavior)
            workflows_df = pd.DataFrame()
            st.info("No active workflows available for reassignment.")
            
            # Optional: Show traceback in development
            if st.session_state.get('debug_mode', False):
                import traceback
                st.code(traceback.format_exc())