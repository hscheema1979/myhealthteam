# Deploy Workflow current_step Fix to Production

## Summary
Fixed workflows not appearing in Results Reviewer dashboard because `current_step` column was not being incremented when steps were completed.

## Changes to Deploy

### 1. Code Update
File: `src/dashboards/workflow_module.py`

The `complete_workflow_step()` function now properly updates `current_step`.

### 2. Run Fix Script on VPS2

SSH to production server and run the fix script:

```bash
# SSH to VPS2
ssh server2

# Navigate to application directory
cd /opt/myhealthteam

# Run the fix script (dry run first)
python3 scripts/fix_workflow_current_step.py

# Apply fixes if dry run looks correct
python3 scripts/fix_workflow_current_step.py --apply

# Restart the service
sudo systemctl restart myhealthteam
```

### 3. Verification

After deployment, verify workflows appear in Results Reviewer dashboard:

```bash
# Check workflows at RR step
sqlite3 production.db "
SELECT instance_id, template_name, current_step, workflow_status
FROM workflow_instances
WHERE workflow_status = 'Active'
AND template_id IN (1,2,3,4,5,6)
AND (
    (template_id IN (1,2,3) AND current_step = 5) OR
    (template_id IN (4,5,6) AND current_step = 4)
)
"
```

Expected: Multiple LAB workflows at step 5 and IMAGING workflows at step 4.

## Files Modified
- `src/dashboards/workflow_module.py` - Updated `complete_workflow_step()` function
- `scripts/fix_workflow_current_step.py` - New utility script to fix existing workflows
