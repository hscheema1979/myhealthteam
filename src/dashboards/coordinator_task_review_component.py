import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta
from src import database

def show(user_id):
    """Display task review for coordinators with Daily/Weekly/Monthly views"""
    st.subheader("Task Review")

    # Get available coordinator task tables using SQLite syntax
    conn = database.get_db_connection()
    try:
        query = """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name LIKE 'coordinator_tasks_%'
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
            # Extract year and month from table name (e.g., coordinator_tasks_2025_12)
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
            key="coordinator_task_review_view_type"
        )
        st.divider()

        tasks_df = pd.DataFrame()
        display_period = ""

        if view_type == "Daily":
            # --- Daily View ---
            selected_date = st.date_input("Select Date", value=pd.to_datetime('today'), key="coordinator_task_review_daily_date")
            st.caption(f"Showing tasks for {selected_date.strftime('%A, %B %d, %Y')}")
            
            # Determine which table to query based on selected date
            year = selected_date.year
            month = selected_date.month
            table_name = f"coordinator_tasks_{year}_{str(month).zfill(2)}"
            
            # Check if table is in available_months (meaning it exists)
            table_exists = any(t[1] == table_name for t in available_months)
            
            if table_exists:
                query = f"""
                SELECT
                    coordinator_task_id,
                    patient_id,
                    task_date,
                    duration_minutes,
                    task_type,
                    notes
                FROM {table_name}
                WHERE coordinator_id = ? AND date(task_date) = date(?)
                ORDER BY task_date DESC
                """
                rows = conn.execute(query, (user_id, selected_date)).fetchall()
                if rows:
                    tasks_df = pd.DataFrame([dict(r) for r in rows])
                    tasks_df = tasks_df.rename(columns={
                        'coordinator_task_id': 'Task ID',
                        'patient_id': 'Patient Name',
                        'task_date': 'DOS',
                        'duration_minutes': 'Duration',
                        'task_type': 'Service Type',
                        'notes': 'Notes'
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

            selected_date_wk = st.date_input("Select any day in the desired week", value=pd.to_datetime('today'), key="coordinator_task_review_weekly_date")
            start_week, end_week = get_week_range(selected_date_wk)
            
            st.caption(f"Showing tasks for week: {start_week.strftime('%Y-%m-%d')} to {end_week.strftime('%Y-%m-%d')}")
            display_period = f"{start_week.strftime('%Y-%m-%d')}_{end_week.strftime('%Y-%m-%d')}"

            # Identify tables to query (week might span two months)
            tables_to_query = set()
            curr = start_week
            while curr <= end_week:
                t_name = f"coordinator_tasks_{curr.year}_{str(curr.month).zfill(2)}"
                # Only add if it exists in DB
                if any(t[1] == t_name for t in available_months):
                    tables_to_query.add(t_name)
                curr += timedelta(days=1)
            
            if tables_to_query:
                all_rows = []
                for t_name in tables_to_query:
                    query = f"""
                    SELECT
                        patient_id,
                        task_date,
                        duration_minutes,
                        task_type,
                        notes
                    FROM {t_name}
                    WHERE coordinator_id = ? AND date(task_date) BETWEEN date(?) AND date(?)
                    ORDER BY task_date DESC
                    """
                    rows = conn.execute(query, (user_id, start_week, end_week)).fetchall()
                    all_rows.extend([dict(r) for r in rows])
                
                if all_rows:
                    tasks_df = pd.DataFrame(all_rows)
                    tasks_df = tasks_df.rename(columns={
                        'patient_id': 'Patient Name',
                        'task_date': 'DOS',
                        'duration_minutes': 'Duration',
                        'task_type': 'Service Type',
                        'notes': 'Notes'
                    })

        elif view_type == "Monthly":
            # --- Monthly View ---
            selected_option = st.selectbox(
                "Select Month:",
                available_months,
                format_func=lambda x: x[0],
                key="coordinator_task_review_month_select"
            )
            
            if selected_option:
                display_name, table_name, _, _ = selected_option
                st.caption(f"Showing tasks for {display_name}")
                display_period = display_name.replace(' ', '_')

                query = f"""
                SELECT
                    patient_id,
                    task_date,
                    duration_minutes,
                    task_type,
                    notes
                FROM {table_name}
                WHERE coordinator_id = ?
                ORDER BY task_date DESC
                """
                rows = conn.execute(query, (user_id,)).fetchall()
                if rows:
                    tasks_df = pd.DataFrame([dict(r) for r in rows])
                    tasks_df = tasks_df.rename(columns={
                        'patient_id': 'Patient Name',
                        'task_date': 'DOS',
                        'duration_minutes': 'Duration',
                        'task_type': 'Service Type',
                        'notes': 'Notes'
                    })

        # --- Display Results ---
        if not tasks_df.empty:
            # Format DOS
            if 'DOS' in tasks_df.columns:
                tasks_df['DOS'] = pd.to_datetime(tasks_df['DOS']).dt.strftime('%Y-%m-%d')

            # Metrics
            total_tasks = len(tasks_df)
            total_duration = tasks_df['Duration'].sum() if 'Duration' in tasks_df.columns else 0
            
            m1, m2 = st.columns(2)
            m1.metric("Total Tasks", total_tasks)
            m2.metric("Total Duration", f"{total_duration} mins")

            # --- Daily View: Editable ---
            if view_type == "Daily":
                st.markdown("**Edit tasks below and click Save Changes to update**")

                # Store original values BEFORE data_editor for comparison
                # Use a key that includes date but NOT any session-specific parts
                original_key = f"original_coord_data_{user_id}_{display_period}"

                if original_key not in st.session_state:
                    # First time loading this date - store the original data from DB
                    st.session_state[original_key] = tasks_df[['Task ID', 'Patient Name', 'DOS', 'Duration', 'Service Type', 'Notes']].copy()

                # Use simple column config without disabled - let data_editor handle editability
                edited_df = st.data_editor(
                    tasks_df[['Patient Name', 'DOS', 'Duration', 'Service Type', 'Notes']],
                    use_container_width=True,
                    hide_index=True,
                    key=f"coordinator_task_editor_{user_id}_{display_period}",
                    num_rows="fixed"
                )
                
                # Save button
                if st.button("💾 Save Changes", type="primary", key=f"save_coord_tasks_{user_id}_{display_period}"):
                    try:
                        # Update database with edited values
                        conn_update = database.get_db_connection()
                        updates_made = 0

                        for i, (idx, row) in enumerate(edited_df.iterrows()):
                            orig_row = st.session_state[original_key].iloc[i]
                            task_id = orig_row['Task ID']  # Get the unique task ID

                            # Check if any editable fields changed - use safer comparison
                            duration_changed = pd.notna(row['Duration']) and pd.notna(orig_row['Duration']) and int(row['Duration']) != int(orig_row['Duration'])
                            type_changed = str(row['Service Type']) != str(orig_row['Service Type'])
                            notes_changed = str(row['Notes']) != str(orig_row['Notes'])

                            if duration_changed or type_changed or notes_changed:
                                # Update the database using unique task ID
                                conn_update.execute(f"""
                                    UPDATE {table_name}
                                    SET duration_minutes = ?,
                                        task_type = ?,
                                        notes = ?
                                    WHERE coordinator_task_id = ?
                                """, (
                                    int(row['Duration']) if pd.notna(row['Duration']) else 0,
                                    str(row['Service Type']),
                                    str(row['Notes']),
                                    task_id
                                ))
                                updates_made += 1

                        conn_update.commit()
                        conn_update.close()

                        if updates_made > 0:
                            st.success(f"✅ Saved {updates_made} task update(s)!")
                            # Clear original state so it gets reloaded from DB on next rerun
                            del st.session_state[original_key]
                            st.rerun()
                        else:
                            st.info("No changes detected.")
                    except Exception as e:
                        st.error(f"Error saving changes: {e}")
                        import traceback
                        st.error(traceback.format_exc())
            
            # --- Weekly/Monthly Views: Read-only ---
            else:
                st.dataframe(
                    tasks_df,
                    use_container_width=True,
                    hide_index=True
                )

            csv = tasks_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"coordinator_tasks_{user_id}_{view_type}_{display_period}.csv",
                mime="text/csv"
            )
        else:
            st.info(f"No tasks found for the selected {view_type.lower()} period.")

    except Exception as e:
        st.error(f"Error loading task review: {e}")
    finally:
        conn.close()
