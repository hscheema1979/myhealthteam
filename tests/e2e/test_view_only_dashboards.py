"""
E2E test: Verify 4 view-only dashboards work correctly.
Tests login, correct title, correct columns, and read-only access.
"""
import re
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8503"

DASHBOARDS = [
    {
        "name": "Live Answering",
        "email": "answering@myhealthteam.org",
        "password": "pass123456",
        "title": "Live Answering Service",
        "expected_cols": ["Patient", "Assigned Coordinator", "Assigned Provider"],
    },
    {
        "name": "Special Teams",
        "email": "specialteams@myhealthteam.org",
        "password": "pass123456",
        "title": "Special Teams Dashboard",
        "expected_cols": ["Patient", "BH Team", "Cog Team", "RPM Team"],
    },
    {
        "name": "Clinical Pharmacy",
        "email": "pharmacy@myhealthteam.org",
        "password": "pass123456",
        "title": "Clinical Pharmacy",
        "expected_cols": ["Patient", "MedList Date"],
    },
    {
        "name": "SMS ChatBot",
        "email": "chatbot@myhealthteam.org",
        "password": "pass123456",
        "title": "SMS ChatBot",
        "expected_cols": ["Patient", "Med POC", "Appt POC"],
    },
]


def login(page, email, password):
    """Log in via email/password."""
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    time.sleep(5)

    email_expander = page.get_by_text("Sign in with Email")
    email_expander.click()
    time.sleep(2)

    page.get_by_label("Email").fill(email)
    page.get_by_role("textbox", name="Password").fill(password)
    page.get_by_role("button", name=re.compile(r"login|sign in|log in|submit", re.IGNORECASE)).click()
    time.sleep(8)


def logout(page):
    """Click logout button."""
    logout_btn = page.get_by_role("button", name=re.compile(r"logout", re.IGNORECASE))
    if logout_btn.count() > 0:
        logout_btn.first.click()
        time.sleep(3)


def test_dashboard(page, config):
    """Test a single view-only dashboard."""
    name = config["name"]
    print(f"\n{'='*50}")
    print(f"  TESTING: {name}")
    print(f"{'='*50}")

    # Login
    login(page, config["email"], config["password"])
    page.screenshot(path=f"/tmp/test_viewonly_{name.replace(' ','_').lower()}.png")

    content = page.content()

    # Check title
    if config["title"] in content:
        print(f"  [PASS] Title '{config['title']}' found")
    else:
        print(f"  [FAIL] Title '{config['title']}' NOT found")

    # Check expected columns
    found = []
    missing = []
    for col in config["expected_cols"]:
        if col in content:
            found.append(col)
        else:
            missing.append(col)

    print(f"  [INFO] Columns found: {found}")
    if missing:
        print(f"  [FAIL] Columns missing: {missing}")
    else:
        print(f"  [PASS] All columns present")

    # Check metrics (Active/Hospice counts)
    if "Active Patients" in content:
        print(f"  [PASS] Active Patients metric found")
    else:
        print(f"  [WARN] Active Patients metric not found")

    # Check search box
    search = page.locator('input[placeholder*="patient"]')
    if search.count() > 0:
        print(f"  [PASS] Search box found")
    else:
        print(f"  [WARN] Search box not found")

    # Check read-only (no edit buttons or data editors)
    edit_buttons = page.locator('button:has-text("Save"), button:has-text("Edit")')
    if edit_buttons.count() == 0:
        print(f"  [PASS] No edit/save buttons (read-only)")
    else:
        print(f"  [WARN] Edit/save buttons found — may not be read-only")

    result = "PASS" if not missing and config["title"] in content else "FAIL"
    print(f"  RESULT: {result}")

    # Logout for next test
    logout(page)
    return result


def run_tests():
    print("=" * 60)
    print("E2E Test: View-Only Dashboards")
    print("=" * 60)

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        for config in DASHBOARDS:
            try:
                results[config["name"]] = test_dashboard(page, config)
            except Exception as e:
                print(f"  [ERROR] {config['name']}: {e}")
                page.screenshot(path=f"/tmp/test_viewonly_error_{config['name'].replace(' ','_').lower()}.png")
                results[config["name"]] = "ERROR"
                # Navigate away to reset state
                page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
                time.sleep(3)

        browser.close()

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, result in results.items():
        print(f"  {name}: {result}")

    passed = sum(1 for r in results.values() if r == "PASS")
    print(f"\n  {passed}/{len(results)} dashboards passed")


if __name__ == "__main__":
    run_tests()
