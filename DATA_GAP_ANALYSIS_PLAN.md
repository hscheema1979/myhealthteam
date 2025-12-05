# Data Gap Analysis Plan

## Objective
Perform comprehensive gap analysis between old production data and new unified import staging data for November and December 2025.

## Tasks
- [ ] **Phase 1: Baseline Data Collection**
  - [ ] Analyze production.db for November/December 2025 coordinator tasks
  - [ ] Analyze production.db for November/December 2025 provider tasks
  - [ ] Document baseline counts and date ranges
  - [ ] Extract sample data for comparison

- [ ] **Phase 2: Current Staging Data Analysis**
  - [ ] Analyze sheets_data.db for November/December 2025 coordinator tasks
  - [ ] Analyze sheets_data.db for November/December 2025 provider tasks
  - [ ] Document current staging counts and date ranges
  - [ ] Extract sample data for comparison

- [ ] **Phase 3: Source CSV Analysis**
  - [ ] Analyze actual CSV files for November/December 2025 data
  - [ ] Document available dates and record counts
  - [ ] Compare source availability vs staged data

- [ ] **Phase 4: Gap Identification**
  - [ ] Identify missing dates in each dataset
  - [ ] Compare record counts by date/coordinator/provider
  - [ ] Identify data quality issues
  - [ ] Map data flow from CSV to staging to production

- [ ] **Phase 5: Sample Comparison**
  - [ ] Compare specific coordinator data: CSV vs staging vs production
  - [ ] Compare specific provider data: CSV vs staging vs production
  - [ ] Identify transformation issues
  - [ ] Document data integrity concerns

- [ ] **Phase 6: Final Report**
  - [ ] Generate comprehensive gap analysis report
  - [ ] Include specific examples and recommendations
  - [ ] Document data discrepancies and causes
  - [ ] Provide actionable remediation steps

## Focus Areas
- **November 2025**: Complete month analysis
- **December 2025**: Partial month analysis (through current date)
- **Coordinator Tasks**: CM ID mapping and task data
- **Provider Tasks**: Provider codes and service data
- **Patient Data**: Name/DOB matching across systems
