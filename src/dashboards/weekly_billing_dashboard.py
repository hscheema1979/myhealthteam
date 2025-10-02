"""
Weekly Billing Dashboard (P00)
Comprehensive dashboard for tracking and managing the weekly billing process.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import calendar
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database import get_db_connection
from src.config.ui_style_config import apply_custom_css
from src.billing.weekly_billing_processor import WeeklyBillingProcessor
from src.auth_module import AuthenticationManager

def get_available_months():
    """Get list of available months from provider_tasks data."""
    conn = get_db_connection()
    
    query = """
    SELECT DISTINCT 
        strftime('%Y', task_date) as year,
        strftime('%m', task_date) as month
    FROM provider_tasks
    WHERE task_date IS NOT NULL
    ORDER BY year DESC, month DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return []
    
    # Convert to list of dictionaries with display names
    months = []
    for _, row in df.iterrows():
        # Skip rows with None values
        if row['year'] is None or row['month'] is None:
            continue
            
        year = int(row['year'])
        month = int(row['month'])
        display = f"{calendar.month_name[month]} {year}"
        months.append({
            'year': year,
            'month': month,
            'display': display
        })
    
    return months

def get_billing_weeks_list(selected_year=None, selected_month=None):
    """Get list of available billing weeks from provider_tasks, optionally filtered by month/year."""
    conn = get_db_connection()
    
    if selected_year and selected_month:
        query = """
        SELECT 
            strftime('%Y-%W', task_date) as billing_week,
            strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
            strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
        FROM provider_tasks
        WHERE strftime('%Y', task_date) = ? 
        AND strftime('%m', task_date) = ?
        AND task_date IS NOT NULL
        GROUP BY strftime('%Y-%W', task_date)
        ORDER BY billing_week DESC
        """
        df = pd.read_sql_query(query, conn, params=[str(selected_year), f"{selected_month:02d}"])
    else:
        query = """
        SELECT 
            strftime('%Y-%W', task_date) as billing_week,
            strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
            strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
        FROM provider_tasks
        WHERE task_date IS NOT NULL
        GROUP BY strftime('%Y-%W', task_date)
        ORDER BY billing_week DESC
        """
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df

