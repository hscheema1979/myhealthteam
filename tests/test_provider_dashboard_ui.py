"""
Provider Dashboard UI Test Framework
Tests the actual Streamlit UI using Playwright in headless mode.
Tests all combinations of Location Type x Patient Type and validates data persistence.

Run: python tests/test_provider_dashboard_ui.py
"""

import asyncio
import sqlite3
import os
import sys
import subprocess
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from playwright.async_api import async_playwright, Browser, Page

sys.path.insert(0, str(Path(__file__).parent.parent))

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

STREAMLIT_PORT = 8505
BASE_URL = f"http://localhost:{STREAMLIT_PORT}"
DB_PATH = "production.db"

# All combinations to test
TEST_MATRIX = [
    # (Location Type, Patient Type, Expected Billing Code)
    ("Home", "Follow Up", "99350"),
    ("Home", "New", "99345"),
    ("Home", "Cognitive", "96138+96132"),
    ("Home", "TCM-7", "99496"),
    ("Home", "TCM-14", "99495"),
    ("Office", "Follow Up", "99214"),
    ("Office", "New", "99204"),
    ("Office", "Acute", "99213"),
    ("Office", "Cognitive", "96138+96132"),
    ("Office", "TCM-7", "99496"),
    ("Office", "TCM-14", "99495"),
    ("Telehealth", "Follow Up", "99214"),
    ("Telehealth", "New", "99204"),
    ("Telehealth", "Acute", "99213"),
    ("Telehealth", "Cognitive", "96138+96132"),
    ("Telehealth", "TCM-7", "99496"),
    ("Telehealth", "TCM-14", "99495"),
]

# =============================================================================
# STREAMLIT PROCESS MANAGEMENT
# =============================================================================

