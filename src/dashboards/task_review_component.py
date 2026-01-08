import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from src import database

def show(user_id):
    """Display task review for providers with Daily/Weekly/Monthly views"""
    st.subheader("Task Review")

    # Get available provider task tables using SQLite syntax
    conn = database.get_db_connection()
    try:
        query = """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name LIKE 'provider_tasks_%'
        ORDER BY name DESC
        """

        result = conn.execute(query).fetchall()
        if not result:
            st.info("No task data found.")
            return

        # Extract available months from table names
        available_months = []
        for row in result:
            table_name = row[0]
            # Extract year and month from table name (e.g., provider_tasks_2025_08)
            parts = table_name.split('_')
            if len(parts) >= 4:
                year = parts[2]
                month = parts[3]
                try:
                    month_name = calendar.month_name[int(month)]
                    display_name = f"{month_name} {year}"
                    available_months.append((display_name, table_name, int(year), int(month)))
                except (ValueError, IndexError):
                    continue

        if not available_months:
            st.info("No valid task data tables found.")
            return

        # --- View Selection ---
        view_type = st.radio(
            "View Type",
            ["Daily", "Weekly", "Monthly"],
            horizontal=True,
            key="task_review_view_type"
        )
        st.divider()

        tasks_df = pd.DataFrame()
        display_period = ""

        if view_type == "Daily":
            # --- Daily View ---
            selected_date = st.date_input("Select Date", value=pd.to_datetime('today'), key="task_review_daily_date")
            st.caption(f"Showing tasks for {selected_date.strftime('%A, %B %d, %Y')}")
            
            # Determine which table to query based on selected date
            year = selected_date.year
            month = selected_date.month
            table_name = f"provider_tasks_{year}_{str(month).zfill(2)}"
            
            # Check if table is in available_months (meaning it exists)
            table_exists = any(t[1] == table_name for t in available_months)
            
            if table_exists:
                query = f"""
                SELECT
                    provider_task_id,
                    patient_name,
                    task_date,
                    task_description
                FROM {table_name}
                WHERE provider_id = ? AND date(task_date) = date(?)
                ORDER BY task_date DESC
                """
                rows = conn.execute(query, (user_id, selected_date)).fetchall()
                if rows:
                    tasks_df = pd.DataFrame([dict(r) for r in rows])
                    tasks_df = tasks_df.rename(columns={
                        'provider_task_id': 'Task ID',
                        'patient_name': 'Patient Name',
                        'task_date': 'Date',
                        'task_description': 'Location of Visit'
                    })
            else:
                pass # Table doesn't exist for this date
                
            display_period = selected_date.strftime('%Y-%m-%d')

        elif view_type == "Weekly":
            # --- Weekly View ---
            # Helper to get week range
            def get_week_range(date_obj):
                start = date_obj - timedelta(days=date_obj.weekday()) # Monday
                end = start + timedelta(days=6) # Sunday
                return start, end

            selected_date_wk = st.date_input("Select any day in the desired week", value=pd.to_datetime('today'), key="task_review_weekly_date")
            start_week, end_week = get_week_range(selected_date_wk)
            
            st.caption(f"Showing tasks for week: {start_week.strftime('%Y-%m-%d')} to {end_week.strftime('%Y-%m-%d')}")
            display_period = f"{start_week.strftime('%Y-%m-%d')}_{end_week.strftime('%Y-%m-%d')}"

            # Identify tables to query (week might span two months)
            tables_to_query = set()
            curr = start_week
            while curr <= end_week:
                t_name = f"provider_tasks_{curr.year}_{str(curr.month).zfill(2)}"
                # Only add if it exists in DB
                if any(t[1] == t_name for t in available_months):
                    tables_to_query.add(t_name)
                curr += timedelta(days=1)
            
            if tables_to_query:
                all_rows = []
                for t_name in tables_to_query:
                    query = f"""
                    SELECT
                        patient_name,
                        task_date,
                        task_description
                    FROM {t_name}
                    WHERE provider_id = ? AND date(task_date) BETWEEN date(?) AND date(?)
                    ORDER BY task_date DESC
                    """
                    rows = conn.execute(query, (user_id, start_week, end_week)).fetchall()
                    all_rows.extend([dict(r) for r in rows])

                if all_rows:
                    tasks_df = pd.DataFrame(all_rows)
                    tasks_df = tasks_df.rename(columns={
                        'patient_name': 'Patient Name',
                        'task_date': 'Date',
                        'task_description': 'Location of Visit'
                    })

        elif view_type == "Monthly":
            # --- Monthly View ---
            selected_option = st.selectbox(
                "Select Month:",
                available_months,
                format_func=lambda x: x[0],
                key="task_review_month_select"
            )
            
            if selected_option:
                display_name, table_name, _, _ = selected_option
                st.caption(f"Showing tasks for {display_name}")
                display_period = display_name.replace(' ', '_')

                query = f"""
                SELECT
                    patient_name,
                    task_date,
                    task_description
                FROM {table_name}
                WHERE provider_id = ?
                ORDER BY task_date DESC
                """
                rows = conn.execute(query, (user_id,)).fetchall()
                if rows:
                    tasks_df = pd.DataFrame([dict(r) for r in rows])
                    tasks_df = tasks_df.rename(columns={
                        'patient_name': 'Patient Name',
                        'task_date': 'Date',
                        'task_description': 'Location of Visit'
                    })

        # --- Display Results ---
        if not tasks_df.empty:
            # Format Date
            if 'Date' in tasks_df.columns:
                tasks_df['Date'] = pd.to_datetime(tasks_df['Date']).dt.strftime('%Y-%m-%d')

            # Metrics
            total_tasks = len(tasks_df)
            st.metric("Total Tasks", total_tasks)

            # --- Daily View: Simplified read-only display ---
            if view_type == "Daily":
                st.dataframe(
                    tasks_df[['Patient Name', 'Date', 'Location of Visit']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Patient Name": st.column_config.TextColumn("Patient Name", width="large"),
                        "Date": st.column_config.TextColumn("Date", width="small"),
                        "Location of Visit": st.column_config.TextColumn("Location of Visit", width="large"),
                    }
                )

            # --- Weekly/Monthly Views: Read-only ---
            else:
                st.dataframe(
                    tasks_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Patient Name": st.column_config.TextColumn("Patient Name", width="large"),
                        "Date": st.column_config.TextColumn("Date", width="small"),
                        "Location of Visit": st.column_config.TextColumn("Location of Visit", width="large"),
                    }
                )

            csv = tasks_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"provider_tasks_{user_id}_{view_type}_{display_period}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"No tasks found for the selected {view_type.lower()} period.")

    except Exception as e:
        st.error(f"Error loading task review: {e}")
    finally:
        conn.close()
