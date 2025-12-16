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
        st.error(f"Error fetching available months: {e}")
        return []
    finally:
        conn.close()

def get_coordinator_billing_data(year, month):
    """Get patient billing data for a specific month from patient_monthly_billing table"""
    conn = get_db_connection()
    try:
        table_name = f"patient_monthly_billing_{year}_{month:02d}"
        
        # Check if table exists
        check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name = ?
        """
        table_exists = conn.execute(check_query, (table_name,)).fetchone()
        
        if not table_exists:
            st.warning(f"Table {table_name} does not exist")
            return pd.DataFrame()
        
        # Get billing summary from pre-aggregated patient billing table
        query = f"""
        SELECT 
            billing_code,
            billing_code_description,
            COUNT(*) as patient_count,
            SUM(total_minutes) as total_minutes,
            ROUND(AVG(total_minutes), 1) as avg_minutes_per_patient
        FROM {table_name}
        GROUP BY billing_code, billing_code_description
        ORDER BY patient_count DESC, total_minutes DESC
        """
        
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching coordinator billing data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_coordinator_summary_stats(year, month):
    """Get summary statistics from patient monthly billing table"""
    conn = get_db_connection()
    try:
        table_name = f"patient_monthly_billing_{year}_{month:02d}"
        
        # Check if table exists
        check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name = ?
        """
        table_exists = conn.execute(check_query, (table_name,)).fetchone()
        
        if not table_exists:
            return {
                'total_coordinators': 0,
                'total_patients': 0,
                'total_minutes': 0,
                'total_billing_entries': 0,
                'avg_minutes_per_entry': 0
            }
        
        query = f"""
        SELECT 
            0 as total_coordinators,
            COUNT(DISTINCT patient_id) as total_patients,
            SUM(total_minutes) as total_minutes,
            COUNT(*) as total_billing_entries,
            AVG(total_minutes) as avg_minutes_per_entry
        FROM {table_name}
        WHERE total_minutes IS NOT NULL
        """
        
        result = conn.execute(query).fetchone()
        return {
            'total_coordinators': result[0] or 0,
            'total_patients': result[1] or 0,
            'total_minutes': result[2] or 0,
            'total_billing_entries': result[3] or 0,
            'avg_minutes_per_entry': round(result[4] or 0, 1)
        }
    finally:
        conn.close()

def get_coordinator_totals(year, month):
    """Get totals by billing code from patient monthly billing table"""
    conn = get_db_connection()
    try:
        table_name = f"patient_monthly_billing_{year}_{month:02d}"
        
        # Check if table exists
        check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name = ?
        """
        table_exists = conn.execute(check_query, (table_name,)).fetchone()
        
        if not table_exists:
            return pd.DataFrame()
        
        query = f"""
        SELECT 
            billing_code as coordinator_name,
            COUNT(DISTINCT patient_id) as patient_count,
            SUM(total_minutes) as total_minutes,
            COUNT(*) as billing_entries
        FROM {table_name}
        WHERE total_minutes IS NOT NULL
        GROUP BY billing_code, billing_code_description
        ORDER BY total_minutes DESC
        """
        
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def get_billing_code_distribution(year, month):
    """Get billing code distribution from patient monthly billing table"""
    conn = get_db_connection()
    try:
        table_name = f"patient_monthly_billing_{year}_{month:02d}"
        
        # Check if table exists
        check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name = ?
        """
        table_exists = conn.execute(check_query, (table_name,)).fetchone()
        
        if not table_exists:
            return pd.DataFrame()
        
        query = f"""
        SELECT 
            billing_code,
            billing_code_description,
            COUNT(*) as entry_count,
            SUM(total_minutes) as total_minutes
        FROM {table_name}
        WHERE billing_code IS NOT NULL 
        AND total_minutes IS NOT NULL
        GROUP BY billing_code, billing_code_description
        ORDER BY entry_count DESC
        """
        
        df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()

