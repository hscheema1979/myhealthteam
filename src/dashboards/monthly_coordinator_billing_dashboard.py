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


def get_cache_staleness(year, month):
    """Check if cache table is missing or stale compared to source data"""
    conn = get_db_connection()
    try:
        ym = f"{year}_{month:02d}"
        cache_table = f"coordinator_monthly_billing_cache_{ym}"
        source_table = f"csv_coordinator_tasks_{ym}"

        cursor = conn.cursor()

        # Check if cache table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (cache_table,),
        )
        cache_exists = cursor.fetchone() is not None

        # Check if source table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (source_table,),
        )
        source_exists = cursor.fetchone() is not None

        if not source_exists:
            return "NO_SOURCE"
        if not cache_exists:
            return "MISSING"

        # Compare timestamps - check if source is newer than cache
        # Get max update date from cache
        cursor.execute(f"SELECT MAX(updated_date) FROM {cache_table}")
        cache_date = cursor.fetchone()[0]

        # Get max created date from source (which updates on CSV import)
        cursor.execute(f"SELECT MAX(created_date) FROM {source_table}")
        source_date = cursor.fetchone()[0]

        if not cache_date or not source_date:
            return "STALE"

        # If source is newer, cache is stale
        if source_date > cache_date:
            return "STALE"

        return "FRESH"

    except Exception as e:
        print(f"Error checking cache staleness: {e}")
        return "ERROR"
    finally:
        conn.close()


def rebuild_billing_cache(year, month):
    """Rebuild the billing cache for a specific month"""
    conn = get_db_connection()
    try:
        ym = f"{year}_{month:02d}"
        source_table = f"csv_coordinator_tasks_{ym}"
        cache_table = f"coordinator_monthly_billing_cache_{ym}"

        cursor = conn.cursor()

        # Check if source table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name = ?
        """,
            (source_table,),
        )
        if not cursor.fetchone():
            print(f"Source table {source_table} not found")
            return False

        # Create cache table if not exists
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {cache_table} (
                cache_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                facility TEXT,
                task_count INTEGER DEFAULT 0,
                total_minutes INTEGER DEFAULT 0,
                billing_code TEXT,
                billing_description TEXT,
                billing_status TEXT DEFAULT 'Pending',
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                source_system TEXT DEFAULT 'CSV_IMPORT',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(patient_id, year, month)
            )
        """)

        # Clear existing cache for this month
        cursor.execute(f"DELETE FROM {cache_table} WHERE year = ? AND month = ?", (year, month))

        # Populate with billing codes using SQL
        cursor.execute(f"""
            INSERT INTO {cache_table}
            (patient_id, facility, task_count, total_minutes, billing_code, billing_description,
             billing_status, year, month, source_system, updated_date)
            SELECT
                ct.patient_id,
                COALESCE(p.facility, '') as facility,
                ct.task_count,
                ct.total_minutes,
                CASE
                    WHEN ct.total_minutes < 20 THEN 'NOT_BILLABLE'
                    WHEN ct.total_minutes < 40 THEN '99406'
                    WHEN ct.total_minutes < 60 THEN '99409'
                    WHEN ct.total_minutes < 90 THEN '99412'
                    ELSE '99415'
                END as billing_code,
                CASE
                    WHEN ct.total_minutes < 20 THEN 'Less than 20 minutes'
                    WHEN ct.total_minutes < 40 THEN '20-39 minutes'
                    WHEN ct.total_minutes < 60 THEN '40-59 minutes'
                    WHEN ct.total_minutes < 90 THEN '60-89 minutes'
                    ELSE '90+ minutes'
                END as billing_description,
                'Pending' as billing_status,
                {year} as year,
                {month} as month,
                'CSV_IMPORT' as source_system,
                datetime('now') as updated_date
            FROM (
                SELECT patient_id, COUNT(*) as task_count, SUM(duration_minutes) as total_minutes
                FROM {source_table}
                WHERE patient_id IS NOT NULL
                GROUP BY patient_id
            ) ct
            LEFT JOIN patients p ON ct.patient_id = p.patient_id
            WHERE ct.total_minutes >= 20
        """)

        conn.commit()
        count = cursor.rowcount
        print(f"Rebuilt cache for {ym}: {count} records")
        return True

    except Exception as e:
        print(f"Error rebuilding cache: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def ensure_fresh_cache(year, month):
    """Check cache staleness and rebuild if needed. Returns status."""
    status = get_cache_staleness(year, month)

    if status in ("MISSING", "STALE", "ERROR"):
        print(f"Cache status for {year}-{month:02d}: {status} - rebuilding...")
        success = rebuild_billing_cache(year, month)
        return "REBUILT" if success else "FAILED"
    elif status == "NO_SOURCE":
        print(f"Cache status for {year}-{month:02d}: {status}")
        return status
    else:
        print(f"Cache status for {year}-{month:02d}: {status} - using existing cache")
        return status


def get_available_months():
    """Get list of available months from both CSV imports and live tables"""
    conn = get_db_connection()
    try:
        months = []

        # Get months from CSV coordinator task tables
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'csv_coordinator_tasks_20%'
            ORDER BY name DESC
        """)
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            parts = table_name.split("_")
            if len(parts) >= 4:
                try:
                    year = int(parts[3])
                    month = int(parts[4])
                    month_name = calendar.month_name[month]

                    months.append({
                        "year": year,
                        "month": month,
                        "display": f"{month_name} {year} (CSV Import)",
                        "data_type": "CSV_IMPORT",
                        "table": table_name
                    })
                except (ValueError, IndexError):
                    continue

        # Get months from live coordinator_tasks tables
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'coordinator_tasks_20%'
            ORDER BY name DESC
        """)
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            parts = table_name.split("_")
            if len(parts) >= 4:
                try:
                    year = int(parts[2])
                    month = int(parts[3])
                    month_name = calendar.month_name[month]

                    months.append({
                        "year": year,
                        "month": month,
                        "display": f"{month_name} {year} (Live)",
                        "data_type": "LIVE",
                        "table": table_name
                    })
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


