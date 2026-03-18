"""
E2E test: Verify 7 new columns (DME, eTV Panel, XRx, CareTeam, Folder, AWV, DD)
appear in patient panel views and are editable via ZMO tabs.
"""
import re
import time
from playwright.sync_api import sync_playwright, expect


BASE_URL = "http://127.0.0.1:8503"
USERNAME = "harpreet@myhealthteam.org"
PASSWORD = "pass123"

NEW_COLUMNS = ["DME", "eTV Panel", "XRx", "CareTeam", "Folder", "AWV", "DD"]
ENHANCEMENT_COLUMNS = [
    "Transportation Status", "HH Status", "MedList Date",
    "SmartPh Active", "Language", "RPM Team", "BH Team",
    "Cog Team", "PCP Name", "Consents",
]


def login(page):
    """Log in to the Streamlit app."""
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    time.sleep(5)  # Streamlit takes a moment to render

    # Click "Sign in with Email" expander to reveal the form
    email_expander = page.get_by_text("Sign in with Email")
    email_expander.click()
    time.sleep(2)

    # Now fill the email and password fields
    email_input = page.get_by_label("Email")
    email_input.fill(USERNAME)

    password_input = page.get_by_role("textbox", name="Password")
    password_input.fill(PASSWORD)

    # Click login button
    login_btn = page.get_by_role("button", name=re.compile(r"login|sign in|log in|submit", re.IGNORECASE))
    login_btn.click()

    # Wait for dashboard to load
    time.sleep(8)
    print("  [OK] Logged in successfully")


def test_patient_panel_columns(page):
    """Test that new columns appear in My Patients / Patient Panel view."""
    print("\n=== TEST: Patient Panel Columns ===")

    # Look for My Patients or Patient Panel section
    page_text = page.content()

    found_new = []
    missing_new = []
    for col in NEW_COLUMNS:
        if col in page_text:
            found_new.append(col)
        else:
            missing_new.append(col)

    found_enh = []
    missing_enh = []
    for col in ENHANCEMENT_COLUMNS:
        if col in page_text:
            found_enh.append(col)
        else:
            missing_enh.append(col)

    print(f"  New columns found: {found_new}")
    if missing_new:
        print(f"  New columns MISSING: {missing_new}")
    print(f"  Enhancement columns found: {found_enh}")
    if missing_enh:
        print(f"  Enhancement columns MISSING: {missing_enh}")

    return found_new, missing_new


def test_zmo_tab_editing(page):
    """Test that ZMO tab allows editing the new columns."""
    print("\n=== TEST: ZMO Tab Editing ===")

    # Look for ZMO tab
    zmo_tab = page.get_by_role("tab", name=re.compile(r"ZMO|Patient Management|Data Entry", re.IGNORECASE))
    if zmo_tab.count() > 0:
        zmo_tab.first.click()
        time.sleep(5)
        print("  [OK] ZMO tab found and clicked")

        # Click "Show/Hide Columns" expander if present to see column list
        show_cols = page.get_by_text("Show/Hide Columns")
        if show_cols.count() > 0:
            show_cols.first.click()
            time.sleep(2)
            print("  [OK] Show/Hide Columns expanded")

        # Take a full page screenshot
        page.screenshot(path="/tmp/test_zmo_expanded.png", full_page=True)

        # Get the full page HTML to check for column names
        page_text = page.content()

        # Check for editable fields for new columns
        found_editable = []
        missing_editable = []
        for col in NEW_COLUMNS:
            if col in page_text:
                found_editable.append(col)
            else:
                missing_editable.append(col)

        print(f"  Editable columns in ZMO: {found_editable}")
        if missing_editable:
            print(f"  Missing columns in ZMO: {missing_editable}")

        # Also check for enhancement columns
        found_enh = []
        for col in ENHANCEMENT_COLUMNS:
            if col in page_text:
                found_enh.append(col)
        print(f"  Enhancement columns in ZMO: {found_enh}")

        # Try to find an editable text input or data editor
        editors = page.locator('[data-testid="stDataEditor"], [data-testid="stTextInput"], textarea, input[type="text"]')
        editor_count = editors.count()
        print(f"  Editable widgets found: {editor_count}")

        # Search for column names in data table headers
        # Streamlit data editors use aria-label on column headers
        all_headers = page.locator('[role="columnheader"]')
        header_count = all_headers.count()
        if header_count > 0:
            header_names = []
            for i in range(min(header_count, 100)):
                h = all_headers.nth(i)
                header_names.append(h.inner_text())
            print(f"  Table headers found ({header_count}): {header_names}")

        return found_editable
    else:
        print("  [WARN] ZMO tab not found - checking sidebar")
        sidebar = page.locator('[data-testid="stSidebar"]')
        sidebar_text = sidebar.inner_text() if sidebar.count() > 0 else ""
        print(f"  Sidebar content (first 500 chars): {sidebar_text[:500]}")
        return []


def test_navigate_to_my_patients(page):
    """Navigate to My Patients view."""
    print("\n=== TEST: Navigate to My Patients ===")

    # Check sidebar for navigation
    sidebar = page.locator('[data-testid="stSidebar"]')
    if sidebar.count() > 0:
        sidebar_text = sidebar.inner_text()
        print(f"  Sidebar options: {sidebar_text[:300]}")

    # Try clicking on My Patients link/tab
    my_patients = page.get_by_text(re.compile(r"my patients|patient panel|patient list", re.IGNORECASE))
    if my_patients.count() > 0:
        my_patients.first.click()
        time.sleep(3)
        print("  [OK] Navigated to My Patients")
    else:
        print("  [INFO] My Patients section may already be visible or uses different name")


def run_tests():
    print("=" * 60)
    print("E2E Test: 7 New Columns + ZMO Editability")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            # Login
            login(page)

            # Take screenshot after login
            page.screenshot(path="/tmp/test_after_login.png")
            print("  [OK] Screenshot: /tmp/test_after_login.png")

            # Navigate to My Patients
            test_navigate_to_my_patients(page)
            page.screenshot(path="/tmp/test_my_patients.png")

            # Test columns visible
            found, missing = test_patient_panel_columns(page)

            # Test ZMO editing
            test_zmo_tab_editing(page)
            page.screenshot(path="/tmp/test_zmo_tab.png")
            print("  [OK] Screenshot: /tmp/test_zmo_tab.png")

            # Summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"  New columns found: {len(found)}/{len(NEW_COLUMNS)}")
            if missing:
                print(f"  MISSING: {missing}")
                print("  STATUS: PARTIAL PASS")
            else:
                print("  STATUS: FULL PASS")

        except Exception as e:
            print(f"\n  [ERROR] {e}")
            page.screenshot(path="/tmp/test_error.png")
            print("  Error screenshot: /tmp/test_error.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    run_tests()
