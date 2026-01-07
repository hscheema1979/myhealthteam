"""
Monthly Coordinator Billing Dashboard
Aggregates coordinator minutes by patient with billing code assignment
"""

import calendar
import sqlite3
from datetime import datetime
import zipfile
import io

import pandas as pd
import streamlit as st


def get_db_connection():
    return sqlite3.connect("production.db")


def get_available_months():
    """Get list of available months from coordinator_tasks_YYYY_MM tables"""
    conn = get_db_connection()
    try:
        query = """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name LIKE 'coordinator_tasks_20%'
        ORDER BY name DESC
        """
        tables = conn.execute(query).fetchall()

        months = []
        for table in tables:
            table_name = table[0]
            parts = table_name.split("_")
            if len(parts) >= 4:
                try:
                    year = int(parts[2])
                    month = int(parts[3])
                    month_name = calendar.month_name[month]
                    months.append(
                        {
                            "year": year,
                            "month": month,
                            "display": f"{month_name} {year}",
                        }
                    )
                except (ValueError, IndexError):
                    continue

        return sorted(months, key=lambda x: (x["year"], x["month"]), reverse=True)
    except Exception as e:
        st.error(f"Error getting available months: {e}")
        return []
    finally:
        conn.close()


def get_billing_codes_for_minutes(minutes):
    """Determine billing code based on minutes of service using coordinator_billing_codes table"""
    if minutes is None or minutes == 0:
        return "NOT_BILLABLE", "Less than 20 minutes"

    conn = get_db_connection()
    try:
        # Query the coordinator_billing_codes table to find the appropriate code
        query = """
        SELECT billing_code, description
        FROM coordinator_billing_codes
        WHERE min_minutes <= ? AND max_minutes > ?
        ORDER BY min_minutes DESC
        LIMIT 1
        """
        result = conn.execute(query, (minutes, minutes)).fetchone()

        if result:
            return result[0], result[1]
        else:
            return "NOT_BILLABLE", "No matching billing code found"

    except Exception as e:
        st.error(f"Error getting billing code: {e}")
        return "ERROR", "Error determining billing code"
    finally:
        conn.close()


def get_coordinator_billing_data(year, month):
    """Get coordinator billing data aggregated by patient only"""
    conn = get_db_connection()
    try:
        table_name = f"coordinator_tasks_{year}_{month:02d}"

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (table_name,),
        )

        if not cursor.fetchone():
            return pd.DataFrame()

        query = f"""
        SELECT
            ct.patient_id,
            COUNT(DISTINCT ct.coordinator_id || '_' || ct.task_date || '_' || ct.task_type) as task_count,
            SUM(ct.duration_minutes) as total_minutes,
            COALESCE(p.facility, '') as facility
        FROM (
            SELECT DISTINCT coordinator_id, patient_id, task_date, task_type, duration_minutes
            FROM {table_name}
            WHERE patient_id IS NOT NULL
        ) ct
        LEFT JOIN patients p ON ct.patient_id = p.patient_id
        GROUP BY ct.patient_id
        ORDER BY total_minutes DESC
        """

        df = pd.read_sql_query(query, conn)

        # Apply billing codes based on minutes
        df["billing_code"] = df["total_minutes"].apply(
            lambda x: get_billing_codes_for_minutes(x)[0]
        )
        df["billing_description"] = df["total_minutes"].apply(
            lambda x: get_billing_codes_for_minutes(x)[1]
        )
        df["billing_status"] = "Pending"

        return df

    except Exception as e:
        st.error(f"Error getting coordinator billing data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_coordinator_summary(year, month):
    """Get summary statistics"""
    conn = get_db_connection()
    try:
        table_name = f"coordinator_tasks_{year}_{month:02d}"

        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (table_name,),
        )

        if not cursor.fetchone():
            return None

        query = f"""
        SELECT
            COUNT(DISTINCT patient_id) as total_patients,
            COUNT(*) as total_tasks,
            SUM(duration_minutes) as total_minutes
        FROM (
            SELECT DISTINCT coordinator_id, patient_id, task_date, task_type, duration_minutes
            FROM {table_name}
            WHERE patient_id IS NOT NULL
        )
        """

        result = conn.execute(query).fetchone()
        if result:
            return {
                "total_patients": result[0],
                "total_tasks": result[1],
                "total_minutes": result[2] or 0,
            }
        return None

    except Exception as e:
        st.error(f"Error getting summary: {e}")
        return None
    finally:
        conn.close()


