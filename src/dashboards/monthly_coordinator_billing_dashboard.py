"""
Monthly Coordinator Billing Dashboard
Tracks coordinator billing by month using coordinator_monthly_summary tables
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

# Database connection
def get_db_connection():
    return sqlite3.connect('production.db')

def get_available_months():
    """Get list of available months from coordinator_tasks_YYYY_MM tables"""
    conn = get_db_connection()
    try:
        # Get list of all coordinator_tasks tables
        query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name LIKE 'coordinator_tasks_20%'
        ORDER BY name DESC
        """
        tables = conn.execute(query).fetchall()
        
        months = []
        for table in tables:
            table_name = table[0]
            # Extract year and month from table name (coordinator_tasks_YYYY_MM)
            parts = table_name.split('_')
            if len(parts) >= 3:
                try:
                    year = int(parts[2])
                    month = int(parts[3])
                    month_name = calendar.month_name[month]
                    months.append({
                        'year': year,
                        'month': month,
                        'display': f"{month_name} {year}"
                    })
                except (ValueError, IndexError):
                    continue
        
        return sorted(months, key=lambda x: (x['year'], x['month']), reverse=True)
    except Exception as e:
        st.error(f"Error getting available months: {e}")
        return []
    finally:
        conn.close()

def get_coordinator_monthly_summary(year, month):
    """Get coordinator monthly summary data"""
    conn = get_db_connection()
    try:
        table_name = f"coordinator_tasks_{year}_{month:02d}"
        
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = ?
        """, (table_name,))
        
        if not cursor.fetchone():
            return pd.DataFrame()
        
        # Query the coordinator tasks table
        query = f"""
        SELECT 
            coordinator_name,
            COUNT(*) as total_tasks,
            SUM(minutes_of_service) as total_minutes,
            SUM(CASE WHEN is_billed = 1 THEN 1 ELSE 0 END) as billed_tasks,
            SUM(CASE WHEN is_paid = 1 THEN 1 ELSE 0 END) as paid_tasks,
            SUM(CASE WHEN is_carried_over = 1 THEN 1 ELSE 0 END) as carried_over_tasks
        FROM {table_name}
        WHERE coordinator_name IS NOT NULL
        GROUP BY coordinator_name
        ORDER BY total_minutes DESC
        """
        
        df = pd.read_sql_query(query, conn)
        return df
        
    except Exception as e:
        st.error(f"Error getting coordinator summary: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_coordinator_task_details(year, month, coordinator_name):
    """Get detailed task information for a specific coordinator"""
    conn = get_db_connection()
    try:
        table_name = f"coordinator_tasks_{year}_{month:02d}"
        
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name = ?
        """, (table_name,))
        
        if not cursor.fetchone():
            return pd.DataFrame()
        
        query = f"""
        SELECT 
            task_date,
            patient_name,
            patient_id,
            task_description,
            minutes_of_service,
            billing_code,
            billing_status,
            is_billed,
            is_paid,
            is_carried_over,
            billing_notes
        FROM {table_name}
        WHERE coordinator_name = ?
        ORDER BY task_date
        """
        
        df = pd.read_sql_query(query, conn, params=(coordinator_name,))
        return df
        
    except Exception as e:
        st.error(f"Error getting coordinator details: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def create_billing_status_chart(df):
    """Create billing status overview chart"""
    if df.empty:
        return None
    
    # Calculate status counts across all coordinators
    status_data = {
        'Status': ['Billed', 'Paid', 'Carried Over'],
        'Count': [
            df['billed_tasks'].sum(),
            df['paid_tasks'].sum(),
            df['carried_over_tasks'].sum()
        ]
    }
    
    status_df = pd.DataFrame(status_data)
    
    fig = px.bar(
        status_df,
        x='Status',
        y='Count',
        title='Billing Status Overview',
        color='Status',
        color_discrete_map={
            'Billed': '#3498db',
            'Paid': '#2ecc71',
            'Carried Over': '#f39c12'
        }
    )
    
    fig.update_layout(
        height=400,
        showlegend=False,
        title_x=0.5
    )
    
    return fig

def create_minutes_by_coordinator_chart(df):
    """Create minutes by coordinator chart"""
    if df.empty:
        return None
    
    fig = px.bar(
        df.head(10),
        x='coordinator_name',
        y='total_minutes',
        title='Top 10 Coordinators by Minutes',
        labels={'coordinator_name': 'Coordinator', 'total_minutes': 'Total Minutes'},
        color='total_minutes',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        height=500,
        title_x=0.5,
        xaxis_tickangle=-45
    )
    
    return fig

def display_monthly_coordinator_billing_dashboard():
    """Main function to display the monthly coordinator billing dashboard"""
    st.title("Monthly Coordinator Billing Dashboard")
    
    # Get available months
    months = get_available_months()
    
    if not months:
        st.warning("No coordinator billing data available")
        return
    
    # Month selector
    selected_month = st.selectbox(
        "Select Month",
        options=months,
        format_func=lambda x: x['display']
    )
    
    if selected_month:
        year = selected_month['year']
        month = selected_month['month']
        
        st.subheader(f"Billing Summary for {selected_month['display']}")
        
        # Get summary data
        summary_df = get_coordinator_monthly_summary(year, month)
        
        if summary_df.empty:
            st.info(f"No data available for {selected_month['display']}")
            return
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Coordinators", len(summary_df))
        
        with col2:
            total_minutes = summary_df['total_minutes'].sum()
            st.metric("Total Minutes", f"{total_minutes:,}")
        
        with col3:
            total_billed = summary_df['billed_tasks'].sum()
            st.metric("Billed Tasks", total_billed)
        
        with col4:
            total_paid = summary_df['paid_tasks'].sum()
            st.metric("Paid Tasks", total_paid)
        
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Summary", "Charts", "Details"])
        
        with tab1:
            st.subheader("Coordinator Summary")
            st.dataframe(
                summary_df.style.format({
                    'total_minutes': '{:,}',
                    'billed_tasks': '{:,}',
                    'paid_tasks': '{:,}',
                    'carried_over_tasks': '{:,}'
                }),
                use_container_width=True
            )
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                status_chart = create_billing_status_chart(summary_df)
                if status_chart:
                    st.plotly_chart(status_chart, use_container_width=True)
            
            with col2:
                minutes_chart = create_minutes_by_coordinator_chart(summary_df)
                if minutes_chart:
                    st.plotly_chart(minutes_chart, use_container_width=True)
        
        with tab3:
            st.subheader("Coordinator Details")
            
            # Coordinator selector
            coordinator_names = summary_df['coordinator_name'].tolist()
            selected_coordinator = st.selectbox(
                "Select Coordinator",
                options=coordinator_names
            )
            
            if selected_coordinator:
                details_df = get_coordinator_task_details(
                    year, month, selected_coordinator
                )
                
                if not details_df.empty:
                    st.subheader(f"Tasks for {selected_coordinator}")
                    st.dataframe(
                        details_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Display metrics for selected coordinator
                    coord_summary = summary_df[
                        summary_df['coordinator_name'] == selected_coordinator
                    ].iloc[0]
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Tasks", coord_summary['total_tasks'])
                    with col2:
                        st.metric("Total Minutes", f"{coord_summary['total_minutes']:,}")
                    with col3:
                        st.metric("Billed Tasks", coord_summary['billed_tasks'])
                    with col4:
                        st.metric("Paid Tasks", coord_summary['paid_tasks'])
                else:
                    st.info(f"No detailed tasks found for {selected_coordinator}")

# Main execution
if __name__ == "__main__":
    display_monthly_coordinator_billing_dashboard()