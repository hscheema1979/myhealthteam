import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from src import database as db

# Import UI style configuration
try:
    from src.config.ui_style_config import get_section_title, get_metric_label, TextStyle, SectionTitles
except ImportError:
    # Fallback if config file not available
    def get_section_title(title): return title
    def get_metric_label(metric, is_current=False): return metric
    class TextStyle:
        INFO_INDICATOR = "INFO"
    class SectionTitles:
        PATIENT_SERVICE_ANALYSIS = "Patient Service Analysis"

def display_coordinator_patient_service_analysis(coordinator_id=None, show_all=False, title="Coordinator Patient Service Analysis"):
    """Display patient service breakdown for CM and LC roles showing minutes per patient per month"""
    st.subheader(get_section_title(title))
    
    conn = db.get_db_connection()
    try:
        if show_all:
            # Admin view - show all CM and LC coordinators with patient breakdown
            query = """
                SELECT 
                    cms.coordinator_id,
                    cms.coordinator_name,
                    cms.patient_id,
                    cms.patient_name,
                    cms.year,
                    cms.month,
                    cms.total_minutes,
                    cms.billing_code,
                    cms.billing_code_description,
                    u.full_name as coordinator_full_name,
                    r.role_name
                FROM coordinator_monthly_summary cms
                JOIN coordinators c ON cms.coordinator_id = c.coordinator_id
                JOIN users u ON c.user_id = u.user_id
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE r.role_id IN (37, 40)  -- LC and CM roles
                ORDER BY cms.year DESC, cms.month DESC, u.full_name, cms.patient_name
                LIMIT 500
            """
            data = conn.execute(query).fetchall()
        else:
            # Individual coordinator view
            query = """
                SELECT 
                    cms.coordinator_id,
                    cms.coordinator_name,
                    cms.patient_id,
                    cms.patient_name,
                    cms.year,
                    cms.month,
                    cms.total_minutes,
                    cms.billing_code,
                    cms.billing_code_description,
                    u.full_name as coordinator_full_name,
                    r.role_name
                FROM coordinator_monthly_summary cms
                JOIN coordinators c ON cms.coordinator_id = c.coordinator_id
                JOIN users u ON c.user_id = u.user_id
                JOIN user_roles ur ON u.user_id = ur.user_id
                JOIN roles r ON ur.role_id = r.role_id
                WHERE cms.coordinator_id = ? AND r.role_id IN (37, 40)
                ORDER BY cms.year DESC, cms.month DESC, cms.patient_name
                LIMIT 100
            """
            data = conn.execute(query, (coordinator_id,)).fetchall()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Create summary statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Patients Served", len(df['patient_id'].unique()))
            
            with col2:
                current_month_data = df[(df['year'] == datetime.now().year) & 
                                       (df['month'] == datetime.now().month)]
                if not current_month_data.empty:
                    avg_minutes = current_month_data['total_minutes'].mean()
                    st.metric("Avg Minutes/Patient (Current Month)", f"{avg_minutes:.1f}")
                else:
                    st.metric("Avg Minutes/Patient (Current Month)", "No data")
            
            with col3:
                total_minutes = df['total_minutes'].sum()
                st.metric("Total Minutes Logged", f"{total_minutes:,}")
            
            # Display patient service breakdown table
            st.subheader("Patient Service Breakdown by Month")
            
            # Format the data for display
            df['period'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
            
            # Group by period and coordinator for summary view
            if show_all:
                summary_df = df.groupby(['period', 'coordinator_full_name', 'role_name']).agg({
                    'patient_id': 'nunique',
                    'total_minutes': 'sum'
                }).round(2)
                summary_df.columns = ['Patients Served', 'Total Minutes']
                summary_df['Avg Minutes/Patient'] = (summary_df['Total Minutes'] / 
                                                   summary_df['Patients Served']).round(1)
                st.dataframe(summary_df, use_container_width=True)
            
            # Detailed patient-level breakdown
            st.subheader("Detailed Patient Service Records")
            display_df = df[['period', 'coordinator_full_name', 'role_name', 'patient_name', 
                           'total_minutes', 'billing_code', 'billing_code_description']].copy()
            display_df.columns = ['Period', 'Coordinator', 'Role', 'Patient', 
                                'Minutes', 'Billing Code', 'Service Description']
            
            st.dataframe(display_df, use_container_width=True)
            
            # Patient service charts
            if len(df) > 0:
                st.subheader("Service Analysis Charts")
                
                # Chart 1: Minutes per patient per month
                patient_monthly = df.groupby(['period', 'patient_name'])['total_minutes'].sum().reset_index()
                fig_data = patient_monthly.pivot(index='period', columns='patient_name', values='total_minutes')
                
                if not fig_data.empty:
                    st.bar_chart(fig_data)
                
                # Chart 2: Service distribution by billing code
                if 'billing_code' in df.columns:
                    billing_summary = df.groupby('billing_code_description')['total_minutes'].sum().sort_values(ascending=False)
                    if not billing_summary.empty:
                        st.subheader("Service Type Distribution")
                        st.bar_chart(billing_summary)
        else:
            st.info("No patient service data available for the specified criteria.")
            
    except Exception as e:
        st.error(f"Error loading patient service analysis: {e}")
    finally:
        conn.close()

def display_coordinator_monthly_summary(coordinator_id=None, show_all=False, title="Coordinator Monthly Summary"):
    """Display coordinator monthly performance summary"""
    st.subheader(title)
    
    conn = db.get_db_connection()
    try:
        if show_all:
            # Admin view - show all coordinators
            query = """
                SELECT 
                    cms.coordinator_id,
                    u.full_name as coordinator_name,
                    cms.year,
                    cms.month,
                    cms.total_minutes,
                    cms.total_minutes_per_patient,
                    cms.total_tasks_completed,
                    cms.average_daily_tasks,
                    cms.created_date
                FROM dashboard_coordinator_monthly_summary cms
                JOIN coordinators c ON cms.coordinator_id = c.coordinator_id
                JOIN users u ON c.user_id = u.user_id
                ORDER BY cms.year DESC, cms.month DESC, u.full_name
                LIMIT 100
            """
            data = conn.execute(query).fetchall()
        else:
            # Individual coordinator view
            query = """
                SELECT 
                    cms.coordinator_id,
                    u.full_name as coordinator_name,
                    cms.year,
                    cms.month,
                    cms.total_minutes,
                    cms.total_minutes_per_patient,
                    cms.total_tasks_completed,
                    cms.average_daily_tasks,
                    cms.created_date
                FROM dashboard_coordinator_monthly_summary cms
                JOIN coordinators c ON cms.coordinator_id = c.coordinator_id
                JOIN users u ON c.user_id = u.user_id
                WHERE cms.coordinator_id = ?
                ORDER BY cms.year DESC, cms.month DESC
                LIMIT 12
            """
            data = conn.execute(query, (coordinator_id,)).fetchall()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Format the data for display
            df['period'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
            df['avg_minutes_per_task'] = df['total_minutes'] / df['total_tasks_completed']
            df['avg_minutes_per_task'] = df['avg_minutes_per_task'].fillna(0).round(2)
            
            # Display metrics
            if not show_all:
                col1, col2, col3, col4 = st.columns(4)
                latest = df.iloc[0]
                col1.metric("Total Minutes (Latest Month)", f"{latest['total_minutes']:.0f}")
                col2.metric("Tasks Completed", f"{latest['total_tasks_completed']:.0f}")
                col3.metric("Avg Daily Tasks", f"{latest['average_daily_tasks']:.1f}")
                col4.metric("Avg Minutes per Patient", f"{latest['total_minutes_per_patient']:.1f}")
            
            # Display table with human-readable column names
            display_df = df[['period', 'coordinator_name', 'total_minutes', 'total_tasks_completed', 
                          'average_daily_tasks', 'total_minutes_per_patient', 'avg_minutes_per_task']].copy()
            
            # Rename columns to be more human-readable
            display_df.columns = ['Period', 'Coordinator', 'Total Minutes', 'Tasks Completed', 
                                'Avg Daily Tasks', 'Minutes per Patient', 'Minutes per Task']
            
            # Configure columns for better display
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "Period": st.column_config.TextColumn("Period", width="small"),
                    "Coordinator": st.column_config.TextColumn("Coordinator", width="medium"),
                    "Total Minutes": st.column_config.NumberColumn("Total Minutes", format="%.0f"),
                    "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                    "Avg Daily Tasks": st.column_config.NumberColumn("Avg Daily Tasks", format="%.1f"),
                    "Minutes per Patient": st.column_config.NumberColumn("Minutes per Patient", format="%.1f"),
                    "Minutes per Task": st.column_config.NumberColumn("Minutes per Task", format="%.1f"),
                },
                hide_index=True
            )
        else:
            st.info("No coordinator monthly summary data available.")
            
    except Exception as e:
        st.error(f"Error loading coordinator monthly summary: {e}")
    finally:
        conn.close()

