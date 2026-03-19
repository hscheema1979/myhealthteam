"""
E2E test: Verify ZMO search/clear buttons don't trigger session_state error.

Regression test for: "st.session_state.zmo_search_input cannot be modified
after the widget with key zmo_search_input is instantiated."
"""
import re
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8503"
USERNAME = "harpreet@myhealthteam.org"
PASSWORD = "pass123"


def login(page):
    """Log in to the Streamlit app."""
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    time.sleep(5)

    email_expander = page.get_by_text("Sign in with Email")
    email_expander.click()
    time.sleep(2)

    page.get_by_label("Email").fill(USERNAME)
    page.get_by_role("textbox", name="Password").fill(PASSWORD)
    page.get_by_role("button", name=re.compile(r"login|sign in|log in|submit", re.IGNORECASE)).click()
    time.sleep(8)
    print("  [OK] Logged in")


def navigate_to_zmo(page):
    """Navigate to ZMO tab."""
    zmo_tab = page.get_by_role("tab", name=re.compile(r"ZMO|Patient Management", re.IGNORECASE))
    if zmo_tab.count() > 0:
        zmo_tab.first.click()
        time.sleep(5)
        print("  [OK] ZMO tab opened")
        return True
    print("  [WARN] ZMO tab not found")
    return False


def check_no_error(page, context_msg):
    """Check page doesn't contain session_state error."""
    content = page.content()
    if "cannot be modified after the widget" in content:
        print(f"  [FAIL] {context_msg}: session_state error found!")
        page.screenshot(path=f"/tmp/test_zmo_error_{context_msg.replace(' ', '_')}.png")
        return False
    if "Error" in page.locator('[data-testid="stException"]').all_inner_texts() if page.locator('[data-testid="stException"]').count() > 0 else []:
        print(f"  [FAIL] {context_msg}: Streamlit exception found!")
        return False
    print(f"  [PASS] {context_msg}: no session_state error")
    return True


def test_search_and_clear(page):
    """Test: type in search, then click Clear search button."""
    print("\n=== TEST: Search + Clear Search ===")

    search_input = page.get_by_placeholder("Enter patient name, ID, or MRN...")
    if search_input.count() == 0:
        print("  [SKIP] Search input not found")
        return True

    search_input.first.fill("test")
    time.sleep(2)

    clear_btn = page.get_by_role("button", name="Clear search")
    if clear_btn.count() > 0:
        clear_btn.first.click()
        time.sleep(3)
        result = check_no_error(page, "clear_search")
        return result
    else:
        print("  [SKIP] Clear search button not found")
        return True


def test_clear_results(page):
    """Test: click Clear Results button."""
    print("\n=== TEST: Clear Results Button ===")

    clear_results_btn = page.get_by_role("button", name="Clear Results")
    if clear_results_btn.count() > 0:
        clear_results_btn.first.click()
        time.sleep(3)
        result = check_no_error(page, "clear_results")
        return result
    else:
        print("  [SKIP] Clear Results button not found")
        return True


def test_reset_columns(page):
    """Test: click Reset Columns button."""
    print("\n=== TEST: Reset Columns Button ===")

    reset_btn = page.get_by_role("button", name="Reset Columns")
    if reset_btn.count() > 0:
        reset_btn.first.click()
        time.sleep(3)
        result = check_no_error(page, "reset_columns")
        return result
    else:
        print("  [SKIP] Reset Columns button not found")
        return True


def run_tests():
    print("=" * 60)
    print("E2E Test: ZMO Search Session State Fix")
    print("=" * 60)

    all_pass = True

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            login(page)

            if not navigate_to_zmo(page):
                print("\n  [FAIL] Cannot reach ZMO tab - aborting")
                page.screenshot(path="/tmp/test_zmo_fix_no_tab.png")
                return False

            page.screenshot(path="/tmp/test_zmo_fix_initial.png")

            # Run each test
            all_pass = test_search_and_clear(page) and all_pass

            # Re-navigate to ZMO in case rerun changed the page
            navigate_to_zmo(page)
            all_pass = test_clear_results(page) and all_pass

            navigate_to_zmo(page)
            all_pass = test_reset_columns(page) and all_pass

            # Final summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            if all_pass:
                print("  STATUS: ALL PASS - No session_state errors")
            else:
                print("  STATUS: FAIL - session_state errors detected")

            page.screenshot(path="/tmp/test_zmo_fix_final.png")

        except Exception as e:
            print(f"\n  [ERROR] {e}")
            page.screenshot(path="/tmp/test_zmo_fix_error.png")
            raise
        finally:
            browser.close()

    return all_pass


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
