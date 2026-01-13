import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
from src import database

def show(user_id):
    """Display monthly task review for providers with minutes editing only"""
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
                provider_task_id,
                patient_name,
                task_date,
                minutes_of_service,
                task_description
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
                    'task_description': 'Service Type'
                })

                tasks_df['DOS'] = pd.to_datetime(tasks_df['DOS']).dt.strftime('%Y-%m-%d')

                total_tasks = len(tasks_df)
                total_duration = tasks_df['Duration'].sum() if 'Duration' in tasks_df.columns else 0

                m1, m2 = st.columns(2)
                m1.metric("Total Tasks", total_tasks)
                m2.metric("Total Duration", f"{total_duration} mins")

                st.markdown("**Edit Duration (minutes) below and click Save Changes to update**")

                original_key = f"original_provider_monthly_data_{user_id}_{year}_{month}"

                if original_key not in st.session_state:
                    st.session_state[original_key] = tasks_df[['Task ID', 'Patient Name', 'DOS', 'Duration', 'Service Type']].copy()

                editor_key = f"provider_monthly_task_editor_{user_id}_{year}_{month}"
                edited_df = st.data_editor(
                    tasks_df[['Patient Name', 'DOS', 'Duration', 'Service Type']],
                    use_container_width=True,
                    hide_index=True,
                    key=editor_key,
                    num_rows="fixed",
                    column_config={
                        "Patient Name": st.column_config.TextColumn("Patient Name", width="medium", disabled=True),
                        "DOS": st.column_config.TextColumn("Date", width="small", disabled=True),
                        "Duration": st.column_config.NumberColumn("Duration (mins)", width="small", min_value=0, step=1),
                        "Service Type": st.column_config.TextColumn("Service Type", width="large", disabled=True),
                    }
                )

                if st.button("💾 Save Changes", type="primary", key=f"save_monthly_tasks_{user_id}_{year}_{month}"):
                    try:
                        original_with_idx = st.session_state[original_key].reset_index(drop=True)
                        edited_with_idx = edited_df.reset_index(drop=True)

                        conn_update = database.get_db_connection()
                        updates_made = 0

                        for i in range(len(edited_with_idx)):
                            orig_row = original_with_idx.iloc[i]
                            edited_row = edited_with_idx.iloc[i]
                            task_id = int(orig_row['Task ID'])

                            duration_changed = pd.notna(edited_row['Duration']) and pd.notna(orig_row['Duration']) and int(edited_row['Duration']) != int(orig_row['Duration'])

                            if duration_changed:
                                new_duration = int(edited_row['Duration']) if pd.notna(edited_row['Duration']) else 0

                                conn_update.execute(f"""
                                    UPDATE {table_name}
                                    SET minutes_of_service = {new_duration}
                                    WHERE provider_task_id = {task_id}
                                """)
                                updates_made += 1

                        conn_update.commit()
                        conn_update.close()

                        if updates_made > 0:
                            st.success(f"✅ Saved {updates_made} task update(s)!")
                            recalc_success, recalc_msg, recalc_count = database.recalculate_provider_monthly_summary(
                                year, month, user_id
                            )
                            if recalc_success:
                                st.info(f"📊 Summaries updated: {recalc_msg}")

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
