import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from src import database

def show(user_id):
    """Display monthly task review for providers - read-only view with new columns"""
    st.subheader("Monthly Task Review")

    if st.button("🔄 Refresh Data", key="refresh_provider_monthly_data"):
        st.rerun()

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

        available_months = []
        for row in result:
            table_name = row[0]
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

        selected_option = st.selectbox(
            "Select Month:",
            available_months,
            format_func=lambda x: x[0],
            key="provider_monthly_review_select"
        )

        if selected_option:
            display_name, table_name, year, month = selected_option
            st.caption(f"Showing tasks for {display_name}")

            query = f"""
            SELECT
                pt.provider_task_id,
                pt.patient_name,
                pt.task_date,
                p.date_of_birth,
                tbc.location_type,
                tbc.patient_type,
                pt.notes
            FROM {table_name} pt
            LEFT JOIN patients p ON pt.patient_id = p.patient_id
            LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
            WHERE pt.provider_id = ?
            ORDER BY pt.task_date DESC
            """
            rows = conn.execute(query, (user_id,)).fetchall()

            if rows:
                tasks_df = pd.DataFrame([dict(r) for r in rows])

                tasks_df = tasks_df.rename(columns={
                    'provider_task_id': 'Task ID',
                    'patient_name': 'Patient Name',
                    'task_date': 'Date of Service',
                    'date_of_birth': 'Patient DOB',
                    'location_type': 'Location of Service',
                    'patient_type': 'Patient Type',
                    'notes': 'Notes'
                })

                tasks_df['Date of Service'] = pd.to_datetime(tasks_df['Date of Service']).dt.strftime('%Y-%m-%d')

                total_tasks = len(tasks_df)
                st.metric("Total Tasks", total_tasks)

                st.dataframe(
                    tasks_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Patient Name": st.column_config.TextColumn("Patient Name", width="medium"),
                        "Date of Service": st.column_config.TextColumn("Date of Service", width="small"),
                        "Patient DOB": st.column_config.TextColumn("Patient DOB", width="small"),
                        "Location of Service": st.column_config.TextColumn("Location", width="small"),
                        "Patient Type": st.column_config.TextColumn("Patient Type", width="small"),
                        "Notes": st.column_config.TextColumn("Notes", width="large"),
                    }
                )

                csv = tasks_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"provider_tasks_{user_id}_monthly_{year}_{month}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"No tasks found for {display_name}.")

    except Exception as e:
        st.error(f"Error loading monthly task review: {e}")
    finally:
        conn.close()