def display_coordinator_weekly_summary(coordinator_id=None, show_all=False, title="Coordinator Weekly Summary"):
    """Display coordinator weekly performance summary (placeholder - table doesn't exist yet)"""
    st.subheader(title)
    st.info("⚠️ Coordinator weekly summary table not yet implemented in database schema.")
    
    # This would be the implementation when the table exists:
    # Similar structure to monthly but with weekly data from coordinator_weekly_summary table

def display_provider_monthly_summary(provider_id=None, show_all=False, title="Provider Monthly Summary"):
    """Display provider monthly performance summary with current month highlighting"""
    st.subheader(title)
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    conn = db.get_db_connection()
    try:
        if show_all:
            # CPM/Admin view - show all providers aggregated from monthly partition tables
            query = """
                SELECT 
                    pt.provider_id,
                    pt.provider_name,
                    strftime('%Y', pt.task_date) as year,
                    strftime('%m', pt.task_date) as month,
                    COUNT(pt.provider_task_id) as total_tasks_completed,
                    COUNT(DISTINCT pt.patient_id) as total_patients_served,
                    CASE WHEN strftime('%Y', pt.task_date) = ? AND strftime('%m', pt.task_date) = printf('%02d', ?) THEN 1 ELSE 0 END as is_current_month
                FROM provider_tasks pt
                WHERE pt.task_date IS NOT NULL 
                    AND pt.task_date != ''
                    AND pt.provider_id IS NOT NULL
                    AND pt.provider_name IS NOT NULL
                GROUP BY pt.provider_id, pt.provider_name, strftime('%Y', pt.task_date), strftime('%m', pt.task_date)
                ORDER BY strftime('%Y', pt.task_date) DESC, strftime('%m', pt.task_date) DESC, pt.provider_name
                LIMIT 200
            """
            data = conn.execute(query, (str(current_year), current_month)).fetchall()
        else:
            # Individual provider view
            query = """
                SELECT 
                    pt.provider_id,
                    pt.provider_name,
                    strftime('%Y', pt.task_date) as year,
                    strftime('%m', pt.task_date) as month,
                    COUNT(pt.provider_task_id) as total_tasks_completed,
                    COUNT(DISTINCT pt.patient_id) as total_patients_served,
                    CASE WHEN strftime('%Y', pt.task_date) = ? AND strftime('%m', pt.task_date) = printf('%02d', ?) THEN 1 ELSE 0 END as is_current_month
                FROM provider_tasks pt
                WHERE pt.provider_id = ?
                    AND pt.task_date IS NOT NULL 
                    AND pt.task_date != ''
                GROUP BY strftime('%Y', pt.task_date), strftime('%m', pt.task_date)
                ORDER BY strftime('%Y', pt.task_date) DESC, strftime('%m', pt.task_date) DESC
                LIMIT 24
            """
            data = conn.execute(query, (str(current_year), current_month, provider_id)).fetchall()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Format the data for display
            df['period'] = df['year'].astype(str) + '-' + df['month'].astype(str).str.zfill(2)
            
            # Highlight current month data in metrics
            current_month_data = df[df['is_current_month'] == 1]
            
            if not show_all:
                col1, col2, col3 = st.columns(3)
                if not current_month_data.empty:
                    current = current_month_data.iloc[0]
                    col1.metric("Current Month Tasks", f"{current['total_tasks_completed']:.0f}")
                    col2.metric("Current Month Patients", f"{current['total_patients_served']:.0f}")
                    col3.metric("Avg Tasks per Patient", f"{(current['total_tasks_completed'] / current['total_patients_served']):.1f}")
                else:
                    latest = df.iloc[0] if not df.empty else None
                    if latest is not None:
                        col1.metric("Tasks Completed (Latest)", f"{latest['total_tasks_completed']:.0f}")
                        col2.metric("Patients Served (Latest)", f"{latest['total_patients_served']:.0f}")
                        col3.metric("Avg Tasks per Patient (Latest)", f"{(latest['total_tasks_completed'] / latest['total_patients_served']):.1f}")
            
            # Separate current month data for highlighting
            current_df = df[df['is_current_month'] == 1].copy()
            historical_df = df[df['is_current_month'] == 0].copy()
            
            # Display current month summary if available
            if not current_df.empty:
                st.subheader("Current Month Performance")
                
                # Add progress indicator for current month
                today = datetime.now()
                days_in_month = (datetime(today.year, today.month + 1, 1) - datetime(today.year, today.month, 1)).days
                current_day = today.day
                progress_percentage = (current_day / days_in_month) * 100
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric("Month Progress", f"{current_day}/{days_in_month} days", f"{progress_percentage:.1f}%")
                with col2:
                    st.progress(progress_percentage / 100)
                
                current_display = current_df[['period', 'provider_name', 'total_tasks_completed', 
                                            'total_patients_served']].copy()
                current_display['avg_tasks_per_patient'] = (current_display['total_tasks_completed'] / 
                                                         current_display['total_patients_served']).round(1)
                current_display.columns = ['Period', 'Provider', 'Tasks Completed', 'Patients Served', 'Avg Tasks/Patient']
                
                st.dataframe(
                    current_display,
                    use_container_width=True,
                    column_config={
                        "Period": st.column_config.TextColumn("Period", width="small"),
                        "Provider": st.column_config.TextColumn("Provider", width="medium"),
                        "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                        "Patients Served": st.column_config.NumberColumn("Patients Served", format="%.0f"),
                        "Avg Tasks/Patient": st.column_config.NumberColumn("Avg Tasks/Patient", format="%.1f"),
                    },
                    hide_index=True
                )
            
            # Display historical data
            if not historical_df.empty:
                st.subheader("Historical Performance Data")
                historical_display = historical_df[['period', 'provider_name', 'total_tasks_completed', 
                                                  'total_patients_served']].copy()
                historical_display['avg_tasks_per_patient'] = (historical_display['total_tasks_completed'] / 
                                                            historical_display['total_patients_served']).round(1)
                historical_display.columns = ['Period', 'Provider', 'Tasks Completed', 'Patients Served', 'Avg Tasks/Patient']
                
                st.dataframe(
                    historical_display,
                    use_container_width=True,
                    column_config={
                        "Period": st.column_config.TextColumn("Period", width="small"),
                        "Provider": st.column_config.TextColumn("Provider", width="medium"),
                        "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                        "Patients Served": st.column_config.NumberColumn("Patients Served", format="%.0f"),
                        "Avg Tasks/Patient": st.column_config.NumberColumn("Avg Tasks/Patient", format="%.1f"),
                    },
                    hide_index=True
                )
        else:
            st.info("No provider task data available.")
            
    except Exception as e:
        st.error(f"Error loading provider monthly summary: {e}")
    finally:
        conn.close()

