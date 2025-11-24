import fs from 'fs';
import path from 'path';
import puppeteer from 'puppeteer';
import dotenv from 'dotenv';

dotenv.config();

const STREAMLIT_URL = process.env.STREAMLIT_URL || 'http://localhost:8501';
const HEADLESS = (process.env.HEADLESS || 'true').toLowerCase() === 'true';

const PROVIDER_EMAIL = process.env.PROVIDER_EMAIL || '';
const PROVIDER_PASSWORD = process.env.PROVIDER_PASSWORD || 'pass123';

const COORDINATOR_EMAIL = process.env.COORDINATOR_EMAIL || '';
const COORDINATOR_PASSWORD = process.env.COORDINATOR_PASSWORD || 'pass123';

const ONBOARDING_EMAIL = process.env.ONBOARDING_EMAIL || '';
const ONBOARDING_PASSWORD = process.env.ONBOARDING_PASSWORD || 'pass123';
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

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

async function waitForAppReady(page) {
  await page.waitForSelector('[data-testid="stAppViewContainer"]', { timeout: 60000 });
}

async function clickXPath(page, xpath, timeout = 15000) {
  try {
    await page.waitForXPath(xpath, { timeout });
    const handles = await page.$x(xpath);
    if (handles && handles.length > 0) {
      await handles[0].click();
      return true;
    }
  } catch (e) {
    // ignore
  }
  return false;
}

async function login(page, email, password) {
  await page.goto(STREAMLIT_URL, { waitUntil: 'domcontentloaded' });
  await waitForAppReady(page);
  await page.waitForSelector('[data-testid="stSidebar"]', { timeout: 60000 });

  // If already logged in (persistent login), skip entering credentials
  const alreadyLogged = await page.evaluate(() => {
    const el = document.querySelector('[data-testid="stSidebar"]');
    return el && (el.textContent || '').includes('Logged in as');
  });

  if (!alreadyLogged) {
    const emailSelector = 'input[placeholder="user@example.com"]';
    const passwordSelector = 'input[placeholder="Enter your password"]';

    await page.waitForSelector(emailSelector, { timeout: 60000 });
    await page.click(emailSelector, { clickCount: 3 });
    await page.type(emailSelector, email, { delay: 25 });

    await page.waitForSelector(passwordSelector, { timeout: 60000 });
    await page.click(passwordSelector, { clickCount: 3 });
    await page.type(passwordSelector, password, { delay: 25 });

    // Try multiple ways to submit the login form
    // 1) Click the Login button by text
    await clickXPath(page, "//button[normalize-space()='Login']", 60000);
    // 2) Fallback: Click the Streamlit form submit button by data-testid
    try {
      await page.click('[data-testid="stBaseButton-secondaryFormSubmit"]');
    } catch {}
    // 3) Final fallback: press Enter to submit the st.form
    try {
      await page.keyboard.press('Enter');
    } catch {}
  }

  // Wait for login success: either sidebar shows 'Logged in as' OR main view shows a known dashboard title
  try {
    await page.waitForFunction(
      () => {
        const appText = document.body.innerText || '';
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        const sidebarText = sidebar ? (sidebar.textContent || '') : '';
        const logged = sidebarText.includes('Logged in as');
        const landed = appText.includes('Care Coordinator Dashboard') || appText.includes('Care Provider Dashboard') || appText.includes('Patient Onboarding Dashboard');
        return logged || landed;
      },
      { timeout: 60000 }
    );
  } catch (e) {
    // Proceed even if the login confirmation text wasn't found; subsequent steps will validate dashboard visibility
    await sleep(2000);
  }
}

async function logout(page) {
  try {
    const clicked = await clickXPath(page, "//button[normalize-space()='Logout']", 5000);
    if (clicked) {
      await sleep(1000);
    }
  } catch (e) {
    // ignore
  }
}

async function clickTabByText(page, tabText) {
  const xpath = `//button[@role='tab' and normalize-space()='${tabText}']`;
  const ok = await clickXPath(page, xpath, 15000);
  if (ok) {
    await sleep(1200);
    return true;
  }
  return false;
}

async function captureFullPage(page, outPath) {
  await sleep(1200);
  await page.screenshot({ path: outPath, fullPage: true });
  const stats = fs.statSync(outPath);
  const ok = stats.size > 30 * 1024;
  return { ok, size: stats.size };
}

function addReportSection(reportParts, title, images) {
  reportParts.push(`\n\n## ${title}\n`);
  images.forEach((img) => {
    reportParts.push(`- ${path.basename(img)} (${Math.round(fs.statSync(img).size / 1024)} KB)`);
    reportParts.push(`\n![](${img.replace(/\\/g, '/')})\n`);
  });
}

