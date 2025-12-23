"""
Weekly Provider Billing Dashboard - Phase 2 Implementation
Manages provider task billing workflow with status tracking and audit trail.

Uses provider_task_billing_status table (workflow-driven) instead of raw tasks.
Only accessible to Harpreet (Admin) and Justin (Superuser) for marking as billed.
"""

import calendar
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src import database
from src.config.ui_style_config import (
    get_metric_label,
    get_section_title,
)


def ensure_billing_data_populated():
    """Ensure provider_task_billing_status table is populated from all provider_tasks monthly tables"""
    conn = database.get_db_connection()
    try:
        # Get all provider_tasks_YYYY_MM tables
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE 'provider_tasks_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Process each monthly table
        for table_name in tables:
            insert_query = f"""
            INSERT OR IGNORE INTO provider_task_billing_status (
                provider_task_id,
                provider_id,
                provider_name,
                patient_name,
                task_date,
                billing_week,
                week_start_date,
                week_end_date,
                task_description,
                minutes_of_service,
                billing_code,
                billing_code_description,
                billing_status,
                is_billed,
                billed_date,
                billed_by,
                is_invoiced,
                invoiced_date,
                is_claim_submitted,
                claim_submitted_date,
                is_insurance_processed,
                insurance_processed_date,
                is_approved_to_pay,
                approved_to_pay_date,
                is_paid,
                paid_date,
                is_carried_over,
                original_billing_week,
                carryover_reason,
                billing_notes,
                billing_company,
                created_date,
                updated_date
            )
            SELECT
                pt.provider_task_id,
                pt.provider_id,
                COALESCE(u.full_name, 'Unknown Provider') as provider_name,
                COALESCE(pt.patient_name, pt.patient_id) as patient_name,
                pt.task_date,
                strftime('%Y-%W', pt.task_date) as billing_week,
                strftime('%Y-%m-%d', pt.task_date, '-6 days', 'weekday 1') as week_start_date,
                strftime('%Y-%m-%d', pt.task_date, '+0 days', 'weekday 0') as week_end_date,
                pt.task_description,
                pt.minutes_of_service,
                COALESCE(pt.billing_code, 'Not_Billable') as billing_code,
                COALESCE(
                    pt.billing_code_description,
                    pt.task_description || ' - Default'
                ) as billing_code_description,
                'Pending' as billing_status,
                0 as is_billed,
                NULL as billed_date,
                NULL as billed_by,
                0 as is_invoiced,
                NULL as invoiced_date,
                0 as is_claim_submitted,
                NULL as claim_submitted_date,
                0 as is_insurance_processed,
                NULL as insurance_processed_date,
                0 as is_approved_to_pay,
                NULL as approved_to_pay_date,
                0 as is_paid,
                NULL as paid_date,
                0 as is_carried_over,
                NULL as original_billing_week,
                NULL as carryover_reason,
                NULL as billing_notes,
                NULL as billing_company,
                CURRENT_TIMESTAMP as created_date,
                CURRENT_TIMESTAMP as updated_date
            FROM {table_name} pt
                LEFT JOIN users u ON pt.provider_id = u.user_id
            WHERE pt.billing_code IS NOT NULL
                AND pt.billing_code != 'Not_Billable'
                AND pt.task_date IS NOT NULL
                AND pt.provider_id IS NOT NULL
            """
            conn.execute(insert_query)
        
        conn.commit()
    except Exception as e:
        st.warning(f"Note: Could not auto-populate billing data: {e}")
    finally:
        conn.close()


def get_available_years():
    """Get list of available years from provider_task_billing_status table based on week_start_date"""
    conn = database.get_db_connection()
    try:
        query = """
        SELECT DISTINCT
            STRFTIME('%Y', week_start_date) as year
        FROM provider_task_billing_status
        WHERE week_start_date IS NOT NULL
        ORDER BY year DESC
        """
        rows = conn.execute(query).fetchall()

        years = []
        years_set = set()
        
        for row in rows:
            try:
                year_str = row[0]
                if year_str and isinstance(year_str, str):
                    if year_str not in years_set:
                        years_set.add(year_str)
                        years.append({"year": year_str, "display": year_str})
            except (ValueError, IndexError, TypeError):
                continue

        return years if years else []
    except Exception as e:
        st.error(f"Error getting available years: {e}")
        return []
    finally:
        conn.close()