def get_patient_billing_report(year, month):
    """Get patient-level billing report from pre-aggregated patient billing table"""
    conn = get_db_connection()
    try:
        table_name = f"patient_monthly_billing_{year}_{month:02d}"
        
        # Check if table exists
        check_query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name = ?
        """
        table_exists = conn.execute(check_query, (table_name,)).fetchone()
        
        if not table_exists:
            return pd.DataFrame()
        
        # Get patient billing data from pre-aggregated table
        query = f"""
        SELECT 
            pmb.patient_id,
            COALESCE(p.first_name || ' ' || p.last_name, pmb.patient_id) as patient_name,
            p.date_of_birth,
            pmb.total_minutes,
            ROUND(pmb.total_minutes / 60.0, 2) as total_hours,
            pmb.billing_code,
            pmb.billing_code_description,
            pmb.billing_status,
            pmb.created_date
        FROM {table_name} pmb
        LEFT JOIN patients p ON pmb.patient_id = p.patient_id
        ORDER BY pmb.patient_id
        """
        
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching patient billing report: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def create_coordinator_minutes_chart(df):
    """Create coordinator minutes chart"""
    if df.empty:
        return None
    
    fig = px.bar(
        df, 
        x='coordinator_name', 
        y='total_minutes',
        title='Total Minutes by Coordinator',
        labels={'total_minutes': 'Total Minutes', 'coordinator_name': 'Coordinator'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def create_billing_code_chart(df):
    """Create billing code distribution chart"""
    if df.empty:
        return None
    
    fig = px.pie(
        df, 
        values='entry_count', 
        names='billing_code',
        title='Billing Code Distribution',
        hover_data=['billing_code_description']
    )
    return fig

def display_monthly_coordinator_billing_dashboard():
    """Main dashboard function"""
    st.title("Monthly Coordinator Billing Dashboard")
    st.markdown("Track coordinator billing by month using patient minutes and billing codes")
    
    # Get available months
    available_months = get_available_months()
    
    if not available_months:
        st.error("No coordinator billing data available. Please ensure coordinator_monthly_summary table is populated.")
        return
    
    # Month selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_month_display = st.selectbox(
            "Select Month",
            options=[month['display'] for month in available_months],
            index=0
        )
    
    # Find selected month data
    selected_month = next(
        month for month in available_months 
        if month['display'] == selected_month_display
    )
    
    year = selected_month['year']
    month = selected_month['month']
    
    with col2:
        st.metric("Selected Period", f"{calendar.month_name[month]} {year}")
    
    # Get data
    billing_data = get_coordinator_billing_data(year, month)
    summary_stats = get_coordinator_summary_stats(year, month)
    billing_codes = get_billing_code_distribution(year, month)
    
    # Summary metrics
    st.subheader("Monthly Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Coordinators", summary_stats['total_coordinators'])
    with col2:
        st.metric("Patients", summary_stats['total_patients'])
    with col3:
        st.metric("Total Minutes", f"{summary_stats['total_minutes']:,}")
    with col4:
        st.metric("Billing Entries", summary_stats['total_billing_entries'])
    with col5:
        st.metric("Avg Minutes/Entry", summary_stats['avg_minutes_per_entry'])
    
    # Charts
    if not billing_codes.empty:
        fig2 = create_billing_code_chart(billing_codes)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No billing code data available for charts")
    

    

    
    # Detailed billing data
    st.subheader("Detailed Billing Data")
    
    if not billing_data.empty:
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            billing_codes_filter = ['All'] + sorted(billing_data['billing_code'].dropna().unique().tolist())
            selected_billing_code = st.selectbox("Filter by Billing Code", billing_codes_filter)
        
        with col2:
            # Show total patients and minutes
            total_patients = billing_data['patient_count'].sum()
            total_minutes = billing_data['total_minutes'].sum()
            st.metric("Total Patients", total_patients)
            st.metric("Total Minutes", f"{total_minutes:,.0f}")
        
        # Apply filters
        filtered_data = billing_data.copy()
        
        if selected_billing_code != 'All':
            filtered_data = filtered_data[filtered_data['billing_code'] == selected_billing_code]
        
        # Display filtered data
        st.dataframe(
            filtered_data,
            column_config={
                "billing_code": st.column_config.TextColumn("Billing Code"),
                "billing_description": st.column_config.TextColumn("Description"),
                "patient_count": st.column_config.NumberColumn("Patient Count", format="%d"),
                "total_minutes": st.column_config.NumberColumn("Total Minutes", format="%.0f"),
                "avg_minutes_per_patient": st.column_config.NumberColumn("Avg Minutes/Patient", format="%.1f")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Export functionality
        st.subheader("Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export All Data"):
                csv = billing_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"patient_billing_summary_{year}_{month:02d}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Export Filtered Data"):
                csv = filtered_data.to_csv(index=False)
                st.download_button(
                    label="Download Filtered CSV",
                    data=csv,
                    file_name=f"patient_billing_filtered_{year}_{month:02d}.csv",
                    mime="text/csv"
                )
    
    else:
        st.info("No detailed billing data available for the selected month")
    
    # Patient-Level Billing Report Section
    st.markdown("---")
    st.header("📋 Patient Billing Report (Medicare Reimbursement)")
    
    patient_billing_data = get_patient_billing_report(year, month)
    
    if not patient_billing_data.empty:
        st.subheader(f"Patient Billing Summary - {calendar.month_name[month]} {year}")
        
        # Summary metrics for patient billing
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            unique_patients = patient_billing_data['patient_id'].nunique()
            st.metric("Total Patients", unique_patients)
        
        with col2:
            total_minutes = patient_billing_data['total_minutes'].sum()
            st.metric("Total Minutes", total_minutes)
        
        with col3:
            total_billing_hours = patient_billing_data['total_hours'].sum()
            st.metric("Total Billable Hours", f"{total_billing_hours:.2f}")
        
        with col4:
            avg_hours_per_patient = total_billing_hours / unique_patients if unique_patients > 0 else 0
            st.metric("Avg Hours/Patient", f"{avg_hours_per_patient:.2f}")
        
        # Display patient billing table with essential columns only
        st.subheader("Patient Billing Details")
        
        # Select and rename columns for display
        display_columns = {
            'patient_name': 'Patient Name',
            'billing_code': 'Billing Code',
            'billing_code_description': 'Description',
            'total_minutes': 'Total Minutes',
            'billing_status': 'Billing Status'
        }
        
        display_data = patient_billing_data[list(display_columns.keys())].copy()
        display_data = display_data.rename(columns=display_columns)
        
        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Total Minutes": st.column_config.NumberColumn(
                    "Total Minutes",
                    format="%d min"
                ),
                "Total Hours": st.column_config.NumberColumn(
                    "Total Hours", 
                    format="%.2f hrs"
                ),
                "Services": st.column_config.NumberColumn(
                    "Services",
                    format="%d"
                )
            }
        )
        
        # Export options for patient billing
        st.subheader("Export Patient Billing Report")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export Patient Billing Report"):
                csv = patient_billing_data.to_csv(index=False)
                st.download_button(
                    label="Download Patient Billing CSV",
                    data=csv,
                    file_name=f"patient_billing_report_{year}_{month:02d}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Create a simplified version for Medicare submission with billing codes
            medicare_report = patient_billing_data.groupby(['patient_id', 'patient_name', 'date_of_birth', 'billing_code', 'billing_code_description']).agg({
                'total_minutes': 'sum'
            }).reset_index()
            medicare_report.columns = ['Patient_ID', 'Patient_Name', 'Date_of_Birth', 'Billing_Code', 'Billing_Description', 'Total_Minutes']
            
            if st.button("🏥 Export Medicare Summary"):
                csv = medicare_report.to_csv(index=False)
                st.download_button(
                    label="Download Medicare Summary CSV",
                    data=csv,
                    file_name=f"medicare_summary_{year}_{month:02d}.csv",
                    mime="text/csv"
                )
        
        with col3:
            # Create billing codes summary
            billing_summary = patient_billing_data.groupby(['billing_code']).agg({
                'patient_id': 'nunique',
                'total_minutes': 'sum'
            }).reset_index()
            billing_summary.columns = ['Billing_Code', 'Unique_Patients', 'Total_Minutes']
            
            if st.button("📋 Export Billing Codes Summary"):
                csv = billing_summary.to_csv(index=False)
                st.download_button(
                    label="Download Billing Codes CSV",
                    data=csv,
                    file_name=f"billing_codes_summary_{year}_{month:02d}.csv",
                    mime="text/csv"
                )
    
    else:
        st.info("No patient billing data available for the selected month")
    
    # Manual refresh and data info
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.caption(f"Data last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"This dashboard queries data directly from coordinator_tasks_{year}_{month:02d} table")
    
    with col2:
        if st.button("🔄 Refresh Data", help="Refresh the current view"):
            st.rerun()

if __name__ == "__main__":
    display_monthly_coordinator_billing_dashboard()