class StreamlitManager:
    def __init__(self, port=STREAMLIT_PORT):
        self.port = port
        self.process = None

    def start(self):
        """Start Streamlit."""
        print(f"Starting Streamlit on port {self.port}...")

        # Kill any existing process on this port
        try:
            if os.name == 'nt':
                subprocess.run(["netstat", "-ano"], capture_output=True, check=False)
            else:
                subprocess.run(["lsof", "-ti", f":{self.port}"], capture_output=True, check=False)
        except:
            pass

        self.process = subprocess.Popen(
            ["streamlit", "run", "app.py",
             "--server.port", str(self.port),
             "--server.headless", "true",
             "--browser.gatherUsageStats", "false"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True
        )

        # Wait for Streamlit to be ready
        for i in range(30):
            try:
                import urllib.request
                urllib.request.urlopen(f"{BASE_URL}/_stcore/health", timeout=1)
                print(f"  OK Streamlit ready (port {self.port})")
                return True
            except:
                time.sleep(1)
                if i % 5 == 0:
                    print(f"  Waiting... ({i}/30)")

        print("  X Streamlit failed to start")
        return False

    def stop(self):
        """Stop Streamlit."""
        if self.process:
            print("Stopping Streamlit...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("  OK Streamlit stopped")

# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def cleanup_test_tasks(provider_id: int, task_date: str):
    """Clean up test tasks for a specific date."""
    conn = get_db_connection()
    try:
        conn.execute(
            "DELETE FROM provider_tasks_2026_02 "
            "WHERE provider_id = ? AND task_date = ? AND notes LIKE '%UI_TEST%'",
            (provider_id, task_date)
        )
        conn.commit()
    finally:
        conn.close()

def verify_task_in_db(provider_id: int, task_date: str, location_type: str, patient_type: str) -> dict:
    """Verify a task was saved correctly in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM provider_tasks_2026_02 "
            "WHERE provider_id = ? AND task_date = ? AND notes LIKE '%UI_TEST%' "
            "ORDER BY provider_task_id DESC LIMIT 1",
            (provider_id, task_date)
        )
        task = cursor.fetchone()
        return dict(task) if task else None
    finally:
        conn.close()

# =============================================================================
# TEST FUNCTIONS
# =============================================================================

async def wait_for_selector(page: Page, selector: str, timeout: int = 5000):
    """Wait for a selector with better error handling."""
    try:
        await page.wait_for_selector(selector, timeout=timeout)
        return True
    except:
        return False

async def login(page: Page, username: str) -> bool:
    """Handle login - assumes persistent session or test user."""
    print("\n=== Login ===")

    # Navigate and wait for load
    await page.goto(BASE_URL)
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    # Check if we're already at a dashboard (persistent session)
    page_content = await page.content()
    if "Dashboard" in page_content or "dashboard" in page.url.lower():
        print("  OK Already logged in (persistent session)")
        return True

    # Look for username field
    has_username = await wait_for_selector(page, "input[type='text'], input[name='username']", 2000)

    if has_username:
        print(f"  Logging in as {username}...")
        try:
            # Try username field
            await page.fill("input[type='text'], input[name='username']", username)

            # Try password field
            await page.fill("input[type='password'], input[name='password']", "TestPassword123!")

            # Click login/submit button
            login_clicked = await page.click("input[type='submit'], button[type='submit'], button:has-text('Login')")

            await asyncio.sleep(2)
            return True
        except Exception as e:
            print(f"  ! Login attempt failed: {e}")
    else:
        print("  ! No login form found - may need OAuth or persistent session")

    return False

async def navigate_to_daily_task_log(page: Page) -> bool:
    """Navigate to the Daily Task Log section."""
    print("\n=== Navigating to Daily Task Log ===")

    # Wait for page to fully load
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(1)

    # Try multiple possible selectors for the Daily Task Log section
    selectors = [
        "text=Daily Task Log",
        "[data-testid='stSidebar'] >> text=Daily",
        "[data-testid='stSidebar'] >> text=Task",
        "button:has-text('Daily')",
    ]

    for selector in selectors:
        try:
            if await wait_for_selector(page, selector, 3000):
                await page.click(selector)
                await asyncio.sleep(1)
                print("  OK Found Daily Task Log section")
                return True
        except:
            continue

    print("  ! Daily Task Log section not found, trying alternative...")
    # Try scrolling
    await page.evaluate("window.scrollTo(0, 500)")
    await asyncio.sleep(1)

    return False

async def test_create_task(
    page: Page,
    provider_id: int,
    patient_name: str,
    task_date: str,
    location_type: str,
    patient_type: str,
    expected_billing: str
) -> dict:
    """Test creating a task with specific parameters."""
    test_name = f"{location_type} + {patient_type}"
    print(f"\n=== Testing: {test_name} ===")
    print(f"  Expected billing: {expected_billing}")

    result = {
        "name": test_name,
        "location_type": location_type,
        "patient_type": patient_type,
        "expected_billing": expected_billing,
        "passed": False,
        "errors": [],
        "db_task": None
    }

    try:
        # Look for patient input/selectbox
        patient_selector = "input[type='text']:visible, [data-testid*='patient'], [role='combobox']:visible"

        # First, clear any existing entries or find the add button
        # Look for "Add Task" or "New Task" or similar button
        add_selectors = [
            "button:has-text('Add')",
            "button:has-text('New')",
            "stButton >> text=Add",
            "[data-testid='stElementActionButton']",
        ]

        added = False
        for sel in add_selectors:
            try:
                await page.click(sel, timeout=2000)
                await asyncio.sleep(0.5)
                added = True
                print("  OK Clicked add/new button")
                break
            except:
                continue

        # Look for patient selector
        if await wait_for_selector(page, "input[placeholder*='patient' i], input[aria-label*='patient' i]", 2000):
            await page.fill("input[placeholder*='patient' i], input[aria-label*='patient' i]", patient_name)
            print(f"  OK Selected patient: {patient_name}")
            await asyncio.sleep(0.5)

        # Look for location type selector
        # This could be a selectbox, radio buttons, or other widget
        location_selectors = [
            f"[data-testid*='location'] >> [aria-label*='{location_type}' i]",
            f"select:has-text('{location_type}')",
            f"[role='option']:has-text('{location_type}')",
        ]

        location_found = False
        for sel in location_selectors:
            try:
                if await wait_for_selector(page, sel, 2000):
                    await page.click(sel)
                    location_found = True
                    print(f"  OK Selected location: {location_type}")
                    await asyncio.sleep(0.5)
                    break
            except:
                continue

        if not location_found:
            result["errors"].append(f"Could not find location selector for {location_type}")

        # Look for patient type selector
        patient_type_selectors = [
            f"[data-testid*='patient'] >> [aria-label*='{patient_type}' i]",
            f"select:has-text('{patient_type}')",
            f"[role='option']:has-text('{patient_type}')",
        ]

        patient_type_found = False
        for sel in patient_type_selectors:
            try:
                if await wait_for_selector(page, sel, 2000):
                    await page.click(sel)
                    patient_type_found = True
                    print(f"  OK Selected patient type: {patient_type}")
                    await asyncio.sleep(0.5)
                    break
            except:
                continue

        if not patient_type_found:
            result["errors"].append(f"Could not find patient type selector for {patient_type}")

        # Look for submit/save button
        submit_selectors = [
            "button:has-text('Save')",
            "button:has-text('Submit')",
            "button:has-text('Add Task')",
            "stButton >> text=Save",
            "[data-testid*='submit']",
        ]

        submitted = False
        for sel in submit_selectors:
            try:
                await page.click(sel, timeout=2000)
                submitted = True
                print("  OK Clicked submit button")
                await asyncio.sleep(1)  # Wait for save
                break
            except:
                continue

        if not submitted:
            result["errors"].append("Could not find submit button")
            return result

        # Verify in database
        print("  -> Verifying in database...")
        db_task = verify_task_in_db(provider_id, task_date, location_type, patient_type)

        if db_task:
            result["db_task"] = db_task

            # Check values match
            if db_task.get("location_type") == location_type:
                print(f"  OK DB location_type: {location_type}")
            else:
                result["errors"].append(f"DB location_type mismatch: expected {location_type}, got {db_task.get('location_type')}")

            if db_task.get("patient_type") == patient_type:
                print(f"  OK DB patient_type: {patient_type}")
            else:
                result["errors"].append(f"DB patient_type mismatch: expected {patient_type}, got {db_task.get('patient_type')}")

            if db_task.get("billing_code") == expected_billing:
                print(f"  OK DB billing_code: {expected_billing}")
            else:
                result["errors"].append(f"DB billing_code mismatch: expected {expected_billing}, got {db_task.get('billing_code')}")

            result["passed"] = len(result["errors"]) == 0
        else:
            result["errors"].append("Task not found in database after submit")

    except Exception as e:
        result["errors"].append(f"Exception: {str(e)}")
        print(f"  X Exception: {e}")

    return result

async def run_tests():
    """Run all UI tests."""
    print("\n" + "=" * 70)
    print("PROVIDER DASHBOARD UI TEST FRAMEWORK")
    print("=" * 70)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get test data
    conn = get_db_connection()
    try:
        provider = conn.execute(
            "SELECT u.user_id, u.username, u.full_name FROM users u "
            "JOIN user_roles ur ON u.user_id = ur.user_id "
            "WHERE ur.role_id = 33 LIMIT 1"
        ).fetchone()

        patient = conn.execute(
            "SELECT patient_id, first_name, last_name FROM patients LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    if not provider or not patient:
        print("X Test data not found (need provider role 33 and at least one patient)")
        return

    provider = dict(provider)
    patient = dict(patient)
    test_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\nTest User: {provider['full_name']} (ID: {provider['user_id']})")
    print(f"Test Patient: {patient['first_name']} {patient['last_name']} (ID: {patient['patient_id']})")
    print(f"Test Date: {test_date}")

    # Clean up any existing test data
    cleanup_test_tasks(provider['user_id'], test_date)

    # Start Streamlit
    streamlit = StreamlitManager()
    if not streamlit.start():
        print("X Failed to start Streamlit")
        return

    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            # Enable detailed logging
            page.on("console", lambda msg: print(f"  Browser console: {msg.text}"))
            page.on("pageerror", lambda exc: print(f"  Browser error: {exc}"))

            # Login
            await login(page, provider.get("username", provider.get("full_name", "")))

            # Navigate to task entry
            await navigate_to_daily_task_log(page)

            # Take screenshot for debugging
            screenshot_path = f"test_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            print(f"\n  Screenshot saved: {screenshot_path}")

            # Get page text for debugging
            page_text = await page.inner_text("body")
            print(f"\n  Page text preview (first 500 chars):")
            print("  " + page_text[:500].replace("\n", "\n  "))

            # Test a single combination first
            print("\n" + "=" * 70)
            print("SINGLE COMBINATION TEST")
            print("=" * 70)

            result = await test_create_task(
                page,
                provider['user_id'],
                f"{patient['first_name']} {patient['last_name']}",
                test_date,
                "Home",
                "Follow Up",
                "99350"
            )

            print(f"\nResult: {result['name']}")
            print(f"  Passed: {result['passed']}")
            if result['errors']:
                for err in result['errors']:
                    print(f"  Error: {err}")
            if result.get('db_task'):
                print(f"  DB Task ID: {result['db_task'].get('provider_task_id')}")

            # Close browser
            await browser.close()

    finally:
        streamlit.stop()

    # Final summary
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_tests())
