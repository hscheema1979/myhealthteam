"""
Simple Provider Payment Tracker for Justin
Just shows tasks and lets him mark as paid/not paid - nothing complex
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from database import get_db_connection
from config.ui_style_config import apply_custom_css, get_section_title

def get_provider_tasks_simple():
    """Get all provider tasks for payment tracking"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        billing_status_id,
        provider_name,
        patient_name,
        task_date,
        billing_week,
        task_description,
        minutes_of_service,
        billing_code,
        CASE 
            WHEN is_paid = 1 THEN 'PAID'
            ELSE 'NOT PAID'
        END as payment_status
    FROM provider_task_billing_status
    ORDER BY task_date DESC, provider_name
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def mark_tasks_paid(billing_status_ids):
    """Mark selected tasks as paid"""
    conn = get_db_connection()
    
    try:
        # Mark as paid
        placeholders = ','.join(['?' for _ in billing_status_ids])
        query = f"""
        UPDATE provider_task_billing_status 
        SET is_paid = 1, paid_date = CURRENT_TIMESTAMP, updated_date = CURRENT_TIMESTAMP
        WHERE billing_status_id IN ({placeholders})
        """
        
        conn.execute(query, billing_status_ids)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating payments: {str(e)}")
        return False
    finally:
        conn.close()

def get_payment_summary():
    """Get simple payment summary"""
    conn = get_db_connection()
    
    query = """
    SELECT 
        billing_week,
        COUNT(*) as total_tasks,
        SUM(CASE WHEN is_paid = 1 THEN 1 ELSE 0 END) as paid_tasks,
        SUM(CASE WHEN is_paid = 0 THEN 1 ELSE 0 END) as unpaid_tasks
    FROM provider_task_billing_status
    GROUP BY billing_week
    ORDER BY billing_week DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def display_justin_payment_tracker():
    """Simple payment tracker for Justin"""
    apply_custom_css()
    
    st.title(get_section_title("Provider Payment Tracker - Justin"))
    st.markdown("### Simple Process Map: Mark Providers as Paid")
    
    # Load data
    with st.spinner("Loading provider tasks..."):
        tasks_df = get_provider_tasks_simple()
        summary_df = get_payment_summary()
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    total_tasks = len(tasks_df)
    paid_tasks = len(tasks_df[tasks_df['payment_status'] == 'PAID'])
    unpaid_tasks = total_tasks - paid_tasks
    
    with col1:
        st.metric("Total Tasks", total_tasks)
    with col2:
        st.metric("Paid Tasks", paid_tasks, delta=f"+{paid_tasks}")
    with col3:
        st.metric("Outstanding Tasks", unpaid_tasks, delta=f"+{unpaid_tasks}")
    
    # Payment processing section
    st.subheader(get_section_title("Mark Tasks as Paid"))
    
    if not tasks_df.empty:
        # Filter unpaid tasks
        unpaid_tasks_df = tasks_df[tasks_df['payment_status'] == 'NOT PAID'].copy()
        
        if not unpaid_tasks_df.empty:
            st.markdown(f"**{len(unpaid_tasks_df)} unpaid tasks available for payment**")
            
            # Allow selection
            selected_task_ids = st.multiselect(
                "Select tasks to mark as paid:",
                options=unpaid_tasks_df['billing_status_id'].tolist(),
                format_func=lambda x: f"{unpaid_tasks_df[unpaid_tasks_df['billing_status_id']==x]['provider_name'].iloc[0]} - {unpaid_tasks_df[unpaid_tasks_df['billing_status_id']==x]['patient_name'].iloc[0]} - {unpaid_tasks_df[unpaid_tasks_df['billing_status_id']==x]['task_date'].iloc[0]}"
            )
            
            if selected_task_ids and st.button("Mark Selected as Paid", type="primary"):
                if mark_tasks_paid(selected_task_ids):
                    st.success(f"Successfully marked {len(selected_task_ids)} tasks as paid!")
                    st.rerun()  # Refresh the data
                else:
                    st.error("Failed to update payments")
            
            # Show unpaid tasks
            st.markdown("#### Outstanding Tasks")
            display_unpaid = unpaid_tasks_df[[
                'provider_name', 'patient_name', 'task_date', 'billing_week', 
                'minutes_of_service', 'task_description'
            ]].copy()
            
            display_unpaid.columns = ['Provider', 'Patient', 'Task Date', 'Week', 'Minutes', 'Description']
            
            st.dataframe(display_unpaid, use_container_width=True)
        else:
            st.success("✅ All tasks are already marked as paid!")
    
    # Weekly summary
    st.subheader(get_section_title("Weekly Payment Summary"))
    
    if not summary_df.empty:
        display_summary = summary_df[[
            'billing_week', 'total_tasks', 'paid_tasks', 'unpaid_tasks'
        ]].copy()
        
        display_summary.columns = ['Week', 'Total Tasks', 'Paid Tasks', 'Unpaid Tasks']
        
        st.dataframe(display_summary, use_container_width=True)
    else:
        st.info("No weekly billing data available yet")
    
    # All tasks (for review)
    with st.expander("View All Tasks (Paid and Unpaid)"):
        if not tasks_df.empty:
            display_all = tasks_df[[
                'provider_name', 'patient_name', 'task_date', 'payment_status',
                'minutes_of_service', 'task_description'
            ]].copy()
            
            display_all.columns = ['Provider', 'Patient', 'Task Date', 'Status', 'Minutes', 'Description']
            
            # Color code by status
            def color_status(val):
                color = 'background-color: #d4edda' if val == 'PAID' else 'background-color: #fff3cd'
                return color
            
            styled = display_all.style.applymap(color_status, subset=['Status'])
            st.dataframe(styled, use_container_width=True)
        else:
            st.info("No provider tasks found")

if __name__ == "__main__":
    display_justin_payment_tracker()