def display_provider_weekly_summary(provider_id=None, show_all=False, title="Provider Weekly Summary"):
    """Display provider weekly performance summary"""
    st.subheader(title)
    
    # Check if current user is admin to show payment status
    is_admin = False
    if 'user_email' in st.session_state:
        is_admin = st.session_state.user_email == 'admin@myhealthteam.org'
    
    conn = db.get_db_connection()
    try:
        if show_all:
            # Admin/CPM view - show all providers
            query = """
                SELECT 
                    pws.provider_id,
                    pws.provider_name,
                    pws.year,
                    pws.week_number,
                    pws.week_start_date,
                    pws.week_end_date,
                    pws.total_tasks_completed,
                    pws.total_time_spent_minutes,
                    pws.average_daily_minutes,
                    pws.days_active,
                    pws.paid,
                    pws.created_date
                FROM provider_weekly_summary pws
                ORDER BY pws.year DESC, pws.week_number DESC, pws.provider_name
                LIMIT 100
            """
            data = conn.execute(query).fetchall()
        else:
            # Individual provider view
            query = """
                SELECT 
                    pws.provider_id,
                    pws.provider_name,
                    pws.year,
                    pws.week_number,
                    pws.week_start_date,
                    pws.week_end_date,
                    pws.total_tasks_completed,
                    pws.total_time_spent_minutes,
                    pws.average_daily_minutes,
                    pws.days_active,
                    pws.paid,
                    pws.created_date
                FROM provider_weekly_summary pws
                WHERE pws.provider_id = ?
                ORDER BY pws.year DESC, pws.week_number DESC
                LIMIT 12
            """
            data = conn.execute(query, (provider_id,)).fetchall()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Format the data for display
            df['week_period'] = df['year'].astype(str) + '-W' + df['week_number'].astype(str).str.zfill(2)
            df['avg_minutes_per_day'] = df['average_daily_minutes'].round(1)
            df['payment_status'] = df['paid'].apply(lambda x: 'Paid' if x else 'Pending')
            
            # Display metrics
            if not show_all:
                col1, col2, col3, col4 = st.columns(4)
                latest = df.iloc[0]
                col1.metric("Tasks (Latest Week)", f"{latest['total_tasks_completed']:.0f}")
                col2.metric("Total Minutes", f"{latest['total_time_spent_minutes']:.0f}")
                col3.metric("Days Active", f"{latest['days_active']:.0f}")
                col4.metric("Avg Daily Minutes", f"{latest['avg_minutes_per_day']:.1f}")
            
            # Display table with human-readable column names
            # Conditionally include payment status column only for admin
            if is_admin:
                display_cols = ['week_period', 'provider_name', 'week_start_date', 'week_end_date',
                              'total_tasks_completed', 'total_time_spent_minutes', 'days_active', 
                              'avg_minutes_per_day', 'payment_status']
                column_names = ['Week', 'Provider', 'Start Date', 'End Date',
                              'Tasks Completed', 'Total Minutes', 'Days Active', 
                              'Avg Minutes/Day', 'Payment Status']
            else:
                display_cols = ['week_period', 'provider_name', 'week_start_date', 'week_end_date',
                              'total_tasks_completed', 'total_time_spent_minutes', 'days_active', 
                              'avg_minutes_per_day']
                column_names = ['Week', 'Provider', 'Start Date', 'End Date',
                              'Tasks Completed', 'Total Minutes', 'Days Active', 
                              'Avg Minutes/Day']
            
            display_df = df[display_cols].copy()
            display_df.columns = column_names
            
            # Configure columns for better display
            if is_admin:
                column_config = {
                    "Week": st.column_config.TextColumn("Week", width="small"),
                    "Provider": st.column_config.TextColumn("Provider", width="medium"),
                    "Start Date": st.column_config.DateColumn("Start Date", width="small"),
                    "End Date": st.column_config.DateColumn("End Date", width="small"),
                    "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                    "Total Minutes": st.column_config.NumberColumn("Total Minutes", format="%.0f"),
                    "Days Active": st.column_config.NumberColumn("Days Active", format="%.0f"),
                    "Avg Minutes/Day": st.column_config.NumberColumn("Avg Minutes/Day", format="%.1f"),
                    "Payment Status": st.column_config.TextColumn("Payment Status", width="small"),
                }
            else:
                column_config = {
                    "Week": st.column_config.TextColumn("Week", width="small"),
                    "Provider": st.column_config.TextColumn("Provider", width="medium"),
                    "Start Date": st.column_config.DateColumn("Start Date", width="small"),
                    "End Date": st.column_config.DateColumn("End Date", width="small"),
                    "Tasks Completed": st.column_config.NumberColumn("Tasks Completed", format="%.0f"),
                    "Total Minutes": st.column_config.NumberColumn("Total Minutes", format="%.0f"),
                    "Days Active": st.column_config.NumberColumn("Days Active", format="%.0f"),
                    "Avg Minutes/Day": st.column_config.NumberColumn("Avg Minutes/Day", format="%.1f"),
                }
            
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config=column_config,
                hide_index=True
            )
        else:
            st.info("No provider weekly summary data available.")
            
    except Exception as e:
        st.error(f"Error loading provider weekly summary: {e}")
    finally:
        conn.close()