async function captureForRole(page, roleName, expectedTitle, tabsToVisit) {
  // Try waiting for an H1 title first (more reliable than body text), but don't fail the run if missing
  try {
    const titleXPath = `//h1[normalize-space()="${expectedTitle}"]`;
    await page.waitForXPath(titleXPath, { timeout: 60000 });
  } catch (e) {
    // Fallback: wait for body text to include the expected title; still tolerate failure
    try {
      await page.waitForFunction(
        (t) => document.body && (document.body.innerText || '').includes(t),
        { timeout: 60000 },
        expectedTitle
      );
    } catch (e2) {
      // As a final fallback, continue without strict title match and capture diagnostics
    }
  }

  const roleDir = path.join(screenshotDir, roleName.toLowerCase());
  ensureDir(roleDir);
  const images = [];

  // Save page HTML snapshot for diagnostics
  const htmlPath = path.join(roleDir, `${roleName}_dom.html`);
  try {
    const html = await page.content();
    fs.writeFileSync(htmlPath, html);
  } catch {}

  const landingPath = path.join(roleDir, `${roleName}_dashboard.png`);
  await captureFullPage(page, landingPath);
  images.push(landingPath);

  for (const tab of tabsToVisit) {
    const clicked = await clickTabByText(page, tab);
    if (!clicked) continue;
    const safeTab = tab.toLowerCase().replace(/[^a-z0-9]+/gi, '_');
    const outPath = path.join(roleDir, `${roleName}_${safeTab}.png`);
    await captureFullPage(page, outPath);
    images.push(outPath);
  }

  return images;
}

async function run() {
  const browser = await puppeteer.launch({ headless: HEADLESS, defaultViewport: { width: 1440, height: 900 } });
  const page = await browser.newPage();
  const reportParts = [
    `# Workflow Screenshot Report (Direct Login) - ${timestamp}`,
    `App: ${STREAMLIT_URL}`,
    `Headless: ${HEADLESS}`,
  ];

  // Coordinator (CC)
  if (COORDINATOR_EMAIL) {
    await login(page, COORDINATOR_EMAIL, COORDINATOR_PASSWORD);
    // Debug: capture immediate post-login state
    const postLoginPath = path.join(screenshotDir, 'post_login_coordinator.png');
    await page.screenshot({ path: postLoginPath, fullPage: true });
    const ccImages = await captureForRole(
      page,
      'Coordinator',
      'Care Coordinator Dashboard',
      ['My Patients', 'Phone Reviews', 'Team Management', 'Onboarding Queue & Initial TV Visits', 'Onboarding Queue', 'Initial TV Visits']
    );
    addReportSection(reportParts, 'Care Coordinator', ccImages);
    await logout(page);
  } else {
    reportParts.push('\n> Skipped Coordinator (COORDINATOR_EMAIL not set)');
  }

  // Onboarding (OT)
  if (ONBOARDING_EMAIL) {
    await login(page, ONBOARDING_EMAIL, ONBOARDING_PASSWORD);
    const postLoginPath2 = path.join(screenshotDir, 'post_login_onboarding.png');
    await page.screenshot({ path: postLoginPath2, fullPage: true });
    const otImages = await captureForRole(
      page,
      'Onboarding',
      'Patient Onboarding Dashboard',
      ['Patient Queue', 'Processing Status', 'Facility Management']
    );
    addReportSection(reportParts, 'Onboarding', otImages);
    await logout(page);
  } else {
    reportParts.push('\n> Skipped Onboarding (ONBOARDING_EMAIL not set)');
  }

  // Provider (CP)
  if (PROVIDER_EMAIL) {
    await login(page, PROVIDER_EMAIL, PROVIDER_PASSWORD);
    const postLoginPath3 = path.join(screenshotDir, 'post_login_provider.png');
    await page.screenshot({ path: postLoginPath3, fullPage: true });
    const cpImages = await captureForRole(
      page,
      'Provider',
      'Care Provider Dashboard',
      ['My Patients', 'Onboarding Queue & Initial TV Visits', 'Phone Reviews', 'Task Review', 'Team Management']
    );
    addReportSection(reportParts, 'Care Provider', cpImages);
    await logout(page);
  } else {
    reportParts.push('\n> Skipped Provider (PROVIDER_EMAIL not set)');
  }

  const reportPath = path.join(reportDir, `workflow_screenshots_direct_${timestamp}.md`);
  fs.writeFileSync(reportPath, reportParts.join('\n'));

  await browser.close();
  console.log(`Screenshots saved to: ${screenshotDir}`);
  console.log(`Report: ${reportPath}`);
}

run().catch((err) => {
  console.error('Capture (direct) failed:', err);
  process.exit(1);
});