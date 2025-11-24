import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';
import dotenv from 'dotenv';

dotenv.config();

const STREAMLIT_URL = process.env.STREAMLIT_URL || 'http://localhost:8501';
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || '';
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || '';
const COORDINATOR_EMAIL = process.env.COORDINATOR_EMAIL || '';
const PROVIDER_EMAIL = process.env.PROVIDER_EMAIL || '';
const HEADLESS = (process.env.HEADLESS || 'true').toLowerCase() === 'true';

const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
const baseOutputDir = path.resolve('outputs');
const screenshotDir = path.join(baseOutputDir, 'screenshots', timestamp);
const reportDir = path.join(baseOutputDir, 'reports');

function ensureDir(p) {
  if (!fs.existsSync(p)) {
    fs.mkdirSync(p, { recursive: true });
  }
}

ensureDir(screenshotDir);
ensureDir(reportDir);

async function waitForAppReady(page) {
  // Wait for Streamlit to finish its first render
  await page.waitForSelector('[data-testid="stAppViewContainer"]', { timeout: 30000 });
}

async function loginAsAdmin(page) {
  if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
    throw new Error('ADMIN_EMAIL and ADMIN_PASSWORD must be set (in .env or environment)');
  }
  await page.goto(STREAMLIT_URL, { waitUntil: 'domcontentloaded' });
  await waitForAppReady(page);

  // Sidebar login form
  await page.waitForSelector('[data-testid="stSidebar"]', { timeout: 20000 });

  // Fill email and password
  // Prefer placeholders to avoid brittle label XPath
  const emailSelector = 'input[placeholder="user@example.com"]';
  const passwordSelector = 'input[placeholder="Enter your password"]';

  await page.waitForSelector(emailSelector);
  await page.type(emailSelector, ADMIN_EMAIL, { delay: 30 });

  await page.waitForSelector(passwordSelector);
  await page.type(passwordSelector, ADMIN_PASSWORD, { delay: 30 });

  // Click Login button
  const loginBtnXpath = "//button[normalize-space()='Login']";
  const [loginBtn] = await page.$x(loginBtnXpath);
  if (!loginBtn) {
    throw new Error('Login button not found in sidebar');
  }
  await loginBtn.click();

  // Wait for rerender indicating login success: look for 'Logged in as:' or 'User Impersonation'
  await page.waitForFunction(
    () => {
      const sidebar = document.querySelector('[data-testid="stSidebar"]');
      if (!sidebar) return false;
      const text = sidebar.textContent || '';
      return text.includes('Logged in as') || text.includes('User Impersonation');
    },
    { timeout: 20000 }
  );
}

async function openImpersonationDropdown(page) {
  // Find the selectbox labeled 'Select User to Test:' and open its combobox
  const labelXpath = "//label[normalize-space()='Select User to Test:']";
  const [labelEl] = await page.$x(labelXpath);
  if (!labelEl) {
    throw new Error('Impersonation dropdown label not found. Are you logged in as an Admin?');
  }
  // The selectbox control is usually the next sibling with role=combobox
  const combobox = await labelEl.evaluateHandle((label) => {
    // Search nearby for a role=combobox
    const root = label.parentElement;
    return root.querySelector('[role="combobox"]') || document.querySelector('[role="combobox"]');
  });
  if (!combobox) {
    throw new Error('Impersonation combobox not found');
  }
  await combobox.asElement().click();
}

async function selectUserInDropdown(page, searchText) {
  // After opening the combobox, type to filter, then press Enter to select
  await page.keyboard.type(searchText, { delay: 25 });
  await page.waitForTimeout(500);
  await page.keyboard.press('Enter');
}

async function startImpersonating(page) {
  const startBtnXpath = "//button[normalize-space()='Start Impersonating']";
  const [startBtn] = await page.$x(startBtnXpath);
  if (!startBtn) {
    throw new Error('Start Impersonating button not found');
  }
  await startBtn.click();
  // Wait for rerun (dashboard content changes)
  await page.waitForFunction(
    () => document.body.innerText.includes('Dashboard') || document.body.innerText.includes('My Patients'),
    { timeout: 20000 }
  );
}

async function clickTabByText(page, tabText) {
  const xpath = `//button[@role='tab' and normalize-space()='${tabText}']`;
  const [tabBtn] = await page.$x(xpath);
  if (!tabBtn) return false;
  await tabBtn.click();
  await page.waitForTimeout(800);
  return true;
}

