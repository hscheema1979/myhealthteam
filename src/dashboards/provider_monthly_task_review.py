import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from src import database

# Location and patient type options for dropdowns
LOCATION_TYPES = ["Home", "Office", "Telehealth"]
PATIENT_TYPES = ["Follow Up", "New", "Acute", "Cognitive", "TCM-7", "TCM-14"]

def show(user_id):
    """Display monthly task review for providers with editing enabled"""
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
                COALESCE(tbc.location_type, 'Home') as location_type,
                COALESCE(tbc.patient_type, 'Follow Up') as patient_type,
                COALESCE(pt.notes, '') as notes,
                pt.billing_code
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
                    'provider_task_id': '_task_id',
                    'patient_name': 'Patient Name',
                    'task_date': 'Date of Service',
                    'date_of_birth': 'Patient DOB',
                    'location_type': 'Location of Service',
                    'patient_type': 'Patient Type',
                    'notes': 'Notes',
                    'billing_code': '_billing_code'
                })

                tasks_df['Date of Service'] = pd.to_datetime(tasks_df['Date of Service']).dt.strftime('%Y-%m-%d')

                total_tasks = len(tasks_df)
                st.metric("Total Tasks", total_tasks)

                st.caption("Edit Location, Patient Type, or Notes if corrections are needed. Changes save automatically.")

                # Use data_editor for editable columns
                edited_df = st.data_editor(
                    tasks_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "_task_id": st.column_config.TextColumn("Task ID", disabled=True, hidden=True),
                        "_billing_code": st.column_config.TextColumn("Billing Code", disabled=True, hidden=True),
                        "Patient Name": st.column_config.TextColumn("Patient Name", disabled=True, width="medium"),
                        "Date of Service": st.column_config.TextColumn("Date of Service", disabled=True, width="small"),
                        "Patient DOB": st.column_config.TextColumn("Patient DOB", disabled=True, width="small"),
                        "Location of Service": st.column_config.SelectboxColumn(
                            "Location",
                            options=LOCATION_TYPES,
                            required=True,
                            width="small"
                        ),
                        "Patient Type": st.column_config.SelectboxColumn(
                            "Patient Type",
                            options=PATIENT_TYPES,
                            required=True,
                            width="small"
                        ),
                        "Notes": st.column_config.TextColumn("Notes", width="large"),
                    },
                    num_rows="dynamic"
                )

                # Check for edits and save changes
                if not edited_df.equals(tasks_df):
                    _save_task_changes(conn, table_name, tasks_df, edited_df, user_id, year, month)
                    st.success("Changes saved successfully!")
                    st.rerun()

                # Prepare CSV for download (without hidden columns)
                download_df = edited_df[["Patient Name", "Date of Service", "Patient DOB", "Location of Service", "Patient Type", "Notes"]].copy()
                csv = download_df.to_csv(index=False)
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


def _save_task_changes(conn, table_name, original_df, edited_df, provider_id, year, month):
    """
    Save changes from the edited task dataframe back to the database.
    Updates billing_code based on location_type and patient_type changes.
    """
    try:
        # Merge to find changed rows
        merged = original_df.merge(edited_df, on='_task_id', how='outer', suffixes=('_orig', '_edit'), indicator=True)

        # Track weeks affected for billing summary update
        affected_weeks = set()

        for idx, row in merged.iterrows():
            if row['_merge'] == 'both':
                task_id = row['_task_id']

                # Check for changes
                location_changed = row['Location of Service_orig'] != row['Location of Service_edit']
                patient_type_changed = row['Patient Type_orig'] != row['Patient Type_edit']
                notes_changed = row['Notes_orig'] != row['Notes_edit']

                if location_changed or patient_type_changed or notes_changed:
                    new_location = row['Location of Service_edit']
                    new_patient_type = row['Patient Type_edit']
                    new_notes = row['Notes_edit']
                    task_date = row['Date of Service_orig']

                    # Find the matching billing code for new location/patient_type
                    new_billing_code = database.get_billing_code_for_location_patient_type(
                        conn, new_location, new_patient_type
                    )

                    if new_billing_code:
                        # Update the task
                        conn.execute(f"""
                            UPDATE {table_name}
                            SET billing_code = ?,
                                notes = ?,
                                imported_at = CURRENT_TIMESTAMP
                            WHERE provider_task_id = ?
                        """, (new_billing_code, new_notes, task_id))

                        # Track affected week for billing summary update
                        from datetime import datetime
                        dt = datetime.strptime(task_date, '%Y-%m-%d')
                        week_start = (dt - pd.Timedelta(days=dt.weekday())).strftime('%Y-%m-%d')
                        affected_weeks.add(week_start)

        conn.commit()

        # Update billing summaries for affected weeks
        if affected_weeks:
            _update_affected_billing_summaries(provider_id, affected_weeks)

    except Exception as e:
        st.error(f"Error saving changes: {e}")
        conn.rollback()


