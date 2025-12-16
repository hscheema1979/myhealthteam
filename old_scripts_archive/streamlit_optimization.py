#!/usr/bin/env python3
"""
Streamlit optimization functions for faster refresh
"""

import streamlit as st
import sqlite3
import time
from functools import lru_cache

# ===== OPTIMIZATION 1: CACHED DATABASE CONNECTIONS =====

@st.cache_resource(ttl=3600)  # Cache for 1 hour
def get_db_connection_cached():
    """Cached database connection to avoid reopening connections"""
    return sqlite3.connect('production.db', check_same_thread=False)

# ===== OPTIMIZATION 2: CACHED DATA LOADING =====

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_workflows_cached():
    """Cached workflow data"""
    conn = get_db_connection_cached()
    result = conn.execute("SELECT * FROM workflow_instances WHERE workflow_status = 'Active'")
    workflows = result.fetchall()
    return workflows

@st.cache_data(ttl=600)  # Cache for 10 minutes
def get_user_roles_cached(user_id):
    """Cached user roles"""
    conn = get_db_connection_cached()
    result = conn.execute("SELECT role_id FROM user_roles WHERE user_id = ?", (user_id,))
    roles = [r[0] for r in result.fetchall()]
    return roles

# ===== OPTIMIZATION 3: PROGRESS INDICATORS =====

def show_loading_progress(total_items, description="Loading..."):
    """Show progress bar for long operations"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(total_items):
        progress = (i + 1) / total_items
        progress_bar.progress(progress)
        status_text.text(f"{description} {i+1}/{total_items}")
        yield i
    
    progress_bar.empty()
    status_text.empty()

# ===== OPTIMIZATION 4: PARTIAL UPDATES =====

def create_partial_update_container(key):
    """Create a container for partial updates without full rerun"""
    return st.empty()

def update_partial_container(container, content_func):
    """Update only a specific container"""
    with container.container():
        content_func()

# ===== OPTIMIZATION 5: DEBOUNCED INPUTS =====

def debounced_text_input(label, value="", delay=0.5, key=None):
    """Text input that doesn't trigger immediate reruns"""
    if key is None:
        key = f"debounced_input_{label}"
    
    if key not in st.session_state:
        st.session_state[key] = value
    
    # Only update if value changed significantly or user pressed Enter
    new_value = st.text_input(label, value=st.session_state[key], key=f"{key}_input")
    
    if new_value != st.session_state[key]:
        # Add small delay to prevent excessive reruns
        time.sleep(delay)
        st.session_state[key] = new_value
    
    return st.session_state[key]

# ===== OPTIMIZATION 6: LAZY LOADING =====

def lazy_load_section(section_name, load_func):
    """Load a section only when needed"""
    if f"load_{section_name}" not in st.session_state:
        if st.button(f"Load {section_name}", key=f"btn_{section_name}"):
            with st.spinner(f"Loading {section_name}..."):
                st.session_state[f"load_{section_name}"] = load_func()
                st.rerun()
        return None
    else:
        return st.session_state[f"load_{section_name}"]

# ===== OPTIMIZATION 7: DATABASE QUERY OPTIMIZATION =====

def optimized_workflow_query():
    """Optimized query that only gets necessary columns"""
    conn = get_db_connection_cached()
    result = conn.execute("""
        SELECT 
            instance_id,
            template_name,
            patient_name,
            coordinator_name,
            workflow_status,
            current_step
        FROM workflow_instances 
        WHERE workflow_status = 'Active'
        ORDER BY created_at DESC
        LIMIT 1000
    """)
    return result.fetchall()

# ===== EXAMPLE USAGE IN ADMIN DASHBOARD =====

def optimized_admin_workflow_section():
    """Optimized version of workflow reassignment section"""
    
    with tab_workflow:
        st.subheader("🔧 Workflow Reassignment")
        st.markdown("Admin-level workflow management with bulk reassignment capabilities")
        
        debug_mode = st.session_state.get('admin_debug_session', False)
        
        # Use cached connection and data
        try:
            # Use optimized query
            workflows = optimized_workflow_query()
            
            if workflows:
                # Show progress for large datasets
                with st.spinner(f'Processing {len(workflows)} workflows...'):
                    # Convert to DataFrame efficiently
                    workflows_df = pd.DataFrame(workflows, columns=[
                        'instance_id', 'workflow_type', 'patient_name', 
                        'coordinator_name', 'workflow_status', 'current_step'
                    ])
                
                if debug_mode:
                    st.write(f"DEBUG: Found {len(workflows_df)} workflows")
                
                # Use cached summary calculation
                summary = get_reassignment_summary(workflows_df)
                
                # Show metrics efficiently
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Workflows", summary['total_workflows'])
                col2.metric("Active Coordinators", len(summary['by_coordinator']))
                col3.metric("Average Step", f"{summary['avg_steps']:.1f}")
                
                # Use cached coordinator data
                from src.utils.workflow_reassignment_ui import show_workflow_reassignment_table
                selected_instance_ids, should_rerun = show_workflow_reassignment_table(
                    workflows_df=workflows_df,
                    user_id=user_id,
                    table_key="admin_workflow",
                    show_search_filter=True,
                    debug_mode=debug_mode
                )
                
                if should_rerun:
                    st.success("Workflow reassignment completed successfully!")
                    st.rerun()
            else:
                st.info("No active workflows available for reassignment.")
                
        except Exception as e:
            st.error(f"Error loading workflows: {e}")
            if debug_mode:
                import traceback
                st.code(traceback.format_exc())

if __name__ == "__main__":
    # Test the optimizations
    print("Streamlit optimization functions loaded!")
    print("Use these functions in your admin dashboard for faster performance!")