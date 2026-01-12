# Technical Debt: Duplicate `get_users_by_role` Functions

## Issue Summary

There are **3 functions** in `src/database.py` that perform similar user retrieval by role operations:

1. **Line 874**: `get_users_by_role(role_identifier)` - Returns `user_id, username, full_name, role_name`
2. **Line 2973**: `get_users_by_role_name(role_name)` - Returns `user_id, username, full_name` (only accepts role_name string)
3. **Line 3235**: `get_users_by_role(role_identifier)` - Returns `user_id, username, full_name` (missing role_name)

## Problem

- Two functions have the **exact same name** (`get_users_by_role`) at different locations
- Function 1 (line 874) includes `role_name` in the SELECT but **no code actually uses it**
- Function 2 (line 3235) is the one being used by all 22 callers across the codebase
- Function 3 (line 2973) is redundant since Function 2 already handles role_name strings

## Usage Analysis

### Call Patterns Found (22 total calls across 8 files)

#### 1. **admin_dashboard.py** (2 calls)
- Line 1656: `db.get_users_by_role(ROLE_CARE_PROVIDER)` - Uses role_id constant
- Line 1666: `db.get_users_by_role(36)` - Uses hardcoded role_id (36 = Care Coordinator)
- **Purpose**: Provider/coordinator reassignment dropdowns
- **Fields used**: `user_id`, `full_name`

#### 2. **onboarding_dashboard.py** (5 calls)
- Line 1192: `database.get_users_by_role("CP")` - Uses role abbreviation string
- Line 1214: `database.get_users_by_role("CP")` - Uses role abbreviation string
- Line 1224: `database.get_users_by_role("CC")` - Uses role abbreviation string
- Line 1280: `database.get_users_by_role("CP")` - Uses role abbreviation string
- Line 1290: `database.get_users_by_role("CC")` - Uses role abbreviation string
- **Purpose**: Initial TV provider/coordinator assignment
- **Fields used**: `full_name`, `username`

#### 3. **care_coordinator_dashboard_enhanced.py** (4 calls)
- Line 423: `database.get_users_by_role(36)` - Uses hardcoded role_id
- Line 561: `database.get_users_by_role(36)` - Uses hardcoded role_id
- Line 1215: `database.get_users_by_role(36)` - Uses hardcoded role_id
- Line 1240: `database.get_users_by_role(36)` - Uses hardcoded role_id
- **Purpose**: Coordinator filtering and assignment
- **Fields used**: `user_id`, `full_name`, `username`

#### 4. **care_provider_dashboard_enhanced.py** (3 calls)
- Line 573: `database.get_users_by_role(33)` - Uses hardcoded role_id (33 = Care Provider)
- Line 574: `database.get_users_by_role(36)` - Uses hardcoded role_id (36 = Care Coordinator)
- Line 1526: `database.get_users_by_role(36)` - Uses hardcoded role_id
- **Purpose**: Provider/coordinator filtering and assignment
- **Fields used**: `user_id`, `full_name`

#### 5. **coordinator_manager_dashboard.py** (2 calls)
- Line 122: `db.get_users_by_role(ROLE_CARE_COORDINATOR)` - Uses role_id constant
- Line 363: `db.get_users_by_role(ROLE_CARE_COORDINATOR)` - Uses role_id constant
- **Purpose**: Coordinator reassignment
- **Fields used**: `user_id`, `full_name`

#### 6. **lead_coordinator_dashboard.py** (1 call)
- Line 21: `get_users_by_role("Care Coordinator")` - Uses full role name string
- **Purpose**: Task assignment to coordinators
- **Fields used**: `username`

#### 7. **workflow_module.py** (1 call)
- Line 950: `get_users_by_role(36)` - Uses hardcoded role_id
- **Purpose**: Workflow assignment to coordinators
- **Fields used**: `user_id`, `full_name`, `username`

#### 8. **phone_review.py** (1 call)
- Line 14: `database.get_users_by_role(33)` - Uses hardcoded role_id (33 = Care Provider)
- **Purpose**: Provider selection for phone review
- **Fields used**: `user_id`, `full_name`, `username`

## Input Parameter Patterns

### Role ID (Integer)
- `33` = Care Provider
- `36` = Care Coordinator
- `ROLE_CARE_PROVIDER` (constant)
- `ROLE_CARE_COORDINATOR` (constant)

### Role Name (String)
- `"CP"` - Care Provider abbreviation
- `"CC"` - Care Coordinator abbreviation
- `"Care Coordinator"` - Full role name

## Return Column Requirements

### Most Common Pattern (19/22 calls)
- `user_id` - Required for assignments
- `full_name` - Required for display
- `username` - Sometimes used for display

### Rare Pattern (3/22 calls)
- `username` only (lead_coordinator_dashboard.py)

### Unused Pattern
- `role_name` - Included in Function 1 but never used by any caller

## Risk Assessment

### High Risk
- **Function name collision**: Two functions with same name at different locations
- **Ambiguity**: Which function is actually being called?
- **Maintenance burden**: Changes must be made in multiple places

### Medium Risk
- **Inconsistent input patterns**: Mix of role_id integers and role_name strings
- **Hardcoded values**: Magic numbers (33, 36) scattered throughout codebase
- **Unused code**: Function 1 includes `role_name` column that no one uses

### Low Risk
- **Current functionality works**: All 22 calls are functioning correctly
- **No breaking changes observed**: System is stable despite the duplication

## Proposed Resolution Plan

### Phase 1: Analysis & Planning
1. Confirm which function is actually being called by all 22 callers
2. Verify no code depends on the `role_name` column from Function 1
3. Document all role_id constants and role_name strings used

### Phase 2: Consolidation
1. Keep **Function 2 (line 3235)** as the single source of truth
2. Delete **Function 1 (line 874)** - unused `role_name` column
3. Delete **Function 3 (line 2973)** - redundant, Function 2 handles role_name strings
4. Update function docstring to document both input patterns (role_id int, role_name string)

### Phase 3: Standardization (Optional)
1. Replace hardcoded role_id values (33, 36) with constants
2. Standardize on role_id integers OR role_name strings (not both)
3. Create a role mapping dictionary for consistency

### Phase 4: Testing
1. Test all 8 dashboards to ensure user dropdowns work correctly
2. Verify provider/coordinator assignments still function
3. Test role-based filtering in all dashboards

## Questions for Review

1. **Should we standardize on role_id integers or role_name strings?**
   - Pros of role_id: Faster queries, type-safe
   - Pros of role_name: More readable, self-documenting

2. **Should we create role constants for all roles?**
   - Currently only `ROLE_CARE_PROVIDER` and `ROLE_CARE_COORDINATOR` exist
   - Could add `ROLE_ONBOARDING`, `ROLE_ADMIN`, etc.

3. **Should we keep the `role_name` column for future use?**
   - Currently unused but might be useful for debugging or display
   - Adds minimal overhead to query

## Dependencies

- Files affected: 8 dashboard files
- Functions to modify: 3 in `src/database.py`
- Total calls to update: 0 (if keeping Function 2)
- Testing required: All 8 dashboards

## Timeline Estimate

- Phase 1: 30 minutes (analysis)
- Phase 2: 15 minutes (consolidation)
- Phase 3: 1-2 hours (standardization - optional)
- Phase 4: 1 hour (testing)

**Total**: 2-4 hours (depending on Phase 3)

## Status

- [x] Issue identified
- [x] Usage analysis completed
- [x] Risk assessment documented
- [ ] Resolution plan approved
- [ ] Implementation started
- [ ] Testing completed
- [ ] Deployment verified