async function captureFullPage(page, outPath) {
  await page.waitForTimeout(1000);
  await page.screenshot({ path: outPath, fullPage: true });
  const stats = fs.statSync(outPath);
  const ok = stats.size > 30 * 1024; // 30KB minimum sanity check
  return { ok, size: stats.size };
}

function addReportSection(reportParts, title, images) {
  reportParts.push(`\n\n## ${title}\n`);
  images.forEach((img) => {
    reportParts.push(`- ${path.basename(img)}`);
    reportParts.push(`\n![](${img.replace(/\\/g, '/')})\n`);
  });
}

async function captureForRole(page, roleName, expectedTitle, tabsToVisit) {
  // Verify page shows expected dashboard title
  await page.waitForFunction(
    (t) => document.body.innerText.includes(t),
    { timeout: 15000 },
    expectedTitle
  );

  const roleDir = path.join(screenshotDir, roleName.toLowerCase());
  ensureDir(roleDir);

  const images = [];

  // Capture initial dashboard view
  const landingPath = path.join(roleDir, `${roleName}_dashboard.png`);
  const res0 = await captureFullPage(page, landingPath);
  images.push(landingPath);

  for (const tab of tabsToVisit) {
    const clicked = await clickTabByText(page, tab);
    if (!clicked) {
      // Skip if tab not present for this user
      continue;
    }
    const safeTab = tab.toLowerCase().replace(/[^a-z0-9]+/gi, '_');
    const outPath = path.join(roleDir, `${roleName}_${safeTab}.png`);
    const res = await captureFullPage(page, outPath);
    images.push(outPath);
  }

  return images;
}

async function run() {
  const browser = await puppeteer.launch({ headless: HEADLESS, defaultViewport: { width: 1440, height: 900 } });
  const page = await browser.newPage();

  // 1) Login as Admin
  await loginAsAdmin(page);

  // Report parts
  const reportParts = [
    `# Workflow Screenshot Report - ${timestamp}`,
    `App: ${STREAMLIT_URL}`,
    `Headless: ${HEADLESS}`,
  ];

  // 2) Coordinator capture
  if (COORDINATOR_EMAIL) {
    await openImpersonationDropdown(page);
    await selectUserInDropdown(page, COORDINATOR_EMAIL);
    await startImpersonating(page);

    const coordImages = await captureForRole(
      page,
      'Coordinator',
      'Care Coordinator Dashboard',
      ['My Patients', 'Phone Reviews', 'Team Management']
    );
    addReportSection(reportParts, 'Care Coordinator', coordImages);

    // Return to admin
    const stopBtnXpath = "//button[normalize-space()='⏹️ Stop Impersonating' or normalize-space()='Stop Impersonating']";
    const [stopBtn] = await page.$x(stopBtnXpath);
    if (stopBtn) {
      await stopBtn.click();
      await page.waitForTimeout(800);
    }
  } else {
    reportParts.push('\n> Skipped Coordinator (COORDINATOR_EMAIL not set)');
  }

  // 3) Provider capture
  if (PROVIDER_EMAIL) {
    await openImpersonationDropdown(page);
    await selectUserInDropdown(page, PROVIDER_EMAIL);
    await startImpersonating(page);

    const provImages = await captureForRole(
      page,
      'Provider',
      'Care Provider Dashboard',
      ['My Patients', 'Onboarding Queue & Initial TV Visits', 'Phone Reviews', 'Task Review', 'Team Management']
    );
    addReportSection(reportParts, 'Care Provider', provImages);

    // Return to admin
    const stopBtnXpath = "//button[normalize-space()='⏹️ Stop Impersonating' or normalize-space()='Stop Impersonating']";
    const [stopBtn] = await page.$x(stopBtnXpath);
    if (stopBtn) {
      await stopBtn.click();
      await page.waitForTimeout(800);
    }
  } else {
    reportParts.push('\n> Skipped Provider (PROVIDER_EMAIL not set)');
  }

  // Write report
  const reportPath = path.join(reportDir, `workflow_screenshots_${timestamp}.md`);
  fs.writeFileSync(reportPath, reportParts.join('\n'));

  await browser.close();

  console.log(`Screenshots saved to: ${screenshotDir}`);
  console.log(`Report: ${reportPath}`);
}

run().catch((err) => {
  console.error('Capture failed:', err);
  process.exit(1);
});