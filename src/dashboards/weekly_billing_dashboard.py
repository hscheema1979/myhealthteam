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
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import get_db_connection, get_weekly_billing_summary_realtime, get_provider_billing_status_realtime
from config.ui_style_config import apply_custom_css

def get_available_months():
    """Get list of available months from provider_tasks data including partitioned tables."""
    conn = get_db_connection()
    
    # Check which tables exist
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'provider_tasks%'
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    if not existing_tables:
        conn.close()
        return []
    
    # Build query dynamically based on existing tables
    queries = []
    
    # Add queries for each existing table
    for table in existing_tables:
        queries.append(f"""
            SELECT
                strftime('%Y', task_date) as year,
                strftime('%m', task_date) as month,
                '{table}' as source_table
            FROM {table}
            WHERE task_date IS NOT NULL
        """)
    
    # Combine all queries with UNION
    query = " UNION ".join(queries) + " ORDER BY year DESC, month DESC"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        return []
    
    # Remove duplicates and convert to list of dictionaries with display names
    months_dict = {}
    for _, row in df.iterrows():
        # Skip rows with None values
        if row['year'] is None or row['month'] is None:
            continue
            
        year = int(row['year'])
        month = int(row['month'])
        key = f"{year}-{month:02d}"
        
        # Only add if not already exists
        if key not in months_dict:
            display = f"{calendar.month_name[month]} {year}"
            months_dict[key] = {
                'year': year,
                'month': month,
                'display': display
            }
    
    return list(months_dict.values())

def get_billing_weeks_list(selected_year=None, selected_month=None):
    """Get list of available billing weeks from provider_tasks including partitioned tables, optionally filtered by month/year."""
    conn = get_db_connection()
    
    # Check which tables exist
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'provider_tasks%'
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    if not existing_tables:
        conn.close()
        return pd.DataFrame()
    
    if selected_year and selected_month:
        # Build table name for the selected year/month
        table_name = f'provider_tasks_{selected_year}_{selected_month:02d}'
        
        if table_name in existing_tables:
            # Use the specific partitioned table
            query = f"""
            SELECT
                strftime('%Y-%W', task_date) as billing_week,
                strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
                strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
            FROM {table_name}
            WHERE strftime('%Y', task_date) = ?
            AND strftime('%m', task_date) = ?
            AND task_date IS NOT NULL
            GROUP BY strftime('%Y-%W', task_date)
            ORDER BY billing_week DESC
            """
            df = pd.read_sql_query(query, conn, params=[str(selected_year), f"{selected_month:02d}"])
        else:
            # No data for this month/year combination
            conn.close()
            return pd.DataFrame()
    else:
        # Get all billing weeks from all existing tables
        queries = []
        for table in existing_tables:
            queries.append(f"""
                SELECT
                    strftime('%Y-%W', task_date) as billing_week,
                    strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
                    strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
                FROM {table}
                WHERE task_date IS NOT NULL
                GROUP BY strftime('%Y-%W', task_date)
            """)
        
        # Combine all queries
        query = " UNION ".join(queries) + " ORDER BY billing_week DESC"
        df = pd.read_sql_query(query, conn)
    
    conn.close()
    return df

def get_billing_weeks_by_date_range(start_date, end_date):
    """Get list of available billing weeks from provider_tasks within a specific date range"""
    try:
        conn = get_db_connection()
        
        # Check which tables exist
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'provider_tasks%'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        if not existing_tables:
            conn.close()
            return pd.DataFrame()
        
        # Build query to search across all existing tables
        queries = []
        for table in existing_tables:
            queries.append(f"""
                SELECT
                    strftime('%Y-%W', task_date) as billing_week,
                    strftime('%Y-%m-%d', MIN(task_date)) as week_start_date,
                    strftime('%Y-%m-%d', MAX(task_date)) as week_end_date
                FROM {table}
                WHERE task_date >= ? AND task_date <= ?
                AND task_date IS NOT NULL
                GROUP BY strftime('%Y-%W', task_date)
            """)
        
        # Combine all queries
        query = " UNION ".join(queries) + " ORDER BY billing_week DESC"
        
        df = pd.read_sql_query(query, conn, params=[
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        ])
        
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching billing weeks for date range: {str(e)}")
        return pd.DataFrame()

def get_weekly_billing_summary():
    """Get summary of all weekly billing using real-time data generation."""
    # Use real-time data generation to get billing summary
    return get_weekly_billing_summary_realtime()

