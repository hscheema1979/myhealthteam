Workflow Screenshot Automation (Puppeteer)

Overview
Two modes are available:
- Admin Impersonation: Logs in as Admin and impersonates Coordinator/Provider (capture)
- Direct Login: Logs in as specific Coordinator and Provider accounts (capture:direct)

Prerequisites
- Node.js 18+
- The Streamlit app running at http://localhost:8501 (or set STREAMLIT_URL)

Setup
1) From d:\Git\myhealthteam2\Streamlit, install dependencies:
   npm install

2) .env (optional) next to package.json (d:\Git\myhealthteam2\Streamlit\scripts\automation\.env)
   For direct login:
   STREAMLIT_URL=http://localhost:8501
   COORDINATOR_EMAIL=hector@myhealthteam.org
   COORDINATOR_PASSWORD=pass123
   PROVIDER_EMAIL=angela@myhealthteam.org
   PROVIDER_PASSWORD=pass123
   HEADLESS=true

   For admin impersonation:
   ADMIN_EMAIL=admin@myhealthteam.org
   ADMIN_PASSWORD=YOUR_ADMIN_PASSWORD
   COORDINATOR_EMAIL=hector@myhealthteam.org
   PROVIDER_EMAIL=angela@myhealthteam.org

Usage
- Admin impersonation:
  npm run capture
- Direct login (recommended if admin is not required):
  npm run capture:direct

Outputs
- Screenshots: outputs/screenshots/<timestamp>/<role>/
- Reports: outputs/reports/workflow_screenshots_<timestamp>.md (impersonation) or workflow_screenshots_direct_<timestamp>.md (direct)

Selector notes
- Targets sidebar inputs by placeholders (Email, Password)
- Tabs clicked by visible text with role="tab"
- In direct mode, a logout is performed between roles

Troubleshooting
- If login fails, verify the credentials exist in the DB and the app’s auth columns match
- If tabs are missing for a role, the script skips them
- If the app is not reachable, start Streamlit:
  python -m streamlit run app.py

Windows Runner
- Admin mode: scripts/run_capture_workflows.ps1
- Direct mode: scripts/run_capture_workflows_direct.ps1