def export_to_csv(df, filename):
    """Export dataframe to CSV"""
    return df.to_csv(index=False).encode("utf-8")


def display_monthly_coordinator_billing_dashboard():
    """Main billing dashboard"""
    # Get available months
    months = get_available_months()

    if not months:
        st.warning("No coordinator billing data available")
        return

    # Add tabs for Single Month View and Bulk Download
    tab1, tab2 = st.tabs(["📅 Single Month View", "📦 Bulk Download"])

    with tab1:
        # Month selector
        col1, col2 = st.columns(2)

        with col1:
            selected_month = st.selectbox(
                "Select Month", options=months, format_func=lambda x: x["display"], key="single_month_select"
            )

        if selected_month:
            year = selected_month["year"]
            month = selected_month["month"]

            with col2:
                st.metric("Selected Period", f"{calendar.month_name[month]} {year}")

            # Get summary data
            summary = get_coordinator_summary(year, month)

            if summary:
                st.subheader("Monthly Summary")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Patients", summary["total_patients"])
                with col2:
                    st.metric("Total Tasks", summary["total_tasks"])
                with col3:
                    st.metric("Total Minutes", f"{summary['total_minutes']:,.0f}")

            # Get detailed data
            billing_df = get_coordinator_billing_data(year, month)

            if not billing_df.empty:
                st.subheader("Billing Data by Patient")

                # Filters
                col1, col2 = st.columns(2)

                with col1:
                    billing_codes = ["All"] + sorted(
                        billing_df["billing_code"].unique().tolist()
                    )
                    selected_code = st.selectbox("Filter by Billing Code", billing_codes, key="single_code_filter")

                with col2:
                    show_pending = st.checkbox("Show Only Pending Codes", value=False, key="single_pending_filter")

                # Apply filters
                filtered_df = billing_df.copy()

                if selected_code != "All":
                    filtered_df = filtered_df[filtered_df["billing_code"] == selected_code]

                if show_pending:
                    filtered_df = filtered_df[filtered_df["billing_code"] == "PENDING"]

                # Display table with selection capability
                st.markdown("### Select Rows for Actions")

                # Initialize session state for editable dataframe
                if "coordinator_billing_editable_df" not in st.session_state:
                    display_cols = [
                        "patient_id",
                        "facility",
                        "task_count",
                        "total_minutes",
                        "billing_code",
                        "billing_description",
                        "billing_status",
                    ]
                    editable_df = filtered_df[display_cols].copy()
                    editable_df.insert(0, "☐ Select", False)
                    st.session_state.coordinator_billing_editable_df = editable_df

                # Display editable dataframe with selection column
                st.markdown("**Check rows below to select them for actions:**")
                edited_df = st.data_editor(
                    st.session_state.coordinator_billing_editable_df,
                    use_container_width=True,
                    hide_index=True,
                    key="coordinator_billing_editor",
                )

                # Update session state with edited dataframe
                st.session_state.coordinator_billing_editable_df = edited_df

                # Get selected rows
                selected_rows = edited_df[edited_df["☐ Select"] == True]

                if not selected_rows.empty:
                    st.markdown("---")
                    st.success(f"✓ {len(selected_rows)} row(s) selected")

                    # Action buttons
                    st.markdown("### Actions")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### Update Billing Code")
                        new_billing_code = st.text_input(
                            "New Billing Code",
                            placeholder="e.g., 99211, 99212",
                            key="coordinator_new_code",
                        )

                        if st.button("Update Billing Code", key="update_code_btn"):
                            if not new_billing_code or new_billing_code.strip() == "":
                                st.error("Please enter a billing code.")
                            else:
                                st.info(f"Would update {len(selected_rows)} row(s) with code: {new_billing_code}")
                                st.session_state.coordinator_billing_editable_df = None
                                # TODO: Implement actual update function

                    with col2:
                        st.markdown("#### Export Selected")
                        if st.button("Export Selected Rows", key="export_selected_btn"):
                            display_cols = [col for col in edited_df.columns if col != "☐ Select"]
                            selected_data = selected_rows[display_cols]
                            csv_data = export_to_csv(selected_data, "coordinator_billing_selected")
                            st.download_button(
                                label="Download Selected (CSV)",
                                data=csv_data,
                                file_name=f"coordinator_billing_selected_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv",
                                key="download_selected",
                            )
                else:
                    st.info("👆 Check the '☐ Select' column to select rows for actions")

                # Export buttons for all/filtered data
                st.markdown("---")
                st.subheader("Export Options")
                col1, col2, col3 = st.columns(3)

                with col1:
                    csv_data = export_to_csv(filtered_df, "coordinator_billing")
                    st.download_button(
                        label="Download Filtered Data (CSV)",
                        data=csv_data,
                        file_name=f"coordinator_billing_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )

                with col2:
                    csv_all = export_to_csv(billing_df, "coordinator_billing_all")
                    st.download_button(
                        label="Download All Data (CSV)",
                        data=csv_all,
                        file_name=f"coordinator_billing_all_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                    )

                with col3:
                    pending_df = billing_df[billing_df["billing_code"] == "PENDING"]
                    if not pending_df.empty:
                        csv_pending = export_to_csv(
                            pending_df, "coordinator_billing_pending"
                        )
                        st.download_button(
                            label="Download Pending Codes (CSV)",
                            data=csv_pending,
                            file_name=f"coordinator_billing_pending_{year}_{month:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                        )

            else:
                st.info("No billing data available for selected period")

    with tab2:
        st.markdown("### 📦 Bulk Download Multiple Months")
        st.markdown("Select multiple months to download individual CSV files for each month.")

        # Multi-select for months
        selected_months_bulk = st.multiselect(
            "Select Months to Download",
            options=months,
            format_func=lambda x: x["display"],
            key="bulk_month_select",
            help="Choose one or more months to download"
        )

        if selected_months_bulk:
            st.success(f"✓ {len(selected_months_bulk)} month(s) selected")

            # Create ZIP file for all selected months
            st.markdown("---")
            st.markdown("### Download All as ZIP")

            # Create in-memory ZIP file
            zip_buffer = io.BytesIO()
            total_files = 0

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for month_data in selected_months_bulk:
                    year = month_data["year"]
                    month = month_data["month"]

                    # Get the data for this month
                    billing_df = get_coordinator_billing_data(year, month)

                    if not billing_df.empty:
                        csv_data = billing_df.to_csv(index=False).encode('utf-8')
                        filename = f"coordinator_billing_{year}_{month:02d}.csv"
                        zip_file.writestr(filename, csv_data)
                        total_files += 1

            zip_buffer.seek(0)
            zip_data = zip_buffer.getvalue()

            # Download ZIP button
            col1, col2 = st.columns([2, 1])
            with col1:
                st.download_button(
                    label=f"📦 Download All {total_files} File(s) as ZIP",
                    data=zip_data,
                    file_name=f"coordinator_billing_bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    key="bulk_download_zip",
                )
            with col2:
                st.caption(f"ZIP size: {len(zip_data) / 1024:.1f} KB")
        else:
            st.info("👆 Select one or more months above to generate download buttons.")


if __name__ == "__main__":
    display_monthly_coordinator_billing_dashboard()