def get_weekly_billing_summary_filtered(selected_year, selected_month):
    """Get summary of weekly billing using real-time data generation."""
    # Calculate date range for the selected month
    import calendar
    end_date = datetime(selected_year, selected_month, calendar.monthrange(selected_year, selected_month)[1])
    start_date = datetime(selected_year, selected_month, 1)
    
    # Get real-time billing data for this month
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    billing_data = get_provider_billing_status_realtime(start_str, end_str)
    
    if billing_data.empty:
        return pd.DataFrame()
    
    # Group by billing week and summarize
    weekly_summary = billing_data.groupby('billing_week').agg({
        'provider_task_id': 'count',
        'minutes_of_service': 'sum',
        'is_billed': 'sum',
        'is_paid': 'sum',
        'is_carried_over': 'sum'
    }).reset_index()
    
    weekly_summary.columns = ['billing_week', 'total_tasks', 'total_minutes', 'billed_tasks', 'paid_tasks', 'carried_over_tasks']
    return weekly_summary.sort_values('billing_week', ascending=False)

def get_weekly_billing_summary_by_week(billing_week):
    """Get summary of weekly billing for a specific week from provider_tasks including partitioned tables."""
    conn = get_db_connection()
    
    # Check which tables exist
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'provider_tasks%'
    """)
    existing_tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    if not existing_tables:
        conn.close()
        return pd.DataFrame()
    
    # Parse billing week to determine which table to query
    if '-' in billing_week:
        year, week = billing_week.split('-')
        year = int(year)
        
        # Try each existing table until we find data
        df = pd.DataFrame()
        for table in existing_tables:
            query = f"""
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
            FROM {table}
            WHERE strftime('%Y-%W', task_date) = ?
            AND task_date IS NOT NULL
            GROUP BY strftime('%Y-%W', task_date)
            """
            df = pd.read_sql_query(query, conn, params=[billing_week])
            
            # If we found data, stop searching
            if not df.empty:
                break
    else:
        # Fallback: try all tables if billing_week format is unexpected
        df = pd.DataFrame()
        for table in existing_tables:
            query = f"""
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
            FROM {table}
            WHERE strftime('%Y-%W', task_date) = ?
            AND task_date IS NOT NULL
            GROUP BY strftime('%Y-%W', task_date)
            """
            df = pd.read_sql_query(query, conn, params=[billing_week])
            
            # If we found data, stop searching
            if not df.empty:
                break
    
    conn.close()
    return df

def get_provider_billing_details(billing_week):
    """Get detailed billing information for a specific week using real-time data generation."""
    # Use real-time provider billing status function
    # The billing_week is in format 'YYYY-WW', so we need to convert to date range
    
    try:
        # Parse billing week to get date range
        if '-' in billing_week:
            year, week = billing_week.split('-')
            year = int(year)
            week_num = int(week)
            
            # Calculate approximate date range for this billing week
            # Get the Monday of the specified week
            import calendar
            jan_1 = datetime(year, 1, 1)
            # Calculate the Monday of the given week
            week_start = jan_1 + timedelta(days=(week_num - 1) * 7)
            week_start = week_start - timedelta(days=week_start.weekday())
            week_end = week_start + timedelta(days=6)
            
            start_date = week_start.strftime('%Y-%m-%d')
            end_date = week_end.strftime('%Y-%m-%d')
            
            # Get real-time billing data for this date range
            billing_data = get_provider_billing_status_realtime(start_date, end_date)
            
            # Filter to the specific billing week
            if not billing_data.empty and 'billing_week' in billing_data.columns:
                filtered_data = billing_data[billing_data['billing_week'] == billing_week]
                return filtered_data
            else:
                return pd.DataFrame()
        else:
            # Fallback: return empty dataframe if billing_week format is unexpected
            return pd.DataFrame()
            
    except Exception as e:
        print(f"Error in get_provider_billing_details: {str(e)}")
        return pd.DataFrame()


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
    """Get tasks that require billing attention using real-time data."""
    # Get recent billing data to check for tasks needing attention
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    billing_data = get_provider_billing_status_realtime(start_date, end_date)
    
    if billing_data.empty:
        return pd.DataFrame()
    
    # Filter tasks that need attention: Not Billed and missing billing codes
    attention_tasks = billing_data[
        (billing_data['billing_status'] == 'Not Billed') &
        ((billing_data['billing_code'].isna()) | 
         (billing_data['billing_code'] == '') | 
         (billing_data['billing_code'] == 'Not_Billable'))
    ]
    
    # Select relevant columns for display
    display_columns = [
        'provider_task_id', 'provider_name', 'patient_name', 'task_date',
        'billing_code', 'minutes_of_service', 'billing_status', 'billing_notes'
    ]
    
    return attention_tasks[display_columns] if not attention_tasks.empty else pd.DataFrame()


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

def create_facility_chart(df):
    """Create facility billing chart showing billing per facility."""
    if df.empty:
        return None
    
    # Use patient_name as proxy for facility since we don't have explicit facility column
    # This limitation should be noted for future improvement
    if 'patient_name' not in df.columns:
        st.warning("Patient name column not found - cannot create facility chart")
        return None
    
    # Group by patient name (facility proxy) and aggregate billing data
    facility_summary = df.groupby('patient_name').agg({
        'provider_task_id': 'count',
        'is_billed': 'sum',
        'is_paid': 'sum',
        'minutes_of_service': 'sum',
        'billing_status': lambda x: len(x[x == 'Not Billed'])  # Count of unbilled tasks
    }).reset_index()
    
    facility_summary.columns = ['Facility', 'Total Tasks', 'Billed Tasks', 'Paid Tasks', 'Total Minutes', 'Unbilled Tasks']
    
    # Create subplots for multiple facility metrics
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Facility Billing Performance (Tasks)', 'Facility Revenue Impact (Minutes)'),
        vertical_spacing=0.1
    )
    
    # First subplot: Task counts
    fig.add_trace(go.Bar(
        name='Total Tasks',
        x=facility_summary['Facility'],
        y=facility_summary['Total Tasks'],
        marker_color='lightblue',
        text=facility_summary['Total Tasks'],
        textposition='outside'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        name='Billed Tasks',
        x=facility_summary['Facility'],
        y=facility_summary['Billed Tasks'],
        marker_color='green',
        text=facility_summary['Billed Tasks'],
        textposition='outside'
    ), row=1, col=1)
    
    fig.add_trace(go.Bar(
        name='Paid Tasks',
        x=facility_summary['Facility'],
        y=facility_summary['Paid Tasks'],
        marker_color='darkgreen',
        text=facility_summary['Paid Tasks'],
        textposition='outside'
    ), row=1, col=1)
    
    # Second subplot: Minutes of service
    fig.add_trace(go.Bar(
        name='Total Minutes',
        x=facility_summary['Facility'],
        y=facility_summary['Total Minutes'],
        marker_color='orange',
        text=facility_summary['Total Minutes'],
        textposition='outside',
        showlegend=False
    ), row=2, col=1)
    
    fig.update_layout(
        title="Facility Billing Analysis",
        height=600,
        barmode='group',
        title_x=0.5
    )
    
    # Update x-axis labels to be readable
    fig.update_xaxes(tickangle=45, row=1, col=1)
    fig.update_xaxes(tickangle=45, row=2, col=1)
    
    # Update y-axis titles
    fig.update_yaxes(title_text="Number of Tasks", row=1, col=1)
    fig.update_yaxes(title_text="Total Minutes", row=2, col=1)
    
    return fig

def display_weekly_billing_dashboard():
    """Main dashboard display function."""
    apply_custom_css()
    
    st.title("Weekly Billing Dashboard")
    st.markdown("### Healthcare Provider Billing Management")
    
    # Initialize variables
    selected_year = None
    selected_month = None
    selected_week = None
    selected_weeks = []
    start_date = None
    end_date = None
    date_filter_type = None
    
    # Enhanced selection controls
    st.subheader("Selection Options")
    
    # Selection mode with enhanced options
    selection_mode = st.radio(
        "Primary Selection Mode:",
        ["Month Selection", "Week Selection", "Custom Date Range"],
        horizontal=True,
        key="primary_selection_mode"
    )
    
    if selection_mode == "Month Selection":
        # Get available months
        available_months = get_available_months()
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        col1, col2, col3 = st.columns(3)
        
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
                    index=default_index,
                    key="month_selection"
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
        
        with col3:
            if not weeks_df.empty:
                week_options = ['All Weeks'] + [f"{row['billing_week']} ({row['week_start_date']} to {row['week_end_date']})" 
                               for _, row in weeks_df.iterrows()]
                selected_week_display = st.selectbox("Select Billing Week", week_options, key="month_week_selection")
                
                if selected_week_display == 'All Weeks':
                    selected_week = None
                    selected_weeks = weeks_df['billing_week'].tolist()
                else:
                    selected_week = selected_week_display.split(' ')[0]
                    selected_weeks = [selected_week]
            else:
                st.warning(f"No billing weeks found for {calendar.month_name[selected_month]} {selected_year}")
                selected_week = None
                selected_weeks = []
        
        date_filter_type = "month"
        start_date = None
        end_date = None
        
    elif selection_mode == "Week Selection":
        # Direct week selection - get all available weeks
        all_weeks_df = get_billing_weeks_list()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not all_weeks_df.empty:
                # Create week options for selectbox
                week_options = [f"{row['billing_week']} ({row['week_start_date']} to {row['week_end_date']})" 
                               for _, row in all_weeks_df.iterrows()]
                
                selected_week_display = st.selectbox(
                    "Select Week:",
                    options=week_options,
                    key="week_selection_mode_select"
                )
                
                # Extract billing week from selection
                selected_week = selected_week_display.split(' ')[0]
                selected_weeks = [selected_week]
                
                # Set for compatibility with existing code
                selected_year = int(selected_week.split('-')[0])
                # Calculate month from week (approximate for display)
                week_num = int(selected_week.split('-')[1])
                # This is an approximation, as week 1 might span two months
                # For display purposes, we can take the month of the middle day of the week
                first_day_of_year = datetime(selected_year, 1, 1)
                # Get the date of the first day of the selected week
                # Assuming ISO week date (week 1 starts with the first Thursday of the year)
                # This calculation is simplified and might not be perfectly accurate for all edge cases
                selected_week_start_date = first_day_of_year + timedelta(weeks=week_num - 1)
                selected_month = selected_week_start_date.month

                date_filter_type = "week"
                start_date = None
                end_date = None
            else:
                st.warning("No billing weeks available")
                selected_week = None
                selected_weeks = []
                selected_year = None
                selected_month = None
                date_filter_type = "week"
                start_date = None
                end_date = None
        
        with col2:
            if selected_week:
                st.metric("Selected Week", selected_week)
            else:
                st.metric("Selected Week", "None")
        
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
    
    
    
    # Removed unnecessary action buttons for cleaner interface
    
    # Main dashboard content
    if selected_weeks:
        # Get data for selected week(s)
        if selected_week:
            # Single week selected
            details_df = get_provider_billing_details(selected_week)
            report_title = f"Week {selected_week} Report"
        else:
            # Multiple weeks selected (All Weeks)
            details_df = pd.DataFrame()
            for week in selected_weeks:
                week_data = get_provider_billing_details(week)
                if not week_data.empty:
                    details_df = pd.concat([details_df, week_data], ignore_index=True)
            if selected_year and selected_month:
                report_title = f"All Weeks in {calendar.month_name[selected_month]} {selected_year}"
            else:
                report_title = f"Multiple Weeks Report"
        
        # Get summary data
        if selected_week:
            summary_df = get_weekly_billing_summary_by_week(selected_week)
        elif date_filter_type == "month" and selected_year and selected_month:
            summary_df = get_weekly_billing_summary_filtered(selected_year, selected_month)
        else:
            summary_df = get_weekly_billing_summary()
        
        # ========================================
        # SECTION 1: WEEKLY REPORT (READ-ONLY SUMMARY)
        # ========================================
        st.subheader(report_title)
        st.markdown("---")
        
        # Key metrics row for Weekly Report
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
        
        # Summary charts for Weekly Report
        col1, col2, col3 = st.columns(3)
        
        with col1:
            provider_chart = create_provider_performance_chart(details_df)
            if provider_chart:
                st.plotly_chart(provider_chart, use_container_width=True)
        
        with col2:
            trend_chart = create_weekly_trend_chart(summary_df)
            if trend_chart:
                st.plotly_chart(trend_chart, use_container_width=True)
        
        with col3:
            facility_chart = create_facility_chart(details_df)
            if facility_chart:
                st.plotly_chart(facility_chart, use_container_width=True)
        
        # Weekly Summary Table (Read-only)
        if not details_df.empty:
            st.subheader("Weekly Summary Table")
            
            # Create summary by provider
            provider_summary = details_df.groupby('provider_name').agg({
                'provider_task_id': 'count',
                'minutes_of_service': 'sum',
                'is_billed': 'sum',
                'is_paid': 'sum',
                'is_carried_over': 'sum'
            }).reset_index()
            
            provider_summary.columns = ['Provider', 'Total Tasks', 'Total Minutes', 'Billed Tasks', 'Paid Tasks', 'Carried Over']
            provider_summary['Billed Rate'] = (provider_summary['Billed Tasks'] / provider_summary['Total Tasks'] * 100).round(1)
            provider_summary['Paid Rate'] = (provider_summary['Paid Tasks'] / provider_summary['Total Tasks'] * 100).round(1)
            
            st.dataframe(provider_summary, use_container_width=True)
        
        # ========================================
        # SECTION 2: BILLING STATUS (DETAILED MANAGEMENT)
        # ========================================
        st.markdown("---")
        st.subheader("Billing Status Management")
        
        # Status overview chart
        col1, col2, col3 = st.columns(3)
        
        with col1:
            status_chart = create_billing_status_overview_chart(details_df)
            if status_chart:
                st.plotly_chart(status_chart, use_container_width=True)
        
        with col2:
            pipeline_chart = create_billing_pipeline_chart(details_df)
            if pipeline_chart:
                st.plotly_chart(pipeline_chart, use_container_width=True)
        
        with col3:
            facility_chart = create_facility_chart(details_df)
            if facility_chart:
                st.plotly_chart(facility_chart, use_container_width=True)
        
        # Detailed data tables
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
                            update_selected_tasks_status(filtered_df, selected_df)

        
        # Detailed data tables
        
        else:
            st.info("No tasks found for the selected filters")
        
        # Tasks requiring attention
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