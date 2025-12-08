# VPS Git Deployment Guide

## Purpose
This guide provides step-by-step instructions for deploying the latest code changes from GitHub to the production VPS using Antigravity.

---

## Prerequisites
- VPS workspace opened in Antigravity
- SSH access to production server
- Git repository: `https://github.com/creative-adventures/myhealthteam.git`
- Streamlit running as a service or in screen/tmux

---

## Deployment Steps

### Step 1: Check Current Status
```bash
# Navigate to application directory
cd /path/to/myhealthteam

# Check current branch and status
git branch
git status

# View current commit
git log -1 --oneline
```

### Step 2: Stop Streamlit Service
```bash
# If running as systemd service:
sudo systemctl stop streamlit

# If running in screen/tmux:
# - Attach to screen: screen -r streamlit
# - Press Ctrl+C to stop
# - Detach: Ctrl+A then D

# Verify it's stopped:
ps aux | grep streamlit
```

### Step 3: Backup Current Code (Optional but Recommended)
```bash
# Create timestamped backup
cd /path/to
cp -r myhealthteam myhealthteam_backup_$(date +%Y%m%d_%H%M%S)

# Or create a git stash if you have local changes:
cd myhealthteam
git stash save "Pre-deployment backup $(date +%Y%m%d_%H%M%S)"
```

### Step 4: Pull Latest Changes
```bash
cd /path/to/myhealthteam

# Fetch latest from GitHub
git fetch origin

# Pull and merge changes
git pull origin main

# If there are conflicts, resolve them and:
# git add <resolved-files>
# git commit -m "Merge: Resolved conflicts"
```

### Step 5: Verify Changes
```bash
# View what changed
git log --oneline -5

# Check for new files
git diff --name-status HEAD~1

# Verify Python files are present
ls -la src/dashboards/task_review_component.py
ls -la src/dashboards/coordinator_task_review_component.py
```

### Step 6: Update Dependencies (if needed)
```bash
# Check if requirements.txt changed
git diff HEAD~1 requirements.txt

# If changed, update dependencies:
pip install -r requirements.txt
```

### Step 7: Restart Streamlit
```bash
# If running as systemd service:
sudo systemctl start streamlit
sudo systemctl status streamlit

# If running in screen/tmux:
screen -S streamlit
streamlit run app.py --server.port 8501
# Press Ctrl+A then D to detach
```

### Step 8: Verify Deployment
```bash
# Check if Streamlit is running
ps aux | grep streamlit

# Check logs for errors
tail -f /path/to/streamlit.log
# OR
journalctl -u streamlit -f

# Test the application
curl http://localhost:8501
```

---

## Latest Deployment (2025-12-08)

### Commit: `6c29467`
**Title:** Fix: Task Review & Workflow System - Major Bug Fixes

**Changes:**
- Fixed task submission to use correct monthly tables
- Added inline editing to Daily view (providers & coordinators)
- Fixed workflow creation and completion bugs
- Removed billing codes from views
- Made database path cross-platform compatible
- Created new task review components

**Files Modified:**
- `src/database.py`
- `src/dashboards/task_review_component.py` (NEW)
- `src/dashboards/coordinator_task_review_component.py` (NEW)
- `src/dashboards/care_provider_dashboard_enhanced.py`
- `src/dashboards/care_coordinator_dashboard_enhanced.py`
- `src/dashboards/workflow_module.py`
- `src/utils/workflow_utils.py`
- `src/auth_module.py`

**Testing Checklist:**
- [ ] Provider can submit tasks
- [ ] Provider Task Review tab shows Daily/Weekly/Monthly views
- [ ] Provider can edit tasks in Daily view
- [ ] Coordinator can create workflows
- [ ] Coordinator Task Review tab works
- [ ] Coordinator can edit tasks in Daily view
- [ ] No billing codes visible to providers/coordinators

---

## Rollback Procedure

If issues occur after deployment:

```bash
# Option 1: Restore from backup
cd /path/to
sudo systemctl stop streamlit
rm -rf myhealthteam
mv myhealthteam_backup_YYYYMMDD_HHMMSS myhealthteam
cd myhealthteam
sudo systemctl start streamlit

# Option 2: Git revert to previous commit
cd /path/to/myhealthteam
git log --oneline -5  # Find previous commit hash
git reset --hard <previous-commit-hash>
sudo systemctl restart streamlit

# Option 3: Restore from git stash
git stash list
git stash apply stash@{0}
sudo systemctl restart streamlit
```

---

## Troubleshooting

### Streamlit won't start
```bash
# Check logs
journalctl -u streamlit -n 50

# Check Python errors
python app.py

# Verify database path
ls -la production.db
```

### Git pull conflicts
```bash
# See conflicting files
git status

# For each conflict:
# 1. Edit file and resolve markers (<<<<<<, ======, >>>>>>)
# 2. git add <file>
# 3. git commit

# Or accept remote changes:
git checkout --theirs <file>
git add <file>
```

### Database issues
```bash
# Check database exists
ls -la production.db

# Verify tables
sqlite3 production.db ".tables"

# Check recent tasks
sqlite3 production.db "SELECT * FROM provider_tasks_2025_12 LIMIT 5;"
```

---

## Antigravity Workflow

When using Antigravity to deploy:

1. **Open VPS workspace** in Antigravity
2. **Share this document** with Antigravity
3. **Request:** "Follow the VPS_GIT_DEPLOYMENT.md guide to deploy the latest changes"
4. **Antigravity will:**
   - Navigate to the application directory
   - Stop Streamlit
   - Pull latest changes from GitHub
   - Restart Streamlit
   - Verify deployment
5. **Review** the output and test the application

---

## Contact & Support

- **Repository:** https://github.com/creative-adventures/myhealthteam
- **Latest Commit:** Check `git log -1` on VPS
- **Deployment Date:** Record in `PROJECT_LIVING_DOCUMENT.md`