def get_weeks_for_year(year):
     """Get actual week numbers (01-52) for a given year from the database"""
     conn = database.get_db_connection()
     try:
         query = """
         SELECT DISTINCT
             billing_week,
             week_start_date,
             week_end_date
         FROM provider_task_billing_status
         WHERE STRFTIME('%Y', week_start_date) = ?
         ORDER BY billing_week ASC
         """
         rows = conn.execute(query, (year,)).fetchall()

         weeks = []
         # Add default "Select a Week" option
         weeks.append(
             {
                 "billing_week": None,
                 "week_start_date": None,
                 "week_end_date": None,
                 "display": "Select a Week",
             }
         )
         
         for row in rows:
             try:
                 week_num = row[0]  # e.g., "2025-01"
                 week_start = row[1]
                 week_end = row[2]
                 # Extract just the week number from YYYY-WW format
                 week_part = week_num.split('-')[1] if '-' in week_num else week_num
                 weeks.append(
                     {
                         "billing_week": week_num,
                         "week_start_date": week_start,
                         "week_end_date": week_end,
                         "display": f"Week {week_part} - {week_start}",
                     }
                 )
             except (ValueError, IndexError, TypeError):
                 continue

         return weeks
     except Exception as e:
         st.error(f"Error getting weeks for year {year}: {e}")
         return []
     finally:
         conn.close()


def get_billing_providers():
    """Get list of available providers from provider_task_billing_status table"""
    conn = database.get_db_connection()
    try:
        query = """
        SELECT DISTINCT
            provider_id,
            provider_name
        FROM provider_task_billing_status
        WHERE provider_name IS NOT NULL
        ORDER BY provider_name
        """
        rows = conn.execute(query).fetchall()

        providers = []
        providers.append(
            {"provider_id": None, "provider_name": None, "display": "All Providers"}
        )
        for row in rows:
            try:
                provider_id = row[0]
                provider_name = row[1]
                providers.append(
                    {
                        "provider_id": provider_id,
                        "provider_name": provider_name,
                        "display": provider_name,
                    }
                )
            except (ValueError, IndexError):
                continue

        return providers
    except Exception as e:
        st.error(f"Error getting available providers: {e}")
        return []
    finally:
        conn.close()


def get_available_billing_weeks():
    """Get list of available billing weeks from provider_task_billing_status table"""
    conn = database.get_db_connection()
    try:
        query = """
        SELECT DISTINCT
            billing_week,
            week_start_date,
            week_end_date
        FROM provider_task_billing_status
        WHERE billing_week IS NOT NULL
        ORDER BY billing_week DESC
        LIMIT 52
        """
        rows = conn.execute(query).fetchall()

        weeks = []
        for row in rows:
            try:
                billing_week = row[0]
                week_start = row[1]
                week_end = row[2]
                weeks.append(
                    {
                        "billing_week": billing_week,
                        "week_start_date": week_start,
                        "week_end_date": week_end,
                        "display": f"{week_start} to {week_end}",
                    }
                )
            except (ValueError, IndexError):
                continue

        return weeks
    except Exception as e:
        st.error(f"Error getting available billing weeks: {e}")
        return []
    finally:
        conn.close()