def get_coordinator_billing_data(selected_month):
    """Get coordinator billing data from cache table (pre-calculated)"""
    conn = get_db_connection()
    try:
        year = selected_month["year"]
        month = selected_month["month"]
        data_type = selected_month.get("data_type", "LIVE")

        ym = f"{year}_{month:02d}"
        cache_table = f"coordinator_monthly_billing_cache_{ym}"

        # For CSV imports, ensure fresh cache and read from it
        if data_type == "CSV_IMPORT":
            # Check staleness and rebuild if needed
            cache_status = ensure_fresh_cache(year, month)

            if cache_status == "NO_SOURCE":
                st.warning(f"Source data table not found for {year}-{month:02d}")
                return pd.DataFrame()
            if cache_status == "FAILED":
                st.error(f"Failed to build billing cache for {year}-{month:02d}")
                return pd.DataFrame()

            # Read from pre-calculated cache
            query = f"""
            SELECT
                patient_id,
                facility,
                task_count,
                total_minutes,
                billing_code,
                billing_description,
                billing_status
            FROM {cache_table}
            ORDER BY total_minutes DESC
            """
            df = pd.read_sql_query(query, conn)
            return df

        # For live data, calculate on-the-fly (no cache for live data yet)
        table_name = selected_month.get("table", f"coordinator_tasks_{year}_{month:02d}")

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

        # Live table column names
        query = f"""
        SELECT
            ct.patient_id,
            COUNT(*) as task_count,
            SUM(ct.duration_minutes) as total_minutes,
            COALESCE(p.facility, '') as facility
        FROM (
            SELECT coordinator_id, patient_id, task_date, task_type, duration_minutes
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

        # Filter out NOT_BILLABLE patients (less than 20 minutes)
        df = df[df["billing_code"] != "NOT_BILLABLE"].copy()

        return df

    except Exception as e:
        st.error(f"Error getting coordinator billing data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_coordinator_summary(selected_month):
    """Get summary statistics from cache (for CSV) or live calculation"""
    conn = get_db_connection()
    try:
        year = selected_month["year"]
        month = selected_month["month"]
        data_type = selected_month.get("data_type", "LIVE")

        ym = f"{year}_{month:02d}"
        cache_table = f"coordinator_monthly_billing_cache_{ym}"

        # For CSV imports, read from cache table
        if data_type == "CSV_IMPORT":
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name = ?
            """,
                (cache_table,),
            )

            if not cursor.fetchone():
                return None

            query = f"""
            SELECT
                COUNT(*) as total_patients,
                SUM(task_count) as total_tasks,
                SUM(total_minutes) as total_minutes
            FROM {cache_table}
            """
            result = conn.execute(query).fetchone()
            if result:
                return {
                    "total_patients": result[0],
                    "total_tasks": result[1],
                    "total_minutes": result[2] or 0,
                }
            return None

        # For live data, calculate on-the-fly
        table_name = selected_month.get("table", f"coordinator_tasks_{year}_{month:02d}")

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

        # Live table column names
        query = f"""
        SELECT
            COUNT(*) as total_patients,
            SUM(task_count) as total_tasks,
            SUM(total_minutes) as total_minutes
        FROM (
            SELECT patient_id, COUNT(*) as task_count, SUM(duration_minutes) as total_minutes
            FROM {table_name}
            WHERE patient_id IS NOT NULL
            GROUP BY patient_id
            HAVING SUM(duration_minutes) >= 20
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
            data_type = selected_month.get("data_type", "")

            with col2:
                st.metric("Selected Period", selected_month["display"])
                if data_type:
                    st.caption(f"Data Source: {data_type}")

            # Get summary data
            summary = get_coordinator_summary(selected_month)

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
            billing_df = get_coordinator_billing_data(selected_month)

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

                # Create cache key based on selection and filters
                cache_key = f"{year}_{month:02d}_{data_type}_{selected_code}_{show_pending}_{len(billing_df)}"

                # Check if we need to rebuild the editable dataframe
                rebuild = True
                if "billing_cache_key" in st.session_state:
                    if st.session_state.billing_cache_key == cache_key:
                        # Check for old "☐ Select" column that would cause encoding errors
                        if "coordinator_billing_editable_df" in st.session_state:
                            df = st.session_state.coordinator_billing_editable_df
                            if isinstance(df, pd.DataFrame) and "☐ Select" in df.columns:
                                rebuild = True
                            else:
                                rebuild = False

                if rebuild:
                    # Build editable dataframe
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
                    editable_df.insert(0, "Pick", False)
                    st.session_state.coordinator_billing_editable_df = editable_df
                    st.session_state.billing_cache_key = cache_key

                # Display table with selection capability
                st.markdown("### Select Rows for Actions")
                st.markdown("**Check rows below to select them for actions:**")
                edited_df = st.data_editor(
                    st.session_state.coordinator_billing_editable_df,
                    use_container_width=True,
                    hide_index=True,
                    key="coordinator_billing_editor",
                )

                # Update session state with user edits
                st.session_state.coordinator_billing_editable_df = edited_df

                # Get selected rows
                if "Pick" in edited_df.columns:
                    selected_rows = edited_df[edited_df["Pick"] == True]
                else:
                    selected_rows = pd.DataFrame()

                if not selected_rows.empty:
                    st.markdown("---")
                    st.success(f"[v] {len(selected_rows)} row(s) selected")

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
                                # TODO: Implement actual update function
                                st.rerun()

                    with col2:
                        st.markdown("#### Export Selected")
                        if st.button("Export Selected Rows", key="export_selected_btn"):
                            display_cols = [col for col in edited_df.columns if col != "Pick"]
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
                    st.info("&gt; Check the 'Pick' column to select rows for actions")

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
                    billing_df = get_coordinator_billing_data(month_data)

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
