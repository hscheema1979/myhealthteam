import streamlit as st

st.set_page_config(
    page_title="Zen Medicine", layout="wide", initial_sidebar_state="expanded"
)
import base64
import mimetypes
import os
import re
import sqlite3

import streamlit.components.v1 as components

from src import database
from src.auth_module import get_auth_manager, render_login_sidebar
from src.core_utils import get_user_role_ids
from src.dashboards import (
    admin_dashboard,
    care_coordinator_dashboard_enhanced,
    care_provider_dashboard_enhanced,
    coordinator_manager_dashboard,
    data_entry_dashboard,
    justin_simple_payment_tracker,
    monthly_coordinator_billing_dashboard,
    onboarding_dashboard,
    weekly_provider_billing_dashboard,
    weekly_provider_payroll_dashboard,
)
from src.database import (
    add_user,
    get_all_users,
    get_care_plan,
    get_coordinator_performance_metrics,
    get_db_connection,
    get_patient_details_by_id,
    get_provider_id_from_user_id,
    get_provider_performance_metrics,
    get_tasks_billing_codes,
    get_tasks_by_user,
    get_user_by_id,
    get_user_patient_assignments,
    get_user_roles,
    get_user_roles_by_user_id,
    get_users,
    get_users_by_role,
    update_care_plan,
)


