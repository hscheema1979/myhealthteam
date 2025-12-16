"""
Weekly Provider Payroll Dashboard - Phase 2 Implementation
Manages provider payroll workflow with critical paid_by_zen tracking.

Uses provider_weekly_payroll_status table (workflow-driven).
CRITICAL: Shows paid_by_zen indicators to prevent double-payment to providers.
Access: Justin (Payroll Manager) only.
"""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src import database
from src.config.ui_style_config import (
    get_metric_label,
    get_section_title,
)


def get_available_months():
    """Get list of available months from provider_weekly_payroll_status table"""
    conn = database.get_db_connection()
    try:
        query = """
        SELECT DISTINCT
            pay_year,
            pay_week_start_date
        FROM provider_weekly_payroll_status
        WHERE pay_week_start_date IS NOT NULL
        ORDER BY pay_year DESC, pay_week_start_date DESC
        """
        rows = conn.execute(query).fetchall()

        # Use a set to avoid duplicate months
        months_set = set()
        months = []
        
        # Add "All Months" option first
        months.append(
            {"year": None, "month": None, "year_month": "all", "display": "All Months"}
        )
        
        for row in rows:
            try:
                year = row[0]
                date_str = row[1]
                
                # Parse the date string and format it properly
                if date_str and isinstance(date_str, str):
                    from datetime import datetime
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    month = date_obj.strftime('%m')
                    year_month = date_obj.strftime('%Y-%m')
                    display = date_obj.strftime('%B %Y')
                    
                    # Only add if we haven't seen this year_month before
                    if year_month not in months_set:
                        months_set.add(year_month)
                        months.append(
                            {
                                "year": year,
                                "month": month,
                                "year_month": year_month,
                                "display": display,
                            }
                        )
            except (ValueError, IndexError, TypeError) as e:
                # Skip problematic rows but continue processing
                continue

        # Sort months in descending order (most recent first), keeping "All Months" at top
        all_months = months[:1]
        other_months = sorted(months[1:], key=lambda x: x['year_month'], reverse=True)
        months = all_months + other_months

        return months
    except Exception as e:
        st.error(f"Error getting available months: {e}")
        return []
    finally:
        conn.close()