def get_billing_weeks_by_date_range(start_date, end_date):
    """Get list of available billing weeks from provider_tasks within a specific date range"""
    try:
        conn = get_db_connection()
        
        query = """
        SELECT 
            strftime('%Y-%W', task_date) as billing_week,
            strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
            strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
        FROM provider_tasks
        WHERE task_date >= ? AND task_date <= ?
        AND task_date IS NOT NULL
        GROUP BY strftime('%Y-%W', task_date)
        ORDER BY billing_week DESC
        """
        df = pd.read_sql_query(query, conn, params=[start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')])
        
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching billing weeks for date range: {str(e)}")
        return pd.DataFrame()

def get_weekly_billing_summary():
    """Get summary of all weekly billing from provider_tasks."""
    conn = get_db_connection()
    
    query = """
    SELECT 
        strftime('%Y-%W', task_date) as billing_week,
        strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
        strftime('%Y-%m-%d', MAX(task_date)) as week_end_date,
        COUNT(*) as total_tasks,
        COUNT(DISTINCT provider_name) as provider_count,
        COUNT(DISTINCT patient_id) as patient_count,
        0 as billed_tasks,
        0 as paid_tasks,
        0 as carried_over_tasks
    FROM provider_tasks
    WHERE task_date IS NOT NULL
    GROUP BY strftime('%Y-%W', task_date)
    ORDER BY billing_week DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df

def get_weekly_billing_summary_filtered(selected_year, selected_month):
    """Get summary of weekly billing from provider_tasks filtered by month/year."""
    conn = get_db_connection()
    
    query = """
    SELECT 
        strftime('%Y-%W', task_date) as billing_week,
        strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
        strftime('%Y-%m-%d', MAX(task_date)) as week_end_date,
        COUNT(*) as total_tasks,
        COUNT(DISTINCT provider_name) as provider_count,
        COUNT(DISTINCT patient_id) as patient_count,
        0 as billed_tasks,
        0 as paid_tasks,
        0 as carried_over_tasks
    FROM provider_tasks
    WHERE strftime('%Y', task_date) = ? 
    AND strftime('%m', task_date) = ?
    AND task_date IS NOT NULL
    GROUP BY strftime('%Y-%W', task_date)
    ORDER BY billing_week DESC
    """
    
    df = pd.read_sql_query(query, conn, params=[str(selected_year), f"{selected_month:02d}"])
    conn.close()
    
    return df

def get_provider_billing_details(billing_week):
    """Get detailed billing information for a specific week from provider_tasks."""
    conn = get_db_connection()
    
    query = """
    SELECT 
        provider_task_id,
        provider_id,
        provider_name,
        patient_name,
        task_date,
        task_description,
        minutes_of_service,
        billing_code,
        billing_code_description,
        billing_status,
        is_billed,
        is_invoiced,
        is_claim_submitted,
        is_insurance_processed,
        is_approved_to_pay,
        is_paid,
        is_carried_over,
        provider_paid,
        billing_week,
        original_billing_week,
        carryover_reason,
        billing_notes,
        billed_date,
        invoiced_date,
        claim_submitted_date,
        insurance_processed_date,
        approved_to_pay_date,
        paid_date
    FROM provider_tasks
    WHERE billing_week = ?
    AND task_date IS NOT NULL
    ORDER BY provider_name, task_date
    """
    
    df = pd.read_sql_query(query, conn, params=[billing_week])
    conn.close()
    
    return df


def update_task_billing_status(provider_task_id, status_field, value, notes=None):
    """Update a specific billing status field for a task."""
    conn = get_db_connection()
    
    # Map status fields to their corresponding date fields
    date_fields = {
        'is_billed': 'billed_date',
        'is_invoiced': 'invoiced_date', 
        'is_claim_submitted': 'claim_submitted_date',
        'is_insurance_processed': 'insurance_processed_date',
        'is_approved_to_pay': 'approved_to_pay_date',
        'is_paid': 'paid_date'
    }
    
    try:
        cursor = conn.cursor()
        
        # Build the update query
        update_fields = [f"{status_field} = ?"]
        params = [value]
        
        # If setting to 1 (true), also update the corresponding date
        if value == 1 and status_field in date_fields:
            update_fields.append(f"{date_fields[status_field]} = CURRENT_TIMESTAMP")
        
        # Update billing_status based on the field being updated
        if status_field == 'is_billed' and value == 1:
            update_fields.append("billing_status = 'Billed'")
        elif status_field == 'is_paid' and value == 1:
            update_fields.append("billing_status = 'Paid'")
        
        # Add notes if provided
        if notes:
            update_fields.append("billing_notes = ?")
            params.append(notes)
        
        # Always update the updated_date
        update_fields.append("updated_date = CURRENT_TIMESTAMP")
        
        query = f"""
        UPDATE provider_tasks 
        SET {', '.join(update_fields)}
        WHERE provider_task_id = ?
        """
        params.append(provider_task_id)
        
        cursor.execute(query, params)
        conn.commit()
        
        return True, "Status updated successfully"
        
    except Exception as e:
        return False, f"Error updating status: {str(e)}"
    finally:
        conn.close()


def bulk_update_billing_status(task_ids, status_field, value, notes=None):
    """Update billing status for multiple tasks."""
    conn = get_db_connection()
    
    try:
        cursor = conn.cursor()
        success_count = 0
        
        for task_id in task_ids:
            success, message = update_task_billing_status(task_id, status_field, value, notes)
            if success:
                success_count += 1
        
        return True, f"Updated {success_count} out of {len(task_ids)} tasks"
        
    except Exception as e:
        return False, f"Error in bulk update: {str(e)}"
    finally:
        conn.close()


def update_selected_tasks_status(filtered_df, new_status):
    """Update billing status for all tasks in the filtered dataframe."""
    try:
        conn = get_db_connection()
        task_ids = filtered_df['provider_task_id'].tolist()
        
        # Update billing_status for all selected tasks
        for task_id in task_ids:
            conn.execute(
                "UPDATE provider_tasks SET billing_status = ? WHERE provider_task_id = ?",
                (new_status, task_id)
            )
        
        conn.commit()
        conn.close()
        
        st.success(f"Updated {len(task_ids)} tasks to status: {new_status}")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error updating status: {str(e)}")

def update_provider_paid_status(filtered_df):
    """Update provider_paid status for all tasks in the filtered dataframe."""
    try:
        conn = get_db_connection()
        task_ids = filtered_df['provider_task_id'].tolist()
        
        # Update provider_paid to 1 for all selected tasks
        for task_id in task_ids:
            conn.execute(
                "UPDATE provider_tasks SET provider_paid = 1 WHERE provider_task_id = ?",
                (task_id,)
            )
        
        conn.commit()
        conn.close()
        
        st.success(f"Marked {len(task_ids)} tasks as provider paid")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error updating provider paid status: {str(e)}")


def get_tasks_requiring_attention():
    """Get tasks that require billing attention."""
    conn = get_db_connection()
    
    query = """
    SELECT 
        provider_task_id,
        provider_name,
        patient_name,
        task_date,
        billing_code,
        minutes_of_service,
        billing_status,
        billing_notes
    FROM provider_tasks
    WHERE billing_status = 'Not Billed' 
    AND is_billed = 0
    AND (billing_code IS NULL OR billing_code = '' OR billing_code = 'Not_Billable')
    ORDER BY task_date DESC
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    return df


def create_billing_status_overview_chart(df):
    """Create overview chart of billing statuses."""
    if df.empty:
        return None
    
    status_counts = df['billing_status'].value_counts()
    
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Billing Status Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        title_x=0.5
    )
    
    return fig

def create_provider_performance_chart(df):
    """Create provider performance chart."""
    if df.empty:
        return None
    
    provider_summary = df.groupby('provider_name').agg({
        'billing_status': 'count',
        'is_billed': 'sum',
        'is_paid': 'sum',
        'minutes_of_service': 'sum'
    }).reset_index()
    
    provider_summary.columns = ['Provider', 'Total Tasks', 'Billed Tasks', 'Paid Tasks', 'Total Minutes']
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Total Tasks',
        x=provider_summary['Provider'],
        y=provider_summary['Total Tasks'],
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        name='Billed Tasks',
        x=provider_summary['Provider'],
        y=provider_summary['Billed Tasks'],
        marker_color='green'
    ))
    
    fig.add_trace(go.Bar(
        name='Paid Tasks',
        x=provider_summary['Provider'],
        y=provider_summary['Paid Tasks'],
        marker_color='darkgreen'
    ))
    
    fig.update_layout(
        title="Provider Billing Performance",
        xaxis_title="Provider",
        yaxis_title="Number of Tasks",
        barmode='group',
        height=400
    )
    
    return fig

