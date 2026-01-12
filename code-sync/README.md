# MyHealthTeam - Code Sync & CI/CD

This folder contains automation scripts for deploying code changes to the VPS2 production server.

## Methods

### 1. GitHub Actions CI/CD (Automatic)

**Setup Required:**
1. Go to GitHub Repository Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `VPS_HOST`: Your VPS hostname (e.g., `192.168.1.100` or domain)
   - `VPS_USER`: SSH username (e.g., `root` or `myhealthteam`)
   - `SSH_PRIVATE_KEY`: Your private SSH key contents

**How it works:**
- Automatically triggers on push to `main` branch when Python files change
- Creates backup on server before deploying
- Syncs only code files (not database)
- Optionally restarts the Streamlit application

### 2. Manual Sync Script (Local)

Run from the project root:

```powershell
# Sync code only
.\code-sync\sync-to-production.ps1

# Sync code + database
.\code-sync\sync-to-production.ps1 -IncludeDb

# Dry run (preview changes)
.\code-sync\sync-to-production.ps1 -DryRun
```

### 3. Quick Database Sync Only

```powershell
# Just the database
scp production.db server2:/opt/myhealthteam/production.db
```

## What Gets Synced

**Code files:**
- `app.py` - Main entry point
- `requirements.txt` - Dependencies
- `src/*.py` - Core modules
- `src/dashboards/*.py` - Dashboard modules
- `src/utils/*.py` - Utilities
- `.streamlit/config.toml` - Streamlit config

**Database (optional):**
- `production.db` - SQLite database with patient data

## Server Structure

```
/opt/myhealthteam/
├── app.py
├── production.db
├── src/
├── .streamlit/
├── backups/
│   ├── src-backup-YYYYMMDD_HHMMSS/
│   └── production_backup_YYYYMMDD_HHMMSS.db
└── logs/
```

## Rollback

If something breaks after deployment:

```bash
# SSH to server
ssh server2

# Restore previous code
cp -r /opt/myhealthteam/backups/src-backup-YYYYMMDD_HHMMSS/* /opt/myhealthteam/

# Or restore database
cp /opt/myhealthteam/backups/production_backup_YYYYMMDD_HHMMSS.db /opt/myhealthteam/production.db

# Restart
pm2 restart myhealthteam
```

## Troubleshooting

**Permission denied:**
```bash
# Ensure SSH key is added to server's authorized_keys
ssh-copy-id server2
```

**PM2 not installed:**
```bash
ssh server2
npm install -g pm2
pm2 start "streamlit run app.py" --name myhealthteam
```

**Database locked:**
```bash
ssh server2
pm2 stop myhealthteam
# Copy database
cp production.db production.db.new
mv production.db.new production.db
pm2 restart myhealthteam
```