def _update_affected_billing_summaries(provider_id, affected_weeks):
    """
    Update the provider_weekly_summary_with_billing table for affected weeks.
    Re-calculates the summary for a specific provider and week.
    """
    conn = database.get_db_connection()
    try:
        for week_start in affected_weeks:
            # Calculate week_end (6 days after week_start)
            week_start_dt = datetime.strptime(week_start, '%Y-%m-%d')
            week_end_dt = week_start_dt + pd.Timedelta(days=6)
            week_end = week_end_dt.strftime('%Y-%m-%d')

            # Find which monthly table(s) intersect with this week
            month_start = week_start_dt.replace(day=1)
            month_end = (month_start + pd.Timedelta(days=32)).replace(day=1) - pd.Timedelta(days=1)

            # Determine table name for this month
            table_name = f"provider_tasks_{week_start_dt.year}_{str(week_start_dt.month).zfill(2)}"

            # Check if table exists
            table_exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            ).fetchone()

            if not table_exists:
                continue

            # Get all tasks for this provider within the week from the monthly table
            query = f"""
            SELECT
                pt.provider_id,
                pt.provider_name,
                pt.billing_code,
                tbc.location_type,
                tbc.patient_type,
                tbc.task_description,
                pt.minutes_of_service,
                COUNT(*) as task_count
            FROM {table_name} pt
            LEFT JOIN task_billing_codes tbc ON pt.billing_code = tbc.billing_code
            WHERE pt.provider_id = ?
            AND pt.task_date >= ? AND pt.task_date <= ?
            AND (pt.is_deleted IS NULL OR pt.is_deleted = 0)
            GROUP BY pt.billing_code, tbc.location_type, tbc.patient_type, tbc.task_description
            """

            rows = conn.execute(query, (provider_id, week_start, week_end)).fetchall()

            if rows:
                for row in rows:
                    # Get year and week number
                    year = week_start_dt.year
                    week_number = week_start_dt.isocalendar()[1]

                    # Calculate totals for this billing code
                    total_tasks = sum(r['task_count'] for r in rows if r['billing_code'] == row['billing_code'])
                    total_time = sum(r['minutes_of_service'] for r in rows if r['billing_code'] == row['billing_code'])

                    # Upsert into summary table
                    conn.execute("""
                        INSERT OR REPLACE INTO provider_weekly_summary_with_billing
                        (provider_id, provider_name, week_start_date, week_end_date,
                         year, week_number, billing_code, location_type, patient_type,
                         task_description, total_tasks_completed, total_time_spent_minutes,
                         updated_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        provider_id,
                        row['provider_name'],
                        week_start,
                        week_end,
                        year,
                        week_number,
                        row['billing_code'],
                        row['location_type'],
                        row['patient_type'],
                        row['task_description'],
                        total_tasks,
                        total_time
                    ))

        conn.commit()
    except Exception as e:
        print(f"Error updating billing summaries: {e}")
        conn.rollback()
    finally:
        conn.close()