def get_available_providers():
    """Get list of available providers from provider_weekly_payroll_status table"""
    conn = database.get_db_connection()
    try:
        query = """
        SELECT DISTINCT
            provider_id,
            provider_name
        FROM provider_weekly_payroll_status
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


def get_available_payroll_weeks():
    """Get list of available payroll weeks from provider_weekly_payroll_status table"""
    conn = database.get_db_connection()
    try:
        query = """
        SELECT DISTINCT
            pay_week_number,
            pay_year,
            pay_week_start_date,
            pay_week_end_date
        FROM provider_weekly_payroll_status
        WHERE pay_week_start_date IS NOT NULL
        ORDER BY pay_year DESC, pay_week_number DESC
        LIMIT 52
        """
        rows = conn.execute(query).fetchall()

        weeks = []
        for row in rows:
            try:
                week_num = row[0]
                year = row[1]
                week_start = row[2]
                week_end = row[3]
                weeks.append(
                    {
                        "week_number": week_num,
                        "year": year,
                        "week_start_date": week_start,
                        "week_end_date": week_end,
                        "display": f"Week {week_num} {year}: {week_start} to {week_end}",
                    }
                )
            except (ValueError, IndexError):
                continue

        return weeks
    except Exception as e:
        st.error(f"Error getting available payroll weeks: {e}")
        return []
    finally:
        conn.close()


def get_payroll_data(pay_week_number=None, pay_year=None, payroll_status=None):
    """
    Get provider payroll data from workflow table.

    Args:
        pay_week_number: Optional filter by week number
        pay_year: Optional filter by year
        payroll_status: Optional filter by payroll status (Pending, Approved, Paid, Held)

    Returns:
        DataFrame with payroll records
    """
    conn = database.get_db_connection()
    try:
        query = """
        SELECT
            payroll_id,
            provider_id,
            provider_name,
            pay_week_start_date,
            pay_week_end_date,
            pay_week_number,
            pay_year,
            visit_type,
            task_count,
            total_minutes_of_service,
            hourly_rate,
            total_payroll_amount,
            payroll_status,
            is_approved,
            approved_date,
            approved_by,
            is_paid,
            paid_date,
            paid_by,
            payment_method,
            payment_reference,
            paid_by_zen_count,
            paid_by_zen_minutes,
            notes,
            created_date,
            updated_date
        FROM provider_weekly_payroll_status
        WHERE 1=1
        """

        params = []

        if pay_week_number:
            query += " AND pay_week_number = ?"
            params.append(pay_week_number)

        if pay_year:
            query += " AND pay_year = ?"
            params.append(pay_year)

        if payroll_status:
            query += " AND payroll_status = ?"
            params.append(payroll_status)

        query += " ORDER BY provider_name, visit_type"

        df = pd.read_sql_query(query, conn, params=params)
        return df

    except Exception as e:
        st.error(f"Error getting payroll data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


def get_payroll_summary(pay_week_number=None, pay_year=None):
    """Get summary statistics for payroll week"""
    conn = database.get_db_connection()
    try:
        query = """
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT provider_id) as unique_providers,
            SUM(task_count) as total_tasks,
            SUM(total_minutes_of_service) as total_minutes,
            SUM(total_payroll_amount) as total_payroll_amount,
            COUNT(CASE WHEN is_approved = TRUE THEN 1 END) as approved_count,
            COUNT(CASE WHEN is_paid = TRUE THEN 1 END) as paid_count,
            COUNT(CASE WHEN is_approved = FALSE THEN 1 END) as pending_count,
            SUM(paid_by_zen_count) as total_paid_by_zen_count,
            SUM(paid_by_zen_minutes) as total_paid_by_zen_minutes
        FROM provider_weekly_payroll_status
        WHERE 1=1
        """

        params = []
        if pay_week_number:
            query += " AND pay_week_number = ?"
            params.append(pay_week_number)

        if pay_year:
            query += " AND pay_year = ?"
            params.append(pay_year)

        result = conn.execute(query, params).fetchone()
        if result:
            return {
                "total_records": result[0] or 0,
                "unique_providers": result[1] or 0,
                "total_tasks": result[2] or 0,
                "total_minutes": result[3] or 0,
                "total_payroll_amount": result[4] or 0,
                "approved_count": result[5] or 0,
                "paid_count": result[6] or 0,
                "pending_count": result[7] or 0,
                "paid_by_zen_count": result[8] or 0,
                "paid_by_zen_minutes": result[9] or 0,
            }
        return None
    except Exception as e:
        st.error(f"Error getting summary: {e}")
        return None
    finally:
        conn.close()


def get_payroll_status_options():
    """Get available payroll status values"""
    return [
        "All",
        "Pending",
        "Approved",
        "Paid",
        "Held",
    ]


# def can_view_payroll(user_role_ids):
#     """Check if user can view payroll data (Harpreet/Admin role 34 or Justin)"""
#     # Role 34 = Admin (Harpreet), Justin is superuser
#     return 34 in user_role_ids


def can_edit_payroll(user_id, user_role_ids):
    """Check if user can edit payroll status (Justin only)"""
    # Only Justin can approve and process payments
    # Role 34 = Admin (Harpreet) can view but NOT edit
    # In production, would check specific user_id for Justin
    return user_id == 1  # Justin's user_id is 1 (superuser)


def display_weekly_provider_payroll_dashboard(user_id=None, user_role_ids=None):
    """Main provider payroll dashboard for Justin"""
    st.title("Weekly Provider Payroll Dashboard")
    st.markdown(
        """
    **Payroll Workflow Management** for provider compensation tracking.

    ⚠️ **CRITICAL INFORMATION:**
    - `paid_by_zen_count` and `paid_by_zen_minutes` show tasks where provider was ALREADY COMPENSATED
    - Use this to PREVENT DOUBLE-PAYMENT to providers
    - This is separate from billing workflow (Medicare reimbursement)
    """
    )

    # Check if user can view payroll
    # can_view = can_view_payroll(user_role_ids or [])
    can_edit = can_edit_payroll(user_id, user_role_ids or [])

    # if not can_view:
    #     st.error(
    #         "❌ You do not have permission to view payroll data. Only Harpreet (Admin) and Justin can access this dashboard."
    #     )
    #     return

    if not can_edit:
        st.info(
            "ℹ️ View Mode: You can view payroll data but cannot modify status. Only Justin can approve and process payments."
        )

    # Get available weeks
    weeks = get_available_payroll_weeks()

    if not weeks:
        st.info(
            "No provider payroll data available yet. Data will appear once payroll records are aggregated."
        )
        return

    # Filter controls
    # Row 1: [Select Monthly][Show All Weeks] + [Select Week]
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Select Monthly**")
        months = get_available_months()
        selected_month = st.selectbox(
            "Select Month",
            options=months,
            format_func=lambda x: x["display"],
            key="payroll_month",
        )
        show_all_weeks = st.checkbox(
            "Show All Weeks", value=False, key="payroll_show_all_weeks"
        )

    with col2:
        st.markdown("**Select Week**")
        if selected_month:
            # Filter weeks by selected month
            if selected_month["year_month"] == "all":
                filtered_weeks = weeks
            else:
                filtered_weeks = []
                for week in weeks:
                    # Extract year_month from week_start_date
                    if week.get("week_start_date"):
                        try:
                            from datetime import datetime
                            week_date = datetime.strptime(week["week_start_date"], '%Y-%m-%d')
                            week_year_month = week_date.strftime('%Y-%m')
                            if (str(week["year"]) == str(selected_month["year"]) and 
                                week_year_month == selected_month["year_month"]):
                                filtered_weeks.append(week)
                        except (ValueError, TypeError):
                            # Skip weeks with invalid dates
                            continue
            if filtered_weeks:
                selected_week = st.selectbox(
                    "Select Week",
                    options=filtered_weeks,
                    format_func=lambda x: x["display"],
                    key="payroll_week",
                )
            else:
                st.info("No weeks available for selected month")
                selected_week = None
        else:
            st.info("Select a month first")
            selected_week = None

    # Row 2: [Select Provider]
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Select Provider**")
        providers = get_available_providers()
        if providers:
            selected_provider = st.selectbox(
                "Select Provider",
                options=providers,
                format_func=lambda x: x["display"],
                key="payroll_provider",
            )
        else:
            st.info("No providers available")
            selected_provider = None

    with col2:
        st.markdown("")  # Empty space for alignment

    # Status filter (optional, keep for now)
    payroll_status_options = get_payroll_status_options()
    selected_status = st.selectbox(
        "Filter by Payroll Status",
        options=payroll_status_options,
        key="payroll_status",
    )

    # Main content - handle the filter logic
    if show_all_weeks:
        pay_week = None
        pay_year = None
    elif selected_week:
        pay_week = selected_week["week_number"]
        pay_year = selected_week["year"]
    else:
        pay_week = None
        pay_year = None

    status_filter = None if selected_status == "All" else selected_status

    # Get provider filter for data query
    provider_filter = None
    if selected_provider and selected_provider["provider_id"] is not None:
        provider_filter = selected_provider["provider_name"]

    # Get summary
    summary = get_payroll_summary(pay_week, pay_year)

    if summary:
        st.subheader(get_section_title("Payroll Summary"))

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                get_metric_label("Total Payroll Amount"),
                f"${summary['total_payroll_amount']:,.2f}",
            )

        with col2:
            st.metric(
                get_metric_label("Total Tasks"),
                f"{summary['total_tasks']:,.0f}",
            )

        with col3:
            approved_pct = (
                (summary["approved_count"] / summary["total_records"] * 100)
                if summary["total_records"] > 0
                else 0
            )
            st.metric(
                get_metric_label("Approved"),
                f"{summary['approved_count']:,.0f}",
                delta=f"{approved_pct:.1f}%",
            )

        with col4:
            st.metric(
                get_metric_label("Paid"),
                f"{summary['paid_count']:,.0f}",
            )

        with col5:
            st.metric(
                get_metric_label("Pending"),
                f"{summary['pending_count']:,.0f}",
            )

        # CRITICAL: paid_by_zen tracking
        st.subheader(
            get_section_title(
                "CRITICAL: Already Paid by ZEN (Prevent Double-Payment)"
            )
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Providers Already Compensated (Task Count)",
                f"{summary['paid_by_zen_count']:,.0f}",
                help="Number of tasks where provider was already paid by ZEN. DO NOT PAY AGAIN.",
            )

        with col2:
            st.metric(
                "Providers Already Compensated (Minutes)",
                f"{summary['paid_by_zen_minutes']:,.0f}",
                help="Total minutes for already-paid tasks. DO NOT REIMBURSE AGAIN.",
            )

        st.warning(
            f"⚠️ **ATTENTION:** {summary['paid_by_zen_count']} tasks ({summary['paid_by_zen_minutes']} minutes) "
            f"have already been paid to providers. These are included in payroll records but "
            f"SHOULD NOT be paid again. Verify amounts before processing payments."
        )

    # Get detailed data
    payroll_df = get_payroll_data(pay_week, pay_year, status_filter)

    if not payroll_df.empty:
        st.subheader(get_section_title("Payroll Details"))

        # Display options
        col1, col2, col3 = st.columns(3)

        with col1:
            view_mode = st.radio(
                "View Mode",
                options=[
                    "All Records",
                    "Pending Only",
                    "Approved Only",
                    "Paid Only",
                ],
                horizontal=True,
            )

        with col2:
            sort_by = st.selectbox(
                "Sort By",
                options=["Provider", "Week Start", "Status", "Amount"],
            )

        with col3:
            show_paid_by_zen_detail = st.checkbox(
                "Show paid_by_zen Detail",
                value=True,
                key="payroll_show_paid_by_zen_detail",
                help="Show tasks already paid by ZEN",
            )

        # Filter based on view mode
        display_df = payroll_df.copy()
        if view_mode == "Pending Only":
            display_df = display_df[display_df["is_approved"] == False]
        elif view_mode == "Approved Only":
            display_df = display_df[
                (display_df["is_approved"] == True)
                & (display_df["is_paid"] == False)
            ]
        elif view_mode == "Paid Only":
            display_df = display_df[display_df["is_paid"] == True]

        # Sort
        if sort_by == "Provider":
            display_df = display_df.sort_values("provider_name")
        elif sort_by == "Week Start":
            display_df = display_df.sort_values(
                "pay_week_start_date", ascending=False
            )
        elif sort_by == "Status":
            display_df = display_df.sort_values("payroll_status")
        elif sort_by == "Amount":
            display_df = display_df.sort_values(
                "total_payroll_amount", ascending=False
            )

        # Display columns
        if show_paid_by_zen_detail:
            display_cols = [
                "payroll_id",
                "provider_name",
                "visit_type",
                "pay_week_start_date",
                "task_count",
                "total_minutes_of_service",
                "paid_by_zen_count",
                "paid_by_zen_minutes",
                "total_payroll_amount",
                "payroll_status",
                "is_approved",
                "is_paid",
            ]
        else:
            display_cols = [
                "payroll_id",
                "provider_name",
                "visit_type",
                "pay_week_start_date",
                "task_count",
                "total_minutes_of_service",
                "total_payroll_amount",
                "payroll_status",
                "is_approved",
                "is_paid",
            ]

        available_cols = [col for col in display_cols if col in display_df.columns]

        # Display table
        st.dataframe(
            display_df[available_cols],
            use_container_width=True,
            hide_index=True,
            key="payroll_data",
        )

        # Workflow actions
        if can_edit and not display_df.empty:
            st.subheader(get_section_title("Payroll Actions"))

            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(
                    "**APPROVE PAYROLL** - Select payroll IDs (comma-separated):"
                )
                approve_ids_input = st.text_input(
                    "Payroll IDs to Approve",
                    placeholder="e.g., 1,5,10,23",
                    key="approve_ids",
                )

            with col2:
                st.empty()

            if approve_ids_input:
                try:
                    approve_ids = [
                        int(x.strip()) for x in approve_ids_input.split(",")
                    ]

                    valid_ids = set(display_df["payroll_id"].tolist())
                    invalid_ids = [id for id in approve_ids if id not in valid_ids]

                    if invalid_ids:
                        st.error(
                            f"Invalid payroll IDs: {invalid_ids}. Please check your input."
                        )
                    else:
                        selected_records = display_df[
                            display_df["payroll_id"].isin(approve_ids)
                        ]

                        # Check for paid_by_zen issues
                        has_paid_by_zen = (
                            selected_records["paid_by_zen_count"] > 0
                        ).any()
                        if has_paid_by_zen:
                            st.warning(
                                "⚠️ ALERT: Some selected records have paid_by_zen counts. "
                                "Verify these providers were not already paid before approving."
                            )

                        st.info(
                            f"Ready to approve {len(selected_records)} payroll record(s)"
                        )

                        st.dataframe(
                            selected_records[available_cols],
                            use_container_width=True,
                            hide_index=True,
                        )

                        if st.button("Approve Selected Payroll", type="primary"):
                            success, message, updated_count = (
                                database.approve_provider_payroll(
                                    approve_ids, user_id
                                )
                            )

                            if success:
                                st.success(message)
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(message)

                except ValueError:
                    st.error(
                        "Invalid input format. Please enter comma-separated numbers."
                    )

            # Payment processing section
            st.markdown("---")
            st.markdown(
                "**PROCESS PAYMENTS** - Select approved payroll IDs to mark as paid:"
            )
            pay_ids_input = st.text_input(
                "Payroll IDs to Mark as Paid",
                placeholder="e.g., 1,5,10,23",
                key="pay_ids",
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                payment_method = st.selectbox(
                    "Payment Method",
                    options=["ACH", "Check", "Direct Deposit", "Wire Transfer"],
                    key="payment_method",
                )

            with col2:
                payment_reference = st.text_input(
                    "Payment Reference",
                    placeholder="e.g., Check #, ACH ID",
                    key="payment_reference",
                )

            with col3:
                st.empty()

            if pay_ids_input:
                try:
                    pay_ids = [int(x.strip()) for x in pay_ids_input.split(",")]

                    valid_ids = set(display_df["payroll_id"].tolist())
                    invalid_ids = [id for id in pay_ids if id not in valid_ids]

                    if invalid_ids:
                        st.error(
                            f"Invalid payroll IDs: {invalid_ids}. Please check your input."
                        )
                    else:
                        pay_records = display_df[
                            display_df["payroll_id"].isin(pay_ids)
                        ]

                        # Verify all are approved
                        unapproved = (pay_records["is_approved"] == False).sum()
                        if unapproved > 0:
                            st.error(
                                f"⚠️ {unapproved} record(s) are not approved yet. Approve first before paying."
                            )
                        else:
                            st.info(
                                f"Ready to mark {len(pay_records)} payroll record(s) as paid"
                            )

                            payment_total = pay_records[
                                "total_payroll_amount"
                            ].sum()
                            st.metric(
                                "Total Payment Amount",
                                f"${payment_total:,.2f}",
                            )

                            st.dataframe(
                                pay_records[available_cols],
                                use_container_width=True,
                                hide_index=True,
                            )

                            if st.button("Mark Selected as Paid", type="primary"):
                                success, message, updated_count = (
                                    database.mark_provider_payroll_as_paid(
                                        pay_ids,
                                        user_id,
                                        payment_method=payment_method,
                                        payment_reference=payment_reference,
                                    )
                                )

                                if success:
                                    st.success(message)
                                    st.info(
                                        f"Payment Method: {payment_method}\nReference: {payment_reference}"
                                    )
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error(message)

                except ValueError:
                    st.error(
                        "Invalid input format. Please enter comma-separated numbers."
                    )

        # Export options
        st.subheader(get_section_title("Export Options"))

        col1, col2 = st.columns(2)

        with col1:
            csv_data = display_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Payroll Data (CSV)",
                data=csv_data,
                file_name=f"payroll_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

        with col2:
            # Export pending only
            pending_df = display_df[display_df["is_paid"] == False]
            if not pending_df.empty:
                csv_pending = pending_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Pending (CSV)",
                    data=csv_pending,
                    file_name=f"payroll_pending_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

    else:
        st.info("No payroll data available for selected filters")


if __name__ == "__main__":
    # For testing purposes
    display_weekly_provider_payroll_dashboard(
        user_id=1,
        user_role_ids=[1],  # Justin/Payroll manager
    )