def create_weekly_trend_chart(summary_df):
    """Create weekly billing trend chart."""
    if summary_df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=summary_df['billing_week'],
        y=summary_df['total_tasks'],
        mode='lines+markers',
        name='Total Tasks',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=summary_df['billing_week'],
        y=summary_df['billed_tasks'],
        mode='lines+markers',
        name='Billed Tasks',
        line=dict(color='green')
    ))
    
    fig.add_trace(go.Scatter(
        x=summary_df['billing_week'],
        y=summary_df['paid_tasks'],
        mode='lines+markers',
        name='Paid Tasks',
        line=dict(color='darkgreen')
    ))
    
    fig.add_trace(go.Scatter(
        x=summary_df['billing_week'],
        y=summary_df['carried_over_tasks'],
        mode='lines+markers',
        name='Carried Over Tasks',
        line=dict(color='orange')
    ))
    
    fig.update_layout(
        title="Weekly Billing Trends",
        xaxis_title="Billing Week",
        yaxis_title="Number of Tasks",
        height=400,
        hovermode='x unified'
    )
    
    return fig

def create_billing_pipeline_chart(df):
    """Create billing pipeline funnel chart."""
    if df.empty:
        return None
    
    pipeline_data = {
        'Not Billed': len(df[df['billing_status'] == 'Not Billed']),
        'Billed': len(df[df['is_billed'] == 1]),
        'Invoiced': len(df[df['is_invoiced'] == 1]),
        'Claim Submitted': len(df[df['is_claim_submitted'] == 1]),
        'Insurance Processed': len(df[df['is_insurance_processed'] == 1]),
        'Approve to Pay': len(df[df['is_approved_to_pay'] == 1]),
        'Paid': len(df[df['is_paid'] == 1])
    }
    
    fig = go.Figure(go.Funnel(
        y=list(pipeline_data.keys()),
        x=list(pipeline_data.values()),
        textinfo="value+percent initial"
    ))
    
    fig.update_layout(
        title="Billing Pipeline Funnel",
        height=500
    )
    
    return fig