def get_provider_billing_data(
    billing_week=None, billing_status=None, provider_filter=None
):
    """
    Get provider task billing data from workflow table.

    Args:
        billing_week: Optional filter by billing week
        billing_status: Optional filter by billing status (Pending, Billed, Invoiced, etc.)
        provider_filter: Optional filter by provider name

    Returns:
        DataFrame with billing records
    """
    conn = database.get_db_connection()
    try:
        query = """
        SELECT
            ptbs.billing_status_id,
            ptbs.provider_id,
            ptbs.provider_name,
            ptbs.patient_name,
            ptbs.patient_name as patient_id,
            ptbs.task_date,
            ptbs.task_description,
            ptbs.minutes_of_service,
            ptbs.billing_code,
            ptbs.billing_code_description,
            ptbs.billing_week,
            ptbs.week_start_date,
            ptbs.week_end_date,
            ptbs.billing_status,
            ptbs.is_billed,
            ptbs.billed_date,
            ptbs.billed_by,
            ptbs.billing_company,
            ptbs.is_invoiced,
            ptbs.is_claim_submitted,
            ptbs.is_insurance_processed,
            ptbs.is_approved_to_pay,
            ptbs.is_paid,
            ptbs.created_date,
            ptbs.updated_date,
            '' as facility
        FROM provider_task_billing_status ptbs
        WHERE 1=1
        """

        params = []

        if billing_week:
            query += " AND ptbs.billing_week = ?"
            params.append(billing_week)

        if billing_status:
            query += " AND ptbs.billing_status = ?"
            params.append(billing_status)

        if provider_filter:
            query += " AND ptbs.provider_name = ?"
            params.append(provider_filter)

        query += " ORDER BY ptbs.task_date DESC, ptbs.provider_name, ptbs.patient_name"

        df = pd.read_sql_query(query, conn, params=params)
        return df

    except Exception as e:
        st.error(f"Error getting provider billing data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_billing_summary(billing_week=None, provider_filter=None):
    """Get summary statistics for billing week"""
    conn = database.get_db_connection()
    try:
        # Import the processor to use its enhanced summary method
        from src.billing.weekly_billing_processor import WeeklyBillingProcessor
        processor = WeeklyBillingProcessor()
        
        # Use the processor's enhanced method which supports year filtering
        # For dashboard summary, we'll get the overall summary without provider/year filters
        # but we can pass the billing_week for specific week filtering
        summary = processor.get_billing_summary(billing_week, conn, provider_filter, None, None)
        
        # Extract the overall summary data
        overall = summary.get('overall', {})
        if overall:
            return {
                "total_tasks": overall.get('total_tasks', 0),
                "total_minutes": overall.get('total_minutes', 0),
                "billed_tasks": overall.get('total_billed_tasks', 0),
                "pending_tasks": overall.get('total_tasks', 0) - overall.get('total_billed_tasks', 0),
                "invoiced_tasks": 0,  # Not in weekly billing reports table
                "unique_providers": 0,  # Not in weekly billing reports table
                "unique_patients": 0,  # Not in weekly billing reports table
            }
        else:
            # Fallback to basic query if no summary found
            query = """
            SELECT
                COUNT(*) as total_tasks,
                SUM(minutes_of_service) as total_minutes,
                COUNT(CASE WHEN is_billed = TRUE THEN 1 END) as billed_tasks,
                COUNT(CASE WHEN is_billed = FALSE THEN 1 END) as pending_tasks,
                COUNT(CASE WHEN is_invoiced = TRUE THEN 1 END) as invoiced_tasks,
                COUNT(DISTINCT provider_id) as unique_providers,
                COUNT(DISTINCT patient_name) as unique_patients
            FROM provider_task_billing_status
            WHERE 1=1
            """
            
            params = []
            if billing_week:
                query += " AND billing_week = ?"
                params.append(billing_week)
            
            if provider_filter:
                query += " AND provider_name = ?"
                params.append(provider_filter)
            
            result = conn.execute(query, params).fetchone()
            if result:
                return {
                    "total_tasks": result[0] or 0,
                    "total_minutes": result[1] or 0,
                    "billed_tasks": result[2] or 0,
                    "pending_tasks": result[3] or 0,
                    "invoiced_tasks": result[4] or 0,
                    "unique_providers": result[5] or 0,
                    "unique_patients": result[6] or 0,
                }
        return None
    except Exception as e:
        st.error(f"Error getting summary: {e}")
        return None
    finally:
        conn.close()


def get_billing_status_options():
    """Get available billing status values"""
    return [
        "All",
        "Pending",
        "Billed",
        "Invoiced",
        "Submitted",
        "Processed",
        "Approved to Pay",
        "Paid",
    ]


def can_mark_as_billed(user_role_ids):
    """Check if user can mark tasks as billed"""
    # Anyone with access to the billing report tab can mark tasks as billed
    # No restrictive role check - if they can access the dashboard, they can edit
    return True


def export_for_3rd_party_biller(df):
    """
    Export billing data for 3rd party biller.
    Excludes internal-only columns (paid_by_zen, audit columns, etc.)
    """
    export_cols = [
        "billing_status_id",
        "provider_id",
        "provider_name",
        "patient_id",
        "patient_name",
        "facility",
        "task_date",
        "task_description",
        "minutes_of_service",
        "billing_code",
        "billing_code_description",
        "billing_week",
        "week_start_date",
        "week_end_date",
        "billing_status",
    ]

    available_cols = [col for col in export_cols if col in df.columns]
    return df[available_cols]


def display_weekly_provider_billing_dashboard(user_id=None, user_role_ids=None):
    # Auto-populate billing data from provider_tasks if empty
    ensure_billing_data_populated()
    
    # Process weekly billing reports on dashboard load if needed
    # Only process if we're on a new week or if there's no existing report
    try:
        from src.billing.weekly_billing_processor import WeeklyBillingProcessor
        from datetime import datetime
        processor = WeeklyBillingProcessor()
        
        # Check if we have a recent weekly report for current week
        current_week, _, _ = processor.get_current_billing_week()
        
        # Try to get existing data for this week from provider_task_billing_status
        conn = database.get_db_connection()
        try:
            existing_data = conn.execute(
                "SELECT COUNT(*) FROM provider_task_billing_status WHERE billing_week = ?",
                (current_week,)
            ).fetchone()
            
            # Only process if we don't have data for this week
            if not existing_data or existing_data[0] == 0:
                # Process current week's billing reports
                processor.process_weekly_billing()
        except Exception as e:
            # If there's an issue checking existing reports, still try to process
            processor.process_weekly_billing()
        finally:
            conn.close()
            
    except Exception as e:
        # Log and show warning but don't break the dashboard
        st.warning(f"Warning: Could not process weekly billing reports: {e}")
        import logging
        logging.getLogger(__name__).warning(f"Weekly billing processing failed: {e}")
    
    # Custom CSS for better dropdown width control
    st.markdown("""
    <style>
    /* Make billing status dropdown width fit content */
    div[data-baseweb="selectbox"] > div > div > select {
        min-width: fit-content !important;
        width: fit-content !important;
        max-width: 300px !important;
    }
    
    /* Provider dropdown - also fit content */
    div[data-testid="stSelectbox-1"] select,
    div[data-testid="stSelectbox-2"] select,
    div[data-testid="stSelectbox-3"] select {
        min-width: fit-content !important;
        width: fit-content !important;
        max-width: 250px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check if user has permission to mark tasks as billed
    can_edit = can_mark_as_billed(user_role_ids or [])

    if not can_edit:
        st.info(
            "ℹ️ View Mode: You can view billing data but cannot modify status."
        )

    # Get available weeks
    weeks = get_available_billing_weeks()

    if not weeks:
        st.info(
            "No provider billing data available yet. Data will appear once tasks are imported."
        )
        return

    # Filter controls - All in one row: Year | Week | Provider | Status
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**Year**")
        years = get_available_years()
        if years:
            selected_year = st.selectbox(
                "Select Year",
                options=years,
                format_func=lambda x: x["display"],
                key="provider_billing_year",
            )
        else:
            st.info("No years available")
            selected_year = None

    with col2:
        st.markdown("**Week**")
        if selected_year:
            # Get simple week numbers (01-52) for selected year
            available_weeks = get_weeks_for_year(selected_year["year"])
            selected_week = st.selectbox(
                "Select Week",
                options=available_weeks,
                format_func=lambda x: x["display"],
                key="provider_billing_week",
            )
        else:
            st.info("Select year first")
            selected_week = None

    with col3:
        st.markdown("**Provider**")
        providers = get_billing_providers()
        if providers:
            selected_provider = st.selectbox(
                "Select Provider",
                options=providers,
                format_func=lambda x: x["display"],
                key="billing_provider",
            )
        else:
            st.info("No providers available")
            selected_provider = None

    with col4:
        st.markdown("**Status**")
        billing_status_options = get_billing_status_options()
        selected_status = st.selectbox(
            "Filter by Billing Status",
            options=billing_status_options,
            key="provider_billing_status",
        )

    # Main content - handle the filter logic
    if selected_week:
        billing_week = selected_week["billing_week"]
    else:
        billing_week = None

    status_filter = None if selected_status == "All" else selected_status

    # Get provider filter for data query
    provider_filter = None
    if selected_provider and selected_provider["provider_id"] is not None:
        provider_filter = selected_provider["provider_name"]

    # Get summary
    summary = get_billing_summary(billing_week, provider_filter)

    if summary:
        st.markdown("### Billing Summary")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                get_metric_label("Total Tasks"),
                f"{summary['total_tasks']:,.0f}",
            )

        with col2:
            st.metric(
                get_metric_label("Total Minutes"),
                f"{summary['total_minutes']:,.0f}",
            )

        with col3:
            billed_pct = (
                (summary["billed_tasks"] / summary["total_tasks"] * 100)
                if summary["total_tasks"] > 0
                else 0
            )
            st.metric(
                get_metric_label("Billed Tasks"),
                f"{summary['billed_tasks']:,.0f}",
                delta=f"{billed_pct:.1f}%",
            )

        with col4:
            st.metric(
                get_metric_label("Pending Billed"),
                f"{summary['pending_tasks']:,.0f}",
            )

        with col5:
            st.metric(
                get_metric_label("Unique Providers"),
                f"{summary['unique_providers']:,.0f}",
            )

    # Get detailed data
    billing_df = get_provider_billing_data(
        billing_week, status_filter, provider_filter
    )

    if not billing_df.empty:
        show_audit_trail = st.checkbox("Show Audit Trail", value=False)

        # Display filtered data (already filtered at top level by Billing Status)
        display_df = billing_df.copy()

        # Display columns based on audit trail toggle
        if show_audit_trail:
            display_cols = [
                "provider_name",
                "patient_name",
                "patient_id",
                "facility",
                "task_date",
                "task_description",
                "minutes_of_service",
                "billing_code",
                "billing_status",
                "billing_company",
                "is_billed",
                "billed_date",
                "billed_by",
                "updated_date",
            ]
        else:
            display_cols = [
                "provider_name",
                "patient_name",
                "patient_id",
                "facility",
                "task_date",
                "task_description",
                "minutes_of_service",
                "billing_code",
                "billing_status",
                "billing_company",
            ]

        available_cols = [col for col in display_cols if col in display_df.columns]

        # Row selection and actions functionality
        if can_edit and not display_df.empty:
            st.markdown("### Billing Actions")
            
            # Create fresh editable dataframe with current filtered data
            editable_df = display_df[available_cols].copy()
            editable_df.insert(0, "☐ Select", False)
            
            # Display editable dataframe with selection column
            st.markdown("**Check rows below to select them for billing actions:**")
            edited_df = st.data_editor(
                editable_df,
                use_container_width=True,
                hide_index=True,
                key="provider_billing_editor",
            )
            
            # Get selected rows
            selected_rows = edited_df[edited_df["☐ Select"] == True]
            
            if not selected_rows.empty:
                # Get the billing_status_ids of selected rows
                selected_cols = [col for col in selected_rows.columns if col != "☐ Select"]
                billing_status_col_idx = available_cols.index("billing_status_id") if "billing_status_id" in available_cols else 0
                
                # Match selected rows back to original dataframe to get billing_status_ids
                task_ids = []
                for idx, sel_row in selected_rows.iterrows():
                    # Find matching row in original dataframe
                    for orig_idx, orig_row in display_df.iterrows():
                        match = True
                        for col in available_cols:
                            if col in sel_row.index and col in orig_row.index:
                                if str(sel_row[col]) != str(orig_row[col]):
                                    match = False
                                    break
                        if match:
                            task_ids.append(int(orig_row["billing_status_id"]))
                            break
                
                if task_ids:
                    st.markdown("---")
                    st.success(f"✓ {len(task_ids)} row(s) selected for action")
                    
                    # Action buttons in two columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Assign Billing Company")
                        billing_company_input = st.text_input(
                            "Medicare Billing Company Name",
                            placeholder="e.g., Acme Healthcare Billing",
                            key="billing_company_name",
                        )
                        
                        if st.button("Assign Billing Company", key="assign_company_btn"):
                            if not billing_company_input or billing_company_input.strip() == "":
                                st.error("Please enter a billing company name.")
                            else:
                                success, message, updated_count = (
                                    database.update_billing_company(
                                        task_ids, billing_company_input.strip(), user_id
                                    )
                                )
                                
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                    
                    with col2:
                        st.markdown("#### Mark as Billed")
                        st.markdown("")  # Spacer
                        if st.button("Mark Selected as Billed", type="primary", key="mark_billed_btn"):
                            success, message, updated_count = (
                                database.mark_provider_tasks_as_billed(
                                    task_ids, user_id
                                )
                            )
                            
                            if success:
                                st.success(message)
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(message)
            else:
                st.info("👆 Check the '☐ Select' column to select rows for billing actions")

        # Export options
        st.markdown("### Export Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Export for 3rd party biller
            export_df = export_for_3rd_party_biller(display_df)
            csv_data = export_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download for Biller (CSV)",
                data=csv_data,
                file_name=f"provider_billing_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

        with col2:
            # Export all data
            csv_all = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Full Data (CSV)",
                data=csv_all,
                file_name=f"provider_billing_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

        with col3:
            # Export pending only
            pending_df = display_df[display_df["is_billed"] == False]
            if not pending_df.empty:
                csv_pending = pending_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Pending (CSV)",
                    data=csv_pending,
                    file_name=f"provider_billing_pending_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

    else:
        st.info("No billing data available for selected filters")


if __name__ == "__main__":
    # For testing purposes
    display_weekly_provider_billing_dashboard(
        user_id=1,
        user_role_ids=[34],  # Admin for testing
    )
