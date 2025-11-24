# Admin Dashboard Improvements Implementation Plan

## Goal: Merge improvements from broken file while keeping working billing report

## Implementation Steps:

### Step 1: Enhanced User Role Management
- [ ] Add role filtering: exclude 'Provider' and 'INITIAL_TV_PROVIDER' roles
- [ ] Add 'Edit Patient Info' permission system to User Management tab
- [ ] Improve column configuration and error handling

### Step 2: Enhanced Patient Info Tab  
- [ ] Add color-coded visit tracking (Red/Yellow/Green based on days since visit)
- [ ] Add enhanced search functionality 
- [ ] Add `editable_admin` checkbox mode
- [ ] Add `_apply_patient_info_edits_admin()` function for saving edits

### Step 3: Enhanced Coordinator Tasks
- [ ] Improve coordinator name resolution with `_safe_key()` function
- [ ] Add enhanced data processing and error handling
- [ ] Better filtering and display logic

### Step 4: Enhanced Provider Tasks
- [ ] Add enhanced provider visit breakdown
- [ ] Add provider statistics summary
- [ ] Better color coding and display logic

### Step 5: Staff Onboarding Improvements
- [ ] Add role descriptions
- [ ] Improve form validation
- [ ] Better error handling

### Step 6: Final Testing
- [ ] Verify all existing functionality still works
- [ ] Verify billing report continues to work
- [ ] Test new features incrementally