def display_weekly_billing_dashboard():
    """Main dashboard display function."""
    # Note: set_page_config is handled by the main app when used as a module
    apply_custom_css()
    
    # Access control - restrict to Justin and Harpreet only
    auth_manager = AuthenticationManager()
    if not auth_manager.is_authenticated():
        st.error("Please log in to access the billing dashboard.")
        return
    
    # Get current user ID
    current_user_id = st.session_state.get('user_id')
    
    # Check if user is Justin (18) or Harpreet (12)
    if current_user_id not in [12, 18]:
        st.error("Access denied. This billing report is restricted to authorized personnel only.")
        st.info("Please contact your administrator if you need access to billing reports.")
        return
    
    # Initialize processor
    processor = WeeklyBillingProcessor()
    
    # Date selection controls
    st.subheader("Date Selection")
    
    # Selection mode
    selection_mode = st.radio(
        "Selection Mode:",
        ["Month Selection", "Custom Date Range"],
        horizontal=True
    )
    
    if selection_mode == "Month Selection":
        # Get available months
        available_months = get_available_months()
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        col1, col2 = st.columns(2)
        
        with col1:
            if available_months:
                # Create month options for selectbox
                month_options = [month['display'] for month in available_months]
                
                # Default to current month if available, otherwise first available
                default_index = 0
                for i, month_data in enumerate(available_months):
                    if month_data['year'] == current_year and month_data['month'] == current_month:
                        default_index = i
                        break
                
                selected_month_display = st.selectbox(
                    "Select Month:",
                    options=month_options,
                    index=default_index
                )
                
                # Find selected month data
                selected_month_data = next(
                    month for month in available_months 
                    if month['display'] == selected_month_display
                )
                selected_year = selected_month_data['year']
                selected_month = selected_month_data['month']
            else:
                st.warning("No billing data available")
                selected_year, selected_month = current_year, current_month
        
        with col2:
            st.metric("Selected Period", f"{calendar.month_name[selected_month]} {selected_year}")
        
        # Week selection within selected month
        weeks_df = get_billing_weeks_list(selected_year, selected_month)
        date_filter_type = "month"
        start_date = None
        end_date = None
        
    else:  # Custom Date Range
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input(
                "Start Date:",
                value=datetime.now().date() - timedelta(days=30)
            )
        
        with col2:
            end_date = st.date_input(
                "End Date:",
                value=datetime.now().date()
            )
        
        if start_date and end_date and start_date <= end_date:
            st.metric("Selected Range", f"{start_date} to {end_date}")
            # Get weeks within date range
            weeks_df = get_billing_weeks_by_date_range(start_date, end_date)
            selected_year = None
            selected_month = None
            date_filter_type = "range"
        else:
            st.error("Please select a valid date range (start date must be before or equal to end date)")
            weeks_df = pd.DataFrame()
            date_filter_type = "range"
    
    # Sidebar controls
    st.sidebar.header("Dashboard Controls")
    
    # Week selection
    if not weeks_df.empty:
        week_options = ['All Weeks'] + [f"{row['billing_week']} ({row['week_start_date']} to {row['week_end_date']})" 
                       for _, row in weeks_df.iterrows()]
        selected_week_display = st.sidebar.selectbox("Select Billing Week", week_options)
        
        if selected_week_display == 'All Weeks':
            selected_week = None
            selected_weeks = weeks_df['billing_week'].tolist()
        else:
            selected_week = selected_week_display.split(' ')[0]
            selected_weeks = [selected_week]
    else:
        if date_filter_type == "month" and selected_year and selected_month:
            st.sidebar.warning(f"No billing weeks found for {calendar.month_name[selected_month]} {selected_year}")
        elif date_filter_type == "range":
            st.sidebar.warning(f"No billing weeks found for the selected date range")
        else:
            st.sidebar.warning("No billing weeks available")
        selected_week = None
        selected_weeks = []
    
    # Removed unnecessary action buttons for cleaner interface
    
    # Main dashboard content
    if selected_weeks:
        # Get data for selected week(s)
        if selected_week:
            # Single week selected
            details_df = get_provider_billing_details(selected_week)
            st.subheader(f"Week {selected_week} Details")
        else:
            # Multiple weeks selected (All Weeks)
            details_df = pd.DataFrame()
            for week in selected_weeks:
                week_data = get_provider_billing_details(week)
                if not week_data.empty:
                    details_df = pd.concat([details_df, week_data], ignore_index=True)
            st.subheader(f"All Weeks in {calendar.month_name[selected_month]} {selected_year}")
        
        # Get summary data
        if date_filter_type == "month" and selected_year and selected_month:
            summary_df = get_weekly_billing_summary_filtered(selected_year, selected_month)
        else:
            summary_df = get_weekly_billing_summary()
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        if not details_df.empty:
            with col1:
                st.metric("Total Tasks", len(details_df))
            
            with col2:
                billed_count = len(details_df[details_df['is_billed'] == 1])
                st.metric("Billed Tasks", billed_count)
            
            with col3:
                paid_count = len(details_df[details_df['is_paid'] == 1])
                st.metric("Paid Tasks", paid_count)
            
            with col4:
                carryover_count = len(details_df[details_df['is_carried_over'] == 1])
                st.metric("Carried Over", carryover_count)
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            status_chart = create_billing_status_overview_chart(details_df)
            if status_chart:
                st.plotly_chart(status_chart, use_container_width=True)
        
        with col2:
            provider_chart = create_provider_performance_chart(details_df)
            if provider_chart:
                st.plotly_chart(provider_chart, use_container_width=True)
        
        # Pipeline and trends
        col1, col2 = st.columns(2)
        
        with col1:
            pipeline_chart = create_billing_pipeline_chart(details_df)
            if pipeline_chart:
                st.plotly_chart(pipeline_chart, use_container_width=True)
        
        with col2:
            trend_chart = create_weekly_trend_chart(summary_df)
            if trend_chart:
                st.plotly_chart(trend_chart, use_container_width=True)
        
        # Detailed data tables
        st.subheader("Detailed Task Information")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            providers = ['All'] + sorted(details_df['provider_name'].unique().tolist()) if not details_df.empty else ['All']
            selected_provider = st.selectbox("Filter by Provider", providers)
        
        with col2:
            statuses = ['All'] + sorted(details_df['billing_status'].unique().tolist()) if not details_df.empty else ['All']
            selected_status = st.selectbox("Filter by Status", statuses)
        
        with col3:
            show_carryover = st.checkbox("Show only carried over tasks")
        
        # Apply filters
        filtered_df = details_df.copy()
        
        if selected_provider != 'All':
            filtered_df = filtered_df[filtered_df['provider_name'] == selected_provider]
        
        if selected_status != 'All':
            filtered_df = filtered_df[filtered_df['billing_status'] == selected_status]
        
        if show_carryover:
            filtered_df = filtered_df[filtered_df['is_carried_over'] == 1]
        
        # Display filtered data
        if not filtered_df.empty:
            # Format display columns
            display_columns = [
                'provider_name', 'patient_name', 'task_date', 'task_description',
                'minutes_of_service', 'billing_code', 'billing_status',
                'is_billed', 'is_paid', 'provider_paid', 'is_carried_over'
            ]
            
            display_df = filtered_df[display_columns].copy()
            display_df.columns = [
                'Provider', 'Patient', 'Task Date', 'Description',
                'Minutes', 'Billing Code', 'Status',
                'Billed', 'Paid', 'Provider Paid', 'Carried Over'
            ]
            
            st.dataframe(display_df, use_container_width=True)
            
            # Export options
            col1, col2 = st.columns(2)
            
            with col1:
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name=f"billing_report_{selected_week}.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.write("**Update Billing Status**")
                
                if not filtered_df.empty:
                    # Simple status dropdown
                    status_options = [
                        "Invoiced",
                        "Claim Submitted", 
                        "Insurance Processed",
                        "Approve to Pay",
                        "Paid (Medicare)",
                        "Provider Paid"
                    ]
                    
                    selected_status = st.selectbox(
                        "Select new status:",
                        options=status_options,
                        key="status_update_select"
                    )
                    
                    if st.button("Update All Filtered Tasks", key="update_status_btn"):
                        if selected_status == "Provider Paid":
                            update_provider_paid_status(filtered_df)
                        else:
                            update_selected_tasks_status(filtered_df, selected_status)
        
        else:
            st.info("No tasks found for the selected filters")
        
        # Tasks requiring attention
        st.subheader("Tasks Requiring Attention")
        
        attention_df = filtered_df[
            (filtered_df['billing_status'] == 'Not Billed') & 
            (filtered_df['is_billed'] == 0)
        ]
        
        if not attention_df.empty:
            st.warning(f"Found {len(attention_df)} tasks that require attention")
            
            attention_display = attention_df[[
                'provider_name', 'patient_name', 'task_date', 'billing_code', 
                'minutes_of_service', 'billing_notes'
            ]].copy()
            
            attention_display.columns = [
                'Provider', 'Patient', 'Task Date', 'Billing Code', 
                'Minutes', 'Notes'
            ]
            
            st.dataframe(attention_display, use_container_width=True)
        else:
            st.success("No tasks requiring attention")
    
    else:
        st.info("Please select a billing week or initialize the system to get started")
        
        # Show system status
        st.subheader("System Status")
        
        # Check if tables exist
        conn = get_db_connection()
        
        table_check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('weekly_billing_reports', 'provider_task_billing_status')
        """
        
        existing_tables = pd.read_sql_query(table_check_query, conn)
        conn.close()
        
        if len(existing_tables) == 2:
            st.success("Billing system tables are set up correctly")
        else:
            st.warning("Billing system tables not found. Please initialize the system.")

if __name__ == "__main__":
    display_weekly_billing_dashboard()