def display_patient_assignments_by_workflow(user_id, role_id, title="Patient Assignments"):
    """Display patient assignments based on onboarding workflow"""
    st.subheader(title)
    
    conn = db.get_db_connection()
    try:
        if role_id in [33, 38]:  # Care Provider or Care Provider Manager
            # Show provider-related patient assignments
            query = """
                SELECT 
                    p.first_name,
                    p.last_name,
                    p.date_of_birth,
                    pa.assignment_date,
                    pa.assignment_type,
                    pa.status,
                    pa.priority_level,
                    r.region_name,
                    CASE 
                        WHEN op.stage1_complete = 0 THEN 'Initial Contact Needed'
                        WHEN op.stage2_complete = 0 THEN 'TV Visit Scheduled'
                        WHEN op.stage3_complete = 0 THEN 'Documentation Pending'
                        ELSE 'Ready for Care'
                    END as workflow_stage
                FROM patient_assignments pa
                JOIN patients p ON pa.patient_id = p.patient_id
                LEFT JOIN regions r ON p.region_id = r.region_id
                LEFT JOIN onboarding_patients op ON p.patient_id = op.patient_id
                WHERE pa.provider_id = ?
                ORDER BY pa.assignment_date DESC
                LIMIT 50
            """
            data = conn.execute(query, (user_id,)).fetchall()
            
        elif role_id in [36, 39, 40]:  # Care Coordinator roles
            # Show coordinator-related patient assignments
            query = """
                SELECT 
                    p.first_name,
                    p.last_name,
                    p.date_of_birth,
                    pa.assignment_date,
                    pa.assignment_type,
                    pa.status,
                    pa.priority_level,
                    r.region_name,
                    CASE 
                        WHEN op.stage1_complete = 0 THEN 'Initial Contact Needed'
                        WHEN op.stage2_complete = 0 THEN 'TV Visit Scheduling'
                        WHEN op.stage3_complete = 0 THEN 'Documentation Review'
                        ELSE 'Onboarding Complete'
                    END as workflow_stage
                FROM patient_assignments pa
                JOIN patients p ON pa.patient_id = p.patient_id
                LEFT JOIN regions r ON p.region_id = r.region_id
                LEFT JOIN onboarding_patients op ON p.patient_id = op.patient_id
                WHERE pa.coordinator_id = ?
                ORDER BY pa.assignment_date DESC
                LIMIT 50
            """
            data = conn.execute(query, (user_id,)).fetchall()
        else:
            st.warning("Role not supported for patient assignments view.")
            return
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Create summary metrics
            col1, col2, col3, col4 = st.columns(4)
            total_patients = len(df)
            active_assignments = len(df[df['status'] == 'Active'])
            high_priority = len(df[df['priority_level'] == 'High'])
            pending_workflow = len(df[df['workflow_stage'] != 'Onboarding Complete'])
            
            col1.metric("Total Patients", total_patients)
            col2.metric("Active Assignments", active_assignments)
            col3.metric("High Priority", high_priority)
            col4.metric("Pending Workflow", pending_workflow)
            
            # Display the assignments table with human-readable column names
            display_df = df[['first_name', 'last_name', 'assignment_date', 'assignment_type',
                          'status', 'priority_level', 'region_name', 'workflow_stage']].copy()
            
            # Rename columns to be more human-readable
            display_df.columns = ['First Name', 'Last Name', 'Assignment Date', 'Type',
                                'Status', 'Priority', 'Region', 'Workflow Stage']
            
            # Configure columns for better display
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "First Name": st.column_config.TextColumn("First Name", width="small"),
                    "Last Name": st.column_config.TextColumn("Last Name", width="small"),
                    "Assignment Date": st.column_config.DateColumn("Assignment Date", width="small"),
                    "Type": st.column_config.TextColumn("Type", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Priority": st.column_config.TextColumn("Priority", width="small"),
                    "Region": st.column_config.TextColumn("Region", width="small"),
                    "Workflow Stage": st.column_config.TextColumn("Workflow Stage", width="medium"),
                },
                hide_index=True
            )
            
            # Workflow stage breakdown
            if 'workflow_stage' in df.columns:
                stage_counts = df['workflow_stage'].value_counts()
                st.subheader("Workflow Stage Breakdown")
                for stage, count in stage_counts.items():
                    st.write(f"**{stage}**: {count} patients")
                    
        else:
            st.info("No patient assignments found for this user.")
            
    except Exception as e:
        st.error(f"Error loading patient assignments: {e}")
    finally:
        conn.close()