# Helper: Render the HTML user guide inside the app
def render_help_panel():
    guide_path = os.path.join(
        "scripts", "automation", "outputs", "reports", "dashboard_user_guide.html"
    )
    try:
        with open(guide_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Replace file:// image sources with base64 data URIs to ensure they render inside Streamlit
        def replace_file_uri_with_data_uri(match):
            uri = match.group(1)
            # Normalize Windows file URI (file:///D:/path/to/file.png)
            local_path = uri
            if uri.lower().startswith("file:///"):
                local_path = uri[8:]  # strip 'file:///'
            elif uri.lower().startswith("file://"):
                local_path = uri[7:]  # strip 'file://'

            # Attempt to read and encode the image
            try:
                with open(local_path, "rb") as img_file:
                    img_bytes = img_file.read()
                    b64 = base64.b64encode(img_bytes).decode("ascii")
                    mime_type, _ = mimetypes.guess_type(local_path)
                    if not mime_type:
                        mime_type = "image/png"
                    return f'src="data:{mime_type};base64,{b64}"'
            except Exception:
                # If the image can't be loaded, keep the original src (it may show as broken)
                return f'src="{uri}"'

        # Regex to find src="file://..."
        html_content = re.sub(
            r'src\s*=\s*"(file:[^"]+)"', replace_file_uri_with_data_uri, html_content
        )

        components.html(html_content, height=900, scrolling=True)
    except Exception as e:
        st.error(f"Help guide not found at {guide_path}")
        st.info("Generate the guide via automation rerun or contact admin.")


# NEW: Render a gallery from Coordinator_dashboard_screenshots
def render_screenshot_gallery():
    dir_path = os.path.join("Coordinator_dashboard_screenshots")
    if not os.path.isdir(dir_path):
        st.info(f"Screenshots folder not found: {dir_path}")
        return
    try:
        files = sorted(
            [
                f
                for f in os.listdir(dir_path)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
        )
        if not files:
            st.info("No screenshots found in Coordinator_dashboard_screenshots.")
            return
        for fname in files:
            fpath = os.path.join(dir_path, fname)
            caption = (
                fname.replace("Screenshot Capture - ", "")
                .replace(".png", "")
                .replace(".jpg", "")
            )
            st.image(fpath, caption=caption, use_column_width=True)
    except Exception as ex:
        st.warning(f"Unable to render screenshots: {ex}")


# NEW: Role-specific screenshot gallery with section grouping
def render_role_screenshot_gallery(role: str):
    role = (role or "").lower()
    # Candidate folders by role
    candidates = []
    if role == "coordinator":
        candidates.append(os.path.join("Coordinator_dashboard_screenshots"))
    # Generic fallbacks for any role if present
    candidates.extend(
        [
            os.path.join("outputs", "screenshots", role),
            os.path.join("scripts", "automation", "outputs", "screenshots", role),
        ]
    )
    # Pick first folder that exists and has images
    chosen = None
    for d in candidates:
        if os.path.isdir(d):
            imgs = sorted(
                [
                    f
                    for f in os.listdir(d)
                    if f.lower().endswith((".png", ".jpg", ".jpeg"))
                ]
            )
            if imgs:
                chosen = (d, imgs)
                break
    if not chosen:
        st.info(
            f"No screenshots found for role='{role}'. Checked: {', '.join(candidates)}"
        )
        return
    dir_path, files = chosen

    # Basic grouping by filename tokens to explain sections
    groups = {
        "Patient Panel": ["panel", "patient panel"],
        "Workflow Management": ["workflow", "ongoing", "workflows"],
        "Detailed Workflow Steps": ["step", "workflow step", "task"],
        "Generic Task Form": ["form", "task form"],
    }

    matched = set()
    for section, tokens in groups.items():
        section_imgs = [f for f in files if any(tok in f.lower() for tok in tokens)]
        if section_imgs:
            st.subheader(section)
            for fname in section_imgs:
                matched.add(fname)
                fpath = os.path.join(dir_path, fname)
                caption = (
                    fname.replace("Screenshot Capture - ", "")
                    .replace(".png", "")
                    .replace(".jpg", "")
                )
                st.image(fpath, caption=caption, use_column_width=True)
    # Render any remaining images that didn't match a section
    remaining = [f for f in files if f not in matched]
    if remaining:
        st.subheader("Additional Screenshots")
        for fname in remaining:
            fpath = os.path.join(dir_path, fname)
            caption = (
                fname.replace("Screenshot Capture - ", "")
                .replace(".png", "")
                .replace(".jpg", "")
            )
            st.image(fpath, caption=caption, use_column_width=True)


# New: Detailed HTML Help overlay for Patient Panel (Coordinator)
def render_patient_panel_help_overlay():
    html = """
    <style>
      .help-container { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; color: #2e3e4e; }
      .help-note { background: #fff7e6; border: 1px solid #ffe8b3; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; }
      .grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
      @media (min-width: 900px) { .grid { grid-template-columns: 1fr 2fr; } }
      .section-card { background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; position: relative; }
      .section-title { margin: 0 0 8px 0; font-size: 18px; color: #334155; }
      .subtle { color: #6b7280; font-size: 13px; margin-bottom: 8px; }
      .mockbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 10px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; }
      .input { background: white; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; font-size: 13px; min-width: 160px; }
      .btn { background: #2563eb; color: white; border: none; border-radius: 6px; padding: 8px 12px; font-size: 13px; cursor: pointer; }
      .table { width: 100%; border-collapse: collapse; font-size: 13px; }
      .table th, .table td { border-bottom: 1px solid #e5e7eb; padding: 8px 10px; text-align: left; }
      .table th { background: #f1f5f9; font-weight: 600; color: #334155; }
      .actions { display: flex; gap: 8px; }
      .tag { display: inline-block; padding: 2px 8px; font-size: 12px; border-radius: 999px; background: #e2e8f0; color: #334155; }
      /* Tooltip */
      .hint-wrap { position: relative; display: inline-flex; align-items: center; }
      .hint { margin-left: 6px; display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; border-radius: 50%; background: #0ea5e9; color: white; font-size: 12px; cursor: help; }
      .hint-wrap .tooltip { position: absolute; left: 20px; top: -8px; z-index: 20; width: 320px; background: #0b1320; color: #e5e7eb; border: 1px solid #334155; padding: 10px 12px; border-radius: 8px; font-size: 12px; line-height: 1.35; box-shadow: 0 10px 30px rgba(2,6,23,0.4); display: none; }
      .hint-wrap:hover .tooltip { display: block; }
      .tooltip h4 { margin: 0 0 6px 0; font-size: 13px; color: #93c5fd; }
      .tooltip ul { margin: 0; padding-left: 18px; }
      .caption { color: #64748b; font-size: 12px; margin-top: 6px; }
    </style>
    <div class="help-container">
      <div class="help-note">This is a guidance-only HTML mock of the Coordinator Patient Panel. Use the tooltips (blue “i”) to learn what each control does. It does not show live data.</div>
      <div class="grid">
        <div class="section-card">
          <h3 class="section-title">Filter Bar</h3>
          <div class="subtle">Use filters to narrow the patient panel.</div>
          <div class="mockbar">
            <div class="hint-wrap">
              <input class="input" placeholder="Search by name or ID" />
              <div class="hint">i</div>
              <div class="tooltip">
                <h4>Search</h4>
                <ul>
                  <li>Type part of the patient name (Last, First) or numeric ID.</li>
                  <li>Press Enter to apply. The table filters as you type.</li>
                  <li>Clear the field to return to the full panel.</li>
                </ul>
              </div>
            </div>
            <div class="hint-wrap">
              <select class="input"><option>Assigned CM (any)</option><option>Soberanis, Jose</option><option>Diaz, Albert</option></select>
              <div class="hint">i</div>
              <div class="tooltip">
                <h4>Assigned Coordinator</h4>
                <ul>
                  <li>Filter by Care Coordinator assigned to the patient.</li>
                  <li>Useful for workload views per coordinator.</li>
                </ul>
              </div>
            </div>
            <div class="hint-wrap">
              <select class="input"><option>Status (any)</option><option>Active</option><option>Onboarding</option><option>Inactive</option></select>
              <div class="hint">i</div>
              <div class="tooltip">
                <h4>Status</h4>
                <ul>
                  <li>Show only Active, Onboarding, or Inactive patients.</li>
                  <li>Pairs with workflow stage to focus on work-in-progress.</li>
                </ul>
              </div>
            </div>
            <div class="hint-wrap">
              <select class="input"><option>Date Range (Last Visit)</option><option>Last 7 days</option><option>Last 30 days</option><option>Custom…</option></select>
              <div class="hint">i</div>
              <div class="tooltip">
                <h4>Date Range</h4>
                <ul>
                  <li>Constrain by last visit date or upcoming task due dates.</li>
                  <li>Use custom to set exact from/to dates.</li>
                </ul>
              </div>
            </div>
            <button class="btn">Apply Filters</button>
          </div>
          <div class="caption">Tip: Combine Assigned CM + Status to get an actionable view for one coordinator.</div>
        </div>

        <div class="section-card">
          <h3 class="section-title">Patient Panel Table</h3>
          <div class="subtle">Click a row to open patient details and workflows.</div>
          <table class="table">
            <thead>
              <tr>
                <th>Patient <span class="hint-wrap"><span class="hint">i</span><div class="tooltip"><h4>Patient</h4><ul><li>Name displayed as Last, First.</li><li>Click to open patient profile.</li></ul></div></span></th>
                <th>DOB <span class="hint-wrap"><span class="hint">i</span><div class="tooltip"><h4>Date of Birth</h4><ul><li>Used for validation and matching.</li></ul></div></span></th>
                <th>Last Visit <span class="hint-wrap"><span class="hint">i</span><div class="tooltip"><h4>Last Visit</h4><ul><li>Most recent recorded visit.</li><li>Red highlight if overdue check-ins.</li></ul></div></span></th>
                <th>Next Task <span class="hint-wrap"><span class="hint">i</span><div class="tooltip"><h4>Next Task</h4><ul><li>Primary action to perform next (phone review, schedule, etc.).</li><li>Click in details to update.</li></ul></div></span></th>
                <th>Workflow Stage <span class="hint-wrap"><span class="hint">i</span><div class="tooltip"><h4>Workflow Stage</h4><ul><li>Current step (Onboarding, Review, Follow-up).</li><li>Advances when tasks complete.</li></ul></div></span></th>
                <th>Priority <span class="hint-wrap"><span class="hint">i</span><div class="tooltip"><h4>Priority</h4><ul><li>Urgency indicator (High/Med/Low).</li><li>Often derived from risk or provider notes.</li></ul></div></span></th>
                <th>Assigned CM <span class="hint-wrap"><span class="hint">i</span><div class="tooltip"><h4>Assigned Care Coordinator</h4><ul><li>Person responsible for this patient.</li><li>Editable in details or assignment tools.</li></ul></div></span></th>
                <th>Actions <span class="hint-wrap"><span class="hint">i</span><div class="tooltip"><h4>Row Actions</h4><ul><li>Open Profile: view full details.</li><li>Start Workflow: begin a standardized process.</li><li>Assign CM: reassign coordinator.</li></ul></div></span></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><a href="#">Diaz, Albert</a></td>
                <td>01/01/1980</td>
                <td><span class="tag">2025-11-05</span></td>
                <td>Phone Review</td>
                <td>Review</td>
                <td><span class="tag">High</span></td>
                <td>Soberanis, Jose</td>
                <td class="actions">
                  <button class="btn" style="background:#334155">Open Profile</button>
                  <button class="btn" style="background:#22c55e">Start Workflow</button>
                  <button class="btn" style="background:#f59e0b">Assign CM</button>
                </td>
              </tr>
              <tr>
                <td><a href="#">Medez, Dianela</a></td>
                <td>02/02/1985</td>
                <td><span class="tag">2025-10-28</span></td>
                <td>Schedule Follow-up</td>
                <td>Onboarding</td>
                <td><span class="tag">Medium</span></td>
                <td>Diaz, Albert</td>
                <td class="actions">
                  <button class="btn" style="background:#334155">Open Profile</button>
                  <button class="btn" style="background:#22c55e">Start Workflow</button>
                  <button class="btn" style="background:#f59e0b">Assign CM</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="caption">Hover each header’s blue “i” to see what it means and how to use it.</div>
        </div>

        <div class="section-card">
          <h3 class="section-title">Workflow & Task Details</h3>
          <div class="subtle">When you open a patient, use the forms to advance the workflow.</div>
          <div class="mockbar" style="flex-direction: column; align-items: flex-start;">
            <div class="hint-wrap" style="width:100%">
              <label class="subtle">Generic Task Form — Required Fields</label>
              <div class="hint">i</div>
              <div class="tooltip">
                <h4>Task Form</h4>
                <ul>
                  <li>Task Type: choose the action (Phone Review, Follow-up, Scheduling).</li>
                  <li>Notes: capture details, decisions, and outcomes.</li>
                  <li>Due Date: sets the next task reminder.</li>
                  <li>Status: update to Completed or In Progress when appropriate.</li>
                </ul>
              </div>
            </div>
            <div style="display:flex; gap:8px; width:100%">
              <select class="input" style="flex:1"><option>Task Type</option><option>Phone Review</option><option>Follow-up</option><option>Scheduling</option></select>
              <input class="input" type="date" style="flex:1" />
              <select class="input" style="flex:1"><option>Status</option><option>In Progress</option><option>Completed</option></select>
            </div>
            <textarea class="input" rows="4" style="width:100%" placeholder="Notes (required)"></textarea>
            <div style="display:flex; gap:8px">
              <button class="btn">Save Task</button>
              <button class="btn" style="background:#334155">Cancel</button>
            </div>
          </div>
          <div class="caption">Saving a task may advance the Workflow Stage based on your Task Type and Status.</div>
        </div>
      </div>
    </div>
    """
    components.html(html, height=900, scrolling=True)
    return


# Helper: navigate to Help within the same tab (avoid new sessions)
def go_help(role: str | None = None, section: str | None = None):
    import streamlit as st

    st.query_params["page"] = "help"
    if role:
        st.query_params["role"] = role
    else:
        st.query_params.pop("role", None)
    if section:
        st.query_params["section"] = section
    else:
        st.query_params.pop("section", None)
    st.rerun()


def main():
    # Set sidebar title
    st.sidebar.title("Zen Medicine")

    # Route: dedicated Help pages via query params
    try:
        # Streamlit >=1.32: st.query_params, older: experimental_get_query_params
        # Prefer st.query_params (experimental_get_query_params deprecated after 2024-04-11)
        params = st.query_params if hasattr(st, "query_params") else {}
        page = (params.get("page", [""])[0] or "").lower()
        role = (params.get("role", [""])[0] or "").lower()
        section = (params.get("section", [""])[0] or "").lower()
    except Exception:
        page = role = section = ""

    if page == "help":
        st.title("Help & User Guide")
        if role:
            # Dedicated markdown-based help pages, default to index
            render_help_markdown(role, section or "index")
            return
        else:
            # Fallback to general help panel if no role specified
            render_help_panel()
            return

    # Initialize authentication manager
    auth_manager = get_auth_manager()

    # Render login sidebar (includes impersonation controls)
    render_login_sidebar(auth_manager)

    st.sidebar.markdown("---")

    # Show Help panel if requested (inline mode)
    if st.session_state.get("show_help"):
        st.markdown("### User Guide (Inline)")
        render_help_panel()
        st.button(
            "Close Help",
            key="close_help",
            on_click=lambda: st.session_state.update({"show_help": False}),
        )
        st.markdown("---")

    # Display Current User Info (when authenticated)
    if auth_manager.is_authenticated():
        st.sidebar.markdown("### Current User")

        # Get user details from the authenticated user
        users = database.get_users()
        if users:
            authenticated_email = auth_manager.get_current_user()["email"]
            current_user = next(
                (user for user in users if user["email"] == authenticated_email), None
            )

            if current_user:
                # Display current user info (read-only)
                st.sidebar.info(
                    f"**{current_user['full_name']}** ({current_user['username']})"
                )

                # Set the user session state automatically based on authenticated user
                if (
                    "user_id" not in st.session_state
                    or st.session_state["user_id"] != current_user["user_id"]
                ):
                    st.session_state["user_id"] = current_user["user_id"]
                    st.session_state["user_full_name"] = current_user["full_name"]
                    # Get all role IDs for the user
                    user_role_ids = get_user_role_ids(current_user["user_id"])
                    st.session_state["user_role_ids"] = user_role_ids

                # Role Switching Feature for users with multiple dashboard roles
                user_role_ids = st.session_state["user_role_ids"]
                dashboard_roles = [
                    33,
                    34,
                    36,
                    35,
                    39,
                    37,
                    38,
                    40,
                ]  # All dashboard-capable roles
                available_dashboard_roles = [
                    role_id for role_id in user_role_ids if role_id in dashboard_roles
                ]

                if len(available_dashboard_roles) > 1:
                    st.sidebar.markdown("---")
                    st.sidebar.markdown("### 🔄 Role Switcher")

                    # Role mapping for display
                    role_names = {
                        33: "Provider View",
                        34: "Admin View",
                        36: "Coordinator View",
                        35: "Onboarding View",
                        39: "Data Entry View",
                        37: "Lead Coordinator View",
                        38: "Care Provider Manager View",
                        40: "Coordinator Manager (Enhanced) View",
                    }

                    # Get current view preference from session state
                    if "preferred_dashboard_role" not in st.session_state:
                        st.session_state["preferred_dashboard_role"] = (
                            auth_manager.get_primary_dashboard_role()
                        )

                    current_view = st.session_state["preferred_dashboard_role"]

                    # Show current view
                    st.sidebar.caption(
                        f"Current View: **{role_names.get(current_view, f'Role {current_view}')}**"
                    )

                    # Create options for role switcher
                    role_options = [
                        (role_id, role_names.get(role_id, f"Role {role_id}"))
                        for role_id in available_dashboard_roles
                    ]
                    role_options.sort(key=lambda x: x[0])  # Sort by role ID

                    # Role switcher dropdown with on_change callback
                    def on_role_change():
                        new_role = st.session_state.role_switcher
                        if new_role != st.session_state.get("preferred_dashboard_role"):
                            st.session_state["preferred_dashboard_role"] = new_role

                    current_index = next(
                        (i for i, (rid, _) in enumerate(role_options) if rid == current_view),
                        0,
                    )

                    st.sidebar.selectbox(
                        "Switch to View:",
                        options=[role_id for role_id, name in role_options],
                        format_func=lambda x: role_names.get(x, f"Role {x}"),
                        key="role_switcher",
                        index=current_index,
                        on_change=on_role_change,
                    )

    # Display dashboard based on user and their roles
    if auth_manager.is_authenticated():
        user_id = auth_manager.get_user_id()
        user_role_ids = auth_manager.get_user_roles()

        # Check for preferred role (for users with multiple roles)
        preferred_role = st.session_state.get("preferred_dashboard_role")

        # Get dashboard role to use (preferred role if set, otherwise primary role)
        dashboard_role = (
            preferred_role
            if preferred_role
            else auth_manager.get_primary_dashboard_role()
        )

        if dashboard_role:
            # Route to appropriate dashboard based on dashboard role
            if dashboard_role == 33:  # Provider
                care_provider_dashboard_enhanced.show(user_id, user_role_ids)
            elif dashboard_role == 36:  # Coordinator
                care_coordinator_dashboard_enhanced.show(user_id, user_role_ids)
            elif dashboard_role == 34:  # Admin
                admin_dashboard.show()
            elif dashboard_role == 35:  # Onboarding
                onboarding_dashboard.show()
            elif dashboard_role == 39:  # Data Entry
                data_entry_dashboard.show()
            elif (
                dashboard_role == 37
            ):  # Lead Coordinator (LC) - same as coordinator but with lead privileges
                care_coordinator_dashboard_enhanced.show(user_id, user_role_ids)
            elif (
                dashboard_role == 38
            ):  # Care Provider Manager (CPM) - same as provider but with manager access
                care_provider_dashboard_enhanced.show(user_id, user_role_ids)
            elif (
                dashboard_role == 40
            ):  # Coordinator Manager (CM) - gets coordinator dashboard with workflow reassignment tab
                care_coordinator_dashboard_enhanced.show(user_id, user_role_ids)
            else:
                st.error(f"Unrecognized dashboard role: {dashboard_role}")
                st.info("Please contact your administrator.")
        else:
            st.error(f"User has no recognized dashboard role. Roles: {user_role_ids}")
            st.info("Please contact your administrator.")
    else:
        # Simple landing page for users not logged in
        st.markdown("# Zen Medicine")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(
                """
            <div style="text-align: center; padding: 40px; margin-top: 60px;">
                <h2 style="color: #495057; margin-bottom: 20px;">Please Login to Continue</h2>
                <p style="font-size: 16px; color: #6c757d;">
                    Use the login form in the sidebar to access your dashboard.
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # Sidebar help navigation removed — help is embedded within each dashboard
    # st.sidebar elements removed per request


# Initialize the database


def init_database():
    """Initialize the database with required tables and data."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if database is already initialized
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        if cursor.fetchone():
            return

        # Initialize database schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_roles (
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (role_id) REFERENCES roles (role_id)
            )
        """)

        # Insert default roles
        roles = [
            ("Admin", "System Administrator"),
            ("Provider", "Healthcare Provider"),
            ("Care Coordinator", "Care Coordinator"),
            ("Onboarding", "Onboarding Staff"),
            ("Data Entry", "Data Entry Staff"),
        ]
        cursor.executemany(
            "INSERT INTO roles (role_name, description) VALUES (?, ?)", roles
        )

        # Insert default users
        users = [
            ("admin_user", "admin@example.com", "Admin User", "admin123"),
            ("provider1", "provider1@example.com", "Dr. John Smith", "provider123"),
            (
                "coordinator1",
                "coordinator1@example.com",
                "Sarah Johnson",
                "coordinator123",
            ),
            ("onboarding1", "onboarding1@example.com", "Mike Davis", "onboarding123"),
            ("dataentry1", "dataentry1@example.com", "Lisa Wilson", "dataentry123"),
        ]
        cursor.executemany(
            "INSERT INTO users (username, email, full_name, password_hash) VALUES (?, ?, ?, ?)",
            users,
        )

        # Assign roles to users
        user_roles = [
            (1, 1),  # admin_user -> Admin
            (2, 2),  # provider1 -> Provider
            (3, 3),  # coordinator1 -> Care Coordinator
            (4, 4),  # onboarding1 -> Onboarding
            (5, 5),  # dataentry1 -> Data Entry
        ]
        cursor.executemany(
            "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", user_roles
        )

        conn.commit()
        conn.close()

        print("Database initialized successfully!")

    except Exception as e:
        print(f"Error initializing database: {e}")


# NEW: Markdown-based Help renderer for role/section pages
# UPDATED: Markdown-based Help renderer with Index and basic search
def render_help_markdown(role: str, section: str):
    role = (role or "").lower()
    section = (section or "").lower() or "workflow_guide"
    base_dir = os.path.join("docs", "help")
    role_dir = os.path.join(base_dir, role)

    # Optional: basic search across this role's markdown files
    search_query = st.text_input("Search help (this role only):", value="")
    if search_query:
        hits = []
        try:
            for fname in os.listdir(role_dir):
                if not fname.lower().endswith(".md"):
                    continue
                fpath = os.path.join(role_dir, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    txt = f.read()
                if search_query.lower() in txt.lower():
                    sec = fname[:-3]
                    hits.append(sec)
        except Exception as e:
            st.warning(f"Search skipped: {e}")
        if hits:
            st.markdown("### Search Results")
            for s in hits:
                st.markdown(
                    f"- [{s.replace('_',' ').title()}](/?page=help&role={role}&section={s})"
                )
        else:
            st.info("No matches found in this role.")

    # Index view: list available sections
    if section in ("index", "toc"):
        st.markdown(f"## {role.title()} Help — Index")
        if os.path.isdir(role_dir):
            files = [f[:-3] for f in os.listdir(role_dir) if f.lower().endswith(".md")]
            if files:
                for s in sorted(files):
                    st.markdown(
                        f"- [{s.replace('_',' ').title()}](/?page=help&role={role}&section={s})"
                    )
            else:
                st.markdown(
                    "No sections found yet. Please add markdown files under " + role_dir
                )
        return

    md_path = os.path.join(role_dir, f"{section}.md")
    if os.path.isfile(md_path):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                content = f.read()
            st.markdown(content)
            # Footer nav
            st.markdown(
                f"\n---\nReturn to [Index](/?page=help&role={role}&section=index)"
            )
        except Exception as e:
            st.error(f"Unable to load help content: {e}")
    else:
        st.info(
            f"Help not yet authored for role='{role}', section='{section}'. Expected at {md_path}."
        )
        # List available sections for this role
        if os.path.isdir(role_dir):
            files = [
                f.replace(".md", "")
                for f in os.listdir(role_dir)
                if f.lower().endswith(".md")
            ]
            if files:
                st.markdown("### Available Sections")
                for s in sorted(files):
                    st.markdown(
                        f"- [{s.replace('_',' ').title()}](/?page=help&role={role}&section={s})"
                    )
            else:
                st.markdown(
                    "No sections found yet. Please add markdown files under " + role_dir
                )
    return


# Help elements (actual UI, not screenshots)
def render_provider_help_elements():
    import streamlit as st

    st.header("Provider Help")
    st.markdown(
        "Use these tabs to work your panel: My Patients, Phone Reviews, Task Review. The help below explains each section and the color meanings."
    )

    st.subheader("Color legend (status/priority)")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            '<div style="background:#dc3545;padding:10px;border-radius:6px;color:white;text-align:center;">Overdue</div>',
            unsafe_allow_html=True,
        )
        st.caption("Red = past due")
    with col2:
        st.markdown(
            '<div style="background:#fd7e14;padding:10px;border-radius:6px;color:white;text-align:center;">Due Soon</div>',
            unsafe_allow_html=True,
        )
        st.caption("Orange = due in next few days")
    with col3:
        st.markdown(
            '<div style="background:#198754;padding:10px;border-radius:6px;color:white;text-align:center;">Completed</div>',
            unsafe_allow_html=True,
        )
        st.caption("Green = completed or resolved")
    with col4:
        st.markdown(
            '<div style="background:#0d6efd;padding:10px;border-radius:6px;color:white;text-align:center;">Assigned</div>',
            unsafe_allow_html=True,
        )
        st.caption("Blue = assigned to you/team")
    with col5:
        st.markdown(
            '<div style="background:#6c757d;padding:10px;border-radius:6px;color:white;text-align:center;">On Hold</div>',
            unsafe_allow_html=True,
        )
        st.caption("Gray = waiting or inactive")

    st.subheader("My Patients")
    st.markdown(
        "Manage your assigned patients. Sort by Priority or Next Task, open patient detail to document notes and advance the workflow stage."
    )
    import pandas as pd

    sample_patients = pd.DataFrame(
        [
            {
                "Patient": "Jane Doe",
                "Priority": "High",
                "Status": "Overdue",
                "Workflow Stage": "Follow-up",
                "Next Task": "Phone Review",
                "Due Date": "2025-11-20",
            },
            {
                "Patient": "Mark Lee",
                "Priority": "Medium",
                "Status": "Due Soon",
                "Workflow Stage": "Assessment",
                "Next Task": "Lab Review",
                "Due Date": "2025-11-22",
            },
            {
                "Patient": "Ava Chen",
                "Priority": "Low",
                "Status": "Assigned",
                "Workflow Stage": "Maintenance",
                "Next Task": "Chart Update",
                "Due Date": "2025-11-28",
            },
        ]
    )
    st.dataframe(sample_patients, use_container_width=True)

    st.subheader("Phone Reviews")
    st.markdown(
        "Work the call queue. Filter by due date (e.g., Today), click a call to document outcome, schedule the next follow-up."
    )

    st.subheader("Task Review")
    st.markdown(
        "Review tasks assigned to you. Filter by status and type; complete or reassign as needed."
    )

    st.info(
        "If any color/label differs from your actual app semantics, tell me the exact mapping and I’ll align the legend and highlights immediately."
    )


def render_coordinator_help_elements():
    import streamlit as st

    st.header("Coordinator Help")
    st.markdown(
        "Two main work areas: My Patients and Phone Reviews. Team Management is available for LC/CM roles."
    )

    st.subheader("Color legend (status/priority)")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            '<div style="background:#dc3545;padding:10px;border-radius:6px;color:white;text-align:center;">Escalation/Overdue</div>',
            unsafe_allow_html=True,
        )
        st.caption("Red = urgent or overdue")
    with col2:
        st.markdown(
            '<div style="background:#fd7e14;padding:10px;border-radius:6px;color:white;text-align:center;">Due Soon</div>',
            unsafe_allow_html=True,
        )
        st.caption("Orange = due shortly")
    with col3:
        st.markdown(
            '<div style="background:#198754;padding:10px;border-radius:6px;color:white;text-align:center;">Completed</div>',
            unsafe_allow_html=True,
        )
        st.caption("Green = completed or resolved")
    with col4:
        st.markdown(
            '<div style="background:#0d6efd;padding:10px;border-radius:6px;color:white;text-align:center;">Assigned</div>',
            unsafe_allow_html=True,
        )
        st.caption("Blue = assigned to coordinator/team")
    with col5:
        st.markdown(
            '<div style="background:#6c757d;padding:10px;border-radius:6px;color:white;text-align:center;">On Hold</div>',
            unsafe_allow_html=True,
        )
        st.caption("Gray = waiting or inactive")

    st.subheader("My Patients")
    st.markdown(
        "Triage and coordinate follow-ups. Sort by priority, open patient details, record outcomes, and update next task."
    )

    st.subheader("Phone Reviews")
    st.markdown(
        "Batch process call reviews due today or high priority. Document outcomes and schedule next steps."
    )

    st.subheader("Team Management (LC/CM)")
    st.markdown(
        "Balance workloads, reassign patients, and review coordinator/task metrics."
    )

    st.info(
        "Provide your exact color semantics or edge cases (e.g., 'attention' vs 'overdue') and I’ll update the legend and badges accordingly."
    )


if __name__ == "__main__":
    # Initialize database on first run
    init_database()
    main()
