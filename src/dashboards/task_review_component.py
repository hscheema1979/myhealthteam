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
                    minutes_of_service,
                    task_description,
                    notes
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
                        'task_date': 'DOS',
                        'minutes_of_service': 'Duration',
                        'task_description': 'Service Type',
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
                        provider_task_id,
                        patient_name,
                        task_date,
                        minutes_of_service,
                        task_description,
                        notes
                    FROM {t_name}
                    WHERE provider_id = ? AND date(task_date) BETWEEN date(?) AND date(?)
                    ORDER BY task_date DESC
                    """
                    rows = conn.execute(query, (user_id, start_week, end_week)).fetchall()
                    all_rows.extend([dict(r) for r in rows])
                
                if all_rows:
                    tasks_df = pd.DataFrame(all_rows)
                    tasks_df = tasks_df.rename(columns={
                        'provider_task_id': 'Task ID',
                        'patient_name': 'Patient Name',
                        'task_date': 'DOS',
                        'minutes_of_service': 'Duration',
                        'task_description': 'Service Type',
                        'notes': 'Notes'
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
                    provider_task_id,
                    patient_name,
                    task_date,
                    minutes_of_service,
                    task_description,
                    notes
                FROM {table_name}
                WHERE provider_id = ?
                ORDER BY task_date DESC
                """
                rows = conn.execute(query, (user_id,)).fetchall()
                if rows:
                    tasks_df = pd.DataFrame([dict(r) for r in rows])
                    tasks_df = tasks_df.rename(columns={
                        'provider_task_id': 'Task ID',
                        'patient_name': 'Patient Name',
                        'task_date': 'DOS',
                        'minutes_of_service': 'Duration',
                        'task_description': 'Service Type',
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
                original_key = f"original_provider_data_{user_id}_{display_period}"

                if original_key not in st.session_state:
                    # First time loading this date - store the original data from DB
                    st.session_state[original_key] = tasks_df[['Task ID', 'Patient Name', 'DOS', 'Duration', 'Service Type', 'Notes']].copy()

                # Use data_editor WITH a key to preserve edits
                editor_key = f"provider_task_editor_{user_id}_{display_period}"
                edited_df = st.data_editor(
                    tasks_df[['Patient Name', 'DOS', 'Duration', 'Service Type', 'Notes']],
                    use_container_width=True,
                    hide_index=True,
                    key=editor_key,
                    num_rows="fixed"
                )

                # Save button
                if st.button("💾 Save Changes", type="primary", key=f"save_tasks_{user_id}_{display_period}"):
                    try:
                        # Create aligned copies for proper row matching
                        original_with_idx = st.session_state[original_key].reset_index(drop=True)
                        edited_with_idx = edited_df.reset_index(drop=True)

                        # Update database with edited values
                        conn_update = database.get_db_connection()
                        updates_made = 0

                        for i in range(len(edited_with_idx)):
                            orig_row = original_with_idx.iloc[i]
                            edited_row = edited_with_idx.iloc[i]
                            task_id = int(orig_row['Task ID'])  # Convert to int to avoid numpy type issues

                            # Check if any editable fields changed
                            duration_changed = pd.notna(edited_row['Duration']) and pd.notna(orig_row['Duration']) and int(edited_row['Duration']) != int(orig_row['Duration'])
                            type_changed = str(edited_row['Service Type']) != str(orig_row['Service Type'])
                            notes_changed = str(edited_row['Notes']) != str(orig_row['Notes'])

                            if duration_changed or type_changed or notes_changed:
                                # Use inline values for task_id to avoid numpy parameter binding issues
                                new_duration = int(edited_row['Duration']) if pd.notna(edited_row['Duration']) else 0
                                new_type = str(edited_row['Service Type']) if pd.notna(edited_row['Service Type']) else ""
                                new_notes = str(edited_row['Notes']) if pd.notna(edited_row['Notes']) else ""

                                conn_update.execute(f"""
                                    UPDATE {table_name}
                                    SET minutes_of_service = {new_duration},
                                        task_description = {repr(new_type)},
                                        notes = {repr(new_notes)}
                                    WHERE provider_task_id = {task_id}
                                """)
                                updates_made += 1

                        conn_update.commit()
                        conn_update.close()

                        if updates_made > 0:
                            st.success(f"✅ Saved {updates_made} task update(s)!")
                            # Recalculate the provider_monthly_summary to reflect the changes
                            from datetime import datetime
                            selected_date_obj = datetime.strptime(display_period, '%Y-%m-%d')
                            recalc_success, recalc_msg, recalc_count = database.recalculate_provider_monthly_summary(
                                selected_date_obj.year, selected_date_obj.month, user_id
                            )
                            if recalc_success:
                                st.info(f"📊 Summaries updated: {recalc_msg}")

                            # Clear both original AND editor state so fresh data loads
                            del st.session_state[original_key]
                            if editor_key in st.session_state:
                                del st.session_state[editor_key]
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
                    hide_index=True,
                    column_config={
                        "Patient Name": st.column_config.TextColumn("Patient Name", width="medium"),
                        "DOS": st.column_config.TextColumn("Date", width="small"),
                        "Duration": st.column_config.NumberColumn("Mins", width="small"),
                        "Service Type": st.column_config.TextColumn("Task/Service", width="large"),
                        "Notes": st.column_config.TextColumn("Notes", width="large"),
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