def display_provider_patient_summary(provider_id=None, show_all=False, title="Patient Summary per Provider"):
    """Display patient summary per provider with last visit dates and status"""
    st.subheader(title)
    
    conn = db.get_db_connection()
    try:
        if show_all:
            # CPM/Admin view - show all providers and their patients
            query = """
                SELECT 
                    pp.patient_id,
                    pp.first_name || ' ' || pp.last_name as patient_name,
                    pp.last_visit_date,
                    pp.provider_name,
                    pp.status,
                    pp.enrollment_date,
                    CASE WHEN pp.last_visit_date IS NULL OR pp.last_visit_date = '' THEN 'Never Seen' ELSE 'Has Visit History' END as visit_status,
                    CASE WHEN pp.last_visit_date IS NULL OR pp.last_visit_date = '' THEN 1 ELSE 0 END as needs_visit
                FROM patient_panel pp
                ORDER BY pp.provider_name, pp.needs_visit DESC, pp.last_visit_date DESC
            """
            data = conn.execute(query).fetchall()
        else:
            # Individual provider view
            query = """
                SELECT 
                    pp.patient_id,
                    pp.first_name || ' ' || pp.last_name as patient_name,
                    pp.last_visit_date,
                    pp.provider_name,
                    pp.status,
                    pp.enrollment_date,
                    CASE WHEN pp.last_visit_date IS NULL OR pp.last_visit_date = '' THEN 'Never Seen' ELSE 'Has Visit History' END as visit_status,
                    CASE WHEN pp.last_visit_date IS NULL OR pp.last_visit_date = '' THEN 1 ELSE 0 END as needs_visit
                FROM patient_panel pp
                WHERE pp.provider_id = ?
                ORDER BY pp.needs_visit DESC, pp.last_visit_date DESC
            """
            data = conn.execute(query, (provider_id,)).fetchall()
        
        if data:
            df = pd.DataFrame([dict(row) for row in data])
            
            # Summary metrics
            total_patients = len(df)
            patients_never_seen = df['needs_visit'].sum()
            patients_with_visits = total_patients - patients_never_seen
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Patients", f"{total_patients}")
            col2.metric("Have Visit History", f"{patients_with_visits}")
            col3.metric("Never Seen", f"{patients_never_seen}")
            
            # Display table
            if show_all:
                # Group by provider for summary view
                provider_summary = df.groupby('provider_name').agg({
                    'patient_id': 'count',
                    'needs_visit': 'sum'
                }).reset_index()
                provider_summary.columns = ['Provider', 'Total Patients', 'Never Seen']
                provider_summary['Have Visit History'] = provider_summary['Total Patients'] - provider_summary['Never Seen']
                
                st.subheader("Provider Summary")
                st.dataframe(
                    provider_summary,
                    use_container_width=True,
                    column_config={
                        "Provider": st.column_config.TextColumn("Provider", width="medium"),
                        "Total Patients": st.column_config.NumberColumn("Total Patients"),
                        "Have Visit History": st.column_config.NumberColumn("Have Visit History"),
                        "Never Seen": st.column_config.NumberColumn("Never Seen"),
                    },
                    hide_index=True
                )
            
            # Detailed patient list
            st.subheader("Patient Details")
            display_df = df[['patient_name', 'last_visit_date', 'provider_name', 'status', 'enrollment_date', 'visit_status']].copy()
            display_df.columns = ['Patient Name', 'Last Visit Date', 'Provider', 'Status', 'Enrollment Date', 'Visit Status']
            
            # Highlight patients who need visits
            def highlight_needs_visit(row):
                if row['Visit Status'] == 'Never Seen':
                    return ['background-color: #ffebee'] * len(row)
                else:
                    return [''] * len(row)
            
            st.dataframe(
                display_df.style.apply(highlight_needs_visit, axis=1),
                use_container_width=True,
                column_config={
                    "Patient Name": st.column_config.TextColumn("Patient Name", width="medium"),
                    "Last Visit Date": st.column_config.TextColumn("Last Visit Date", width="small"),
                    "Provider": st.column_config.TextColumn("Provider", width="medium"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Enrollment Date": st.column_config.TextColumn("Enrollment Date", width="small"),
                    "Visit Status": st.column_config.TextColumn("Visit Status", width="small"),
                },
                hide_index=True
            )
        else:
            st.info("No patient panel data available.")
            
    except Exception as e:
        st.error(f"Error loading patient summary: {e}")
    finally:
        conn.close()