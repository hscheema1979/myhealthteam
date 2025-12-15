This updated plan provides the granular detail you requested, outlining each dashboard table, its data needs, the current script support, and the specific gaps/actions required. This comprehensive approach will ensure all dashboards receive accurate, updated data from new imports.

Do you agree with this detailed and comprehensive action plan now? If so, please instruct me to **"toggle to Act mode"** so I can begin executing these precise, targeted corrections, starting with the updates to `PROJECT_LIVING_DOCUMENT.md` and then proceeding through Phase 1, Item 1 (Investigate & Document Base Tables) and Item 2 (Standardize Patient ID Normalization).
| `hire_date` | `users.hire_date` | `source_users.hire_date` | N/A (Internal) | User data entry/lookup |
| `patient_id` | `patient_assignments.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `provider_id` | `patient_assignments.provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `coordinator_id` | `patient_assignments.coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `action_type` | `audit_log.action_type` | N/A | N/A | Internal system logging |
| `table_name` | `audit_log.table_name` | N/A | N/A | Internal system logging |
| `record_id` | `audit_log.record_id` | N/A | N/A | Internal system logging |
| `old_value` | `audit_log.old_value` | N/A | N/A | Internal system logging |
| `new_value` | `audit_log.new_value` | N/A | N/A | Internal system logging |
| `user_id` | `audit_log.user_id` | N/A | N/A | Internal system logging |
| `timestamp` | `audit_log.timestamp` | N/A | N/A | Internal system logging |
| `description` | `audit_log.description` | N/A | N/A | Internal system logging |
| `coordinator_id` | `coordinator_tasks_YYYY_MM.coordinator_id` | `source_coordinator_tasks_history.staff_code` | `cmlog.csv` | Mapped via `user_code_map` from `Staff` |
| `patient_id` | `coordinator_tasks_YYYY_MM.patient_id` | `source_coordinator_tasks_history.patient_name_raw` | `cmlog.csv` | Patient ID normalization from `Pt Name` |
| `task_date` | `coordinator_tasks_YYYY_MM.task_date` | `source_coordinator_tasks_history.activity_date` | `cmlog.csv` | Date parsing from `Date Only` (MM/DD/YY, MM/DD/YYYY to YYYY-MM-DD) |
| `duration_minutes` | `coordinator_tasks_YYYY_MM.duration_minutes` | `source_coordinator_tasks_history.minutes_raw` | `cmlog.csv` | Numeric conversion from `Mins B` |
| `task_type` | `coordinator_tasks_YYYY_MM.task_type` | `source_coordinator_tasks_history.task_type` | `cmlog.csv` | Direct mapping from `Type`, cleaned |
| `notes` | `coordinator_tasks_YYYY_MM.notes` | `source_coordinator_tasks_history.notes` | `cmlog.csv` | Direct mapping from `Notes`, cleaned |
| `source_system` | `coordinator_tasks_YYYY_MM.source_system` | N/A | N/A | Derived (e.g., 'cmlog') |
| `imported_at` | `coordinator_tasks_YYYY_MM.imported_at` | N/A | N/A | System timestamp |
| `patient_id` | `patients.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `patients.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `patients.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `patients.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `status` | `patients.status` | `SOURCE_PATIENT_DATA.Pt Status` | `ZMO_Main.csv` | Direct mapping from `Pt Status`, default 'Active' if null |
| `last_visit_date` | `patients.last_visit_date` | N/A | `cmlog.csv`, `psl.csv`, `rvz.csv` | Aggregated from latest `activity_date` in tasks |
| `service_type` | `patients.service_type` | N/A | `psl.csv`, `rvz.csv` | Derived from `Service` in provider tasks |
| `er_count_1yr` | `patients.er_count_1yr` | N/A | N/A | To be derived from task data / other sources (currently NULL) |
| `hospitalization_count_1yr` | `patients.hospitalization_count_1yr` | N/A | N/A | To be derived from task data / other sources (currently NULL) |
| `subjective_risk_level` | `patients.subjective_risk_level` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `mental_health_concerns` | `patients.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `active_specialists` | `patients.active_specialists` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `code_status` | `patients.code_status` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `cognitive_function` | `patients.cognitive_function` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `functional_status` | `patients.functional_status` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `goals_of_care` | `patients.goals_of_care` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `goc_value` | `patients.goc_value` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `notes` | `patients.notes` | `SOURCE_PATIENT_DATA.Notes` | `ZMO_Main.csv` | Concatenation of various note fields |
| `patient_id` | `patient_panel.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `patient_panel.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `patient_panel.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `patient_panel.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `status` | `patient_panel.status` | `SOURCE_PATIENT_DATA.Pt Status` | `ZMO_Main.csv` | Direct mapping from `Pt Status`, default 'Active' if null |
| `facility` | `patient_panel.facility` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Direct mapping from `Fac` (if exists), lookup in `facilities` table |
| `last_visit_date` | `patient_panel.last_visit_date` | N/A | `cmlog.csv`, `psl.csv`, `rvz.csv` | Aggregated from latest `activity_date` in tasks |
| `last_visit_service_type` | `patient_panel.last_visit_service_type` | N/A | `psl.csv`, `rvz.csv` | Derived from `Service` in provider tasks |
| `assigned_coordinator_id` | `patient_panel.assigned_coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `provider_id` | `patient_panel.provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `goc_value` | `patient_panel.goc_value` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `code_status` | `patient_panel.code_status` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `cognitive_function` | `patient_panel.cognitive_function` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `functional_status` | `patient_panel.functional_status` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `subjective_risk_level` | `patient_panel.subjective_risk_level` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `er_count_1yr` | `patient_panel.er_count_1yr` | N/A | N/A | To be derived from task data / other sources (currently NULL) |
| `hospitalization_count_1yr` | `patient_panel.hospitalization_count_1yr` | N/A | N/A | To be derived from task data / other sources (currently NULL) |
| `mental_health_concerns` | `patient_panel.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `goals_of_care` | `patient_panel.goals_of_care` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `active_specialists` | `patient_panel.active_specialists` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `provider_task_id` | `provider_tasks_YYYY_MM.provider_task_id` | N/A | N/A | Auto-generated/Sequence ID |
| `provider_id` | `provider_tasks_YYYY_MM.provider_id` | `SOURCE_PROVIDER_TASKS_HISTORY.provider_code` | `psl.csv`, `rvz.csv` | Mapped via `user_code_map` from `Prov` |
| `patient_id` | `provider_tasks_YYYY_MM.patient_id` | `SOURCE_PROVIDER_TASKS_HISTORY.patient_name_raw` | `psl.csv`, `rvz.csv` | Patient ID normalization from `Patient Last, First DOB` |
| `task_date` | `provider_tasks_YYYY_MM.task_date` | `SOURCE_PROVIDER_TASKS_HISTORY.activity_date` | `psl.csv`, `rvz.csv` | Date parsing from `DOS` (MM/DD/YY, MM/DD/YYYY to YYYY-MM-DD) |
| `task_description` | `provider_tasks_YYYY_MM.task_description` | `SOURCE_PROVIDER_TASKS_HISTORY.service` | `psl.csv`, `rvz.csv` | Direct mapping from `Service`, cleaned |
| `minutes_of_service` | `provider_tasks_YYYY_MM.minutes_of_service` | `SOURCE_PROVIDER_TASKS_HISTORY.minutes_raw` | `psl.csv`, `rvz.csv` | Numeric conversion from `Minutes` (e.g., "60-69" to 69) |
| `billing_code` | `provider_tasks_YYYY_MM.billing_code` | `SOURCE_PROVIDER_TASKS_HISTORY.billing_code` | `psl.csv`, `rvz.csv` | Direct mapping from `Coding`, validated |
| `billing_code_description` | `provider_tasks_YYYY_MM.billing_code_description` | `task_billing_codes.description` | N/A (Lookup) | Lookup from `task_billing_codes` table |
| `status` | `provider_tasks_YYYY_MM.status` | N/A | N/A | Derived from internal logic/workflow |
| `notes` | `provider_tasks_YYYY_MM.notes` | `SOURCE_PROVIDER_TASKS_HISTORY.Notes` | `psl.csv`, `rvz.csv` | Direct mapping from `Notes` |
| `billing_code` | `patient_monthly_billing_YYYY_MM.billing_code` | `provider_tasks_YYYY_MM.billing_code` | `psl.csv`, `rvz.csv` | Aggregation of billing codes from provider tasks |
| `billing_code_description` | `patient_monthly_billing_YYYY_MM.billing_code_description` | `task_billing_codes.description` | N/A (Lookup) | Lookup from `task_billing_codes` table |
| `patient_id` | `patient_monthly_billing_YYYY_MM.patient_id` | `provider_tasks_YYYY_MM.patient_id` | `psl.csv`, `rvz.csv` | Direct mapping/aggregation from provider tasks |
| `total_minutes` | `patient_monthly_billing_YYYY_MM.total_minutes` | `provider_tasks_YYYY_MM.minutes_of_service` | `psl.csv`, `rvz.csv` | Sum aggregation of `minutes_of_service` |
| `billing_status` | `patient_monthly_billing_YYYY_MM.billing_status` | N/A | N/A | Derived from internal logic/workflow |
| `created_date` | `patient_monthly_billing_YYYY_MM.created_date` | N/A | N/A | System timestamp |
| `billing_status_id` | `provider_task_billing_status.billing_status_id` | N/A | N/A | Auto-generated/Sequence ID |
| `provider_task_id` | `provider_task_billing_status.provider_task_id` | `provider_tasks_YYYY_MM.provider_task_id` | N/A | Direct mapping |
| `provider_id` | `provider_task_billing_status.provider_id` | `provider_tasks_YYYY_MM.provider_id` | `psl.csv`, `rvz.csv` | Direct mapping |
| `provider_name` | `provider_task_billing_status.provider_name` | `users.full_name` (lookup via `provider_id`) | N/A (Lookup) | Lookup from `users` table |
| `patient_name` | `provider_task_billing_status.patient_name` | `patients.first_name`, `patients.last_name` | `ZMO_Main.csv` | Lookup from `patients` table |
| `task_date` | `provider_task_billing_status.task_date` | `provider_tasks_YYYY_MM.task_date` | `psl.csv`, `rvz.csv` | Direct mapping |
| `billing_week` | `provider_task_billing_status.billing_week` | N/A | N/A | Derived from `task_date` (week number) |
| `week_start_date` | `provider_task_billing_status.week_start_date` | N/A | N/A | Derived from `task_date` (week start) |
| `week_end_date` | `provider_task_billing_status.week_end_date` | N/A | N/A | Derived from `task_date` (week end) |
| `task_description` | `provider_task_billing_status.task_description` | `provider_tasks_YYYY_MM.task_description` | `psl.csv`, `rvz.csv` | Direct mapping |
| `minutes_of_service` | `provider_task_billing_status.minutes_of_service` | `provider_tasks_YYYY_MM.minutes_of_service` | `psl.csv`, `rvz.csv` | Direct mapping |
| `billing_code` | `provider_task_billing_status.billing_code` | `provider_tasks_YYYY_MM.billing_code` | `psl.csv`, `rvz.csv` | Direct mapping |
| `billing_code_description` | `provider_task_billing_status.billing_code_description` | `task_billing_codes.description` | N/A (Lookup) | Lookup from `task_billing_codes` table |
| `billing_status` | `provider_task_billing_status.billing_status` | N/A | N/A | Derived from internal logic/workflow |
| `is_billed` | `provider_task_billing_status.is_billed` | N/A | N/A | Derived from internal logic/workflow |
| `is_invoiced` | `provider_task_billing_status.is_invoiced` | N/A | N/A | Derived from internal logic/workflow |
| `is_claim_submitted` | `provider_task_billing_status.is_claim_submitted` | N/A | N/A | Derived from internal logic/workflow |
| `is_insurance_processed` | `provider_task_billing_status.is_insurance_processed` | N/A | N/A | Derived from internal logic/workflow |
| `is_approved_to_pay` | `provider_task_billing_status.is_approved_to_pay` | N/A | N/A | Derived from internal logic/workflow |
| `is_paid` | `provider_task_billing_status.is_paid` | N/A | N/A | Derived from internal logic/workflow |
| `is_carried_over` | `provider_task_billing_status.is_carried_over` | N/A | N/A | Derived from internal logic/workflow |

**2. Care Provider Dashboard Traceability**
| Dashboard Column | Production Table.Column | Staging Table.Column | CSV Source(s) | Transformation/Aggregation Notes |
|------------------|-------------------------|----------------------|---------------|----------------------------------|
| `user_id` | `users.user_id` | `source_users.user_id` | N/A (Internal) | User ID generation/lookup |
| `full_name` | `users.full_name` | `source_users.full_name` | N/A (Internal) | User data entry/lookup |
| `username` | `users.username` | `source_users.username` | N/A (Internal) | User data entry/lookup |
| `patient_id` | `patient_assignments.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `provider_id` | `patient_assignments.provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `coordinator_id` | `patient_assignments.coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `patient_id` | `patients.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `patients.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `patients.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `patients.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `status` | `patients.status` | `SOURCE_PATIENT_DATA.Pt Status` | `ZMO_Main.csv` | Direct mapping from `Pt Status`, default 'Active' if null |
| `facility` | `patients.facility` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Direct mapping from `Fac` (if exists), lookup in `facilities` table |
| `current_facility_id` | `patients.current_facility_id` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Facility ID lookup from `facilities` table based on `Fac` |
| `last_visit_date` | `patients.last_visit_date` | N/A | `cmlog.csv`, `psl.csv`, `rvz.csv` | Aggregated from latest `activity_date` in tasks |
| `service_type` | `patients.service_type` | N/A | `psl.csv`, `rvz.csv` | Derived from `Service` in provider tasks |
| `er_count_1yr` | `patients.er_count_1yr` | N/A | N/A | To be derived from task data / other sources (currently NULL) |
| `hospitalization_count_1yr` | `patients.hospitalization_count_1yr` | N/A | N/A | To be derived from task data / other sources (currently NULL) |
| `subjective_risk_level` | `patients.subjective_risk_level` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `mental_health_concerns` | `patients.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `active_specialists` | `patients.active_specialists` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `code_status` | `patients.code_status` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `cognitive_function` | `patients.cognitive_function` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `functional_status` | `patients.functional_status` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `goals_of_care` | `patients.goals_of_care` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `goc_value` | `patients.goc_value` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `initial_tv_completed` | `patients.initial_tv_completed` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Boolean derived from `Initial TV Date` presence |
| `initial_tv_completed_date` | `patients.initial_tv_completed_date` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Date parsing from `Initial TV Date` |
| `initial_tv_notes` | `patients.initial_tv_notes` | `SOURCE_PATIENT_DATA.Initial TV Notes` | `ZMO_Main.csv` | Direct mapping from `Initial TV Notes` |
| `notes` | `patients.notes` | `SOURCE_PATIENT_DATA.Notes` | `ZMO_Main.csv` | Concatenation of various note fields |
| `patient_id` | `patient_panel.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `patient_panel.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `patient_panel.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `patient_panel.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `status` | `patient_panel.status` | `SOURCE_PATIENT_DATA.Pt Status` | `ZMO_Main.csv` | Direct mapping from `Pt Status`, default 'Active' if null |
| `facility` | `patient_panel.facility` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Direct mapping from `Fac` (if exists), lookup in `facilities` table |
| `current_facility_id` | `patient_panel.current_facility_id` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Facility ID lookup from `facilities` table based on `Fac` |
| `last_visit_date` | `patient_panel.last_visit_date` | N/A | `cmlog.csv`, `psl.csv`, `rvz.csv` | Aggregated from latest `activity_date` in tasks |
| `last_visit_service_type` | `patient_panel.last_visit_service_type` | N/A | `psl.csv`, `rvz.csv` | Derived from `Service` in provider tasks |
| `assigned_coordinator_id` | `patient_panel.assigned_coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `provider_id` | `patient_panel.provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `goc_value` | `patient_panel.goc_value` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `code_status` | `patient_panel.code_status` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `cognitive_function` | `patient_panel.cognitive_function` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `functional_status` | `patient_panel.functional_status` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `subjective_risk_level` | `patient_panel.subjective_risk_level` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `er_count_1yr` | `patient_panel.er_count_1yr` | N/A | N/A | To be derived from task data / other sources (currently NULL) |
| `hospitalization_count_1yr` | `patient_panel.hospitalization_count_1yr` | N/A | N/A | To be derived from task data / other sources (currently NULL) |
| `mental_health_concerns` | `patient_panel.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `goals_of_care` | `patient_panel.goals_of_care` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `active_specialists` | `patient_panel.active_specialists` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `facility_id` | `facilities.facility_id` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Generated ID, lookup from `Fac` |
| `facility_name` | `facilities.facility_name` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Direct mapping from `Fac`, cleaned |
| `onboarding_id` | `onboarding_patients.onboarding_id` | N/A | N/A | Auto-generated/Sequence ID |
| `patient_id` | `onboarding_patients.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `onboarding_patients.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `onboarding_patients.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `onboarding_patients.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `phone_primary` | `onboarding_patients.phone_primary` | `SOURCE_PATIENT_DATA.Phone` | `ZMO_Main.csv` | Direct mapping from `Phone`, cleaned |
| `email` | `onboarding_patients.email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `hypertension` | `onboarding_patients.hypertension` | `SOURCE_PATIENT_DATA.Hypertension` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `mental_health_concerns` | `onboarding_patients.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `dementia` | `onboarding_patients.dementia` | `SOURCE_PATIENT_DATA.Dementia` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `annual_well_visit` | `onboarding_patients.annual_well_visit` | `SOURCE_PATIENT_DATA.Last Annual Wellness Visit` | `ZMO_Main.csv` | Direct mapping from relevant column |
| `created_date` | `onboarding_patients.created_date` | N/A | N/A | System timestamp |
| `tv_date` | `onboarding_patients.tv_date` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Direct mapping from `Initial TV Date` |
| `tv_time` | `onboarding_patients.tv_time` | N/A | N/A | To be derived from `Initial TV Date`/`Initial TV Time` (if available) |
| `assigned_provider_user_id` | `onboarding_patients.assigned_provider_user_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `initial_tv_completed` | `onboarding_patients.initial_tv_completed` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Boolean derived from `Initial TV Date` presence |
| `initial_tv_provider` | `onboarding_patients.initial_tv_provider` | `SOURCE_PATIENT_DATA.Initial TV Prov` | `ZMO_Main.csv` | Direct mapping from `Initial TV Prov` |
| `visit_type` | `onboarding_patients.visit_type` | N/A | N/A | Derived from task data / other sources (currently NULL) |
| `billing_code` | `onboarding_patients.billing_code` | N/A | N/A | Derived from task data / other sources (currently NULL) |
| `duration_minutes` | `onboarding_patients.duration_minutes` | N/A | N/A | Derived from task data / other sources (currently NULL) |
| `provider_task_id` | `provider_tasks_YYYY_MM.provider_task_id` | N/A | N/A | Auto-generated/Sequence ID |
| `provider_id` | `provider_tasks_YYYY_MM.provider_id` | `SOURCE_PROVIDER_TASKS_HISTORY.provider_code` | `psl.csv`, `rvz.csv` | Mapped via `user_code_map` from `Prov` |
| `patient_id` | `provider_tasks_YYYY_MM.patient_id` | `SOURCE_PROVIDER_TASKS_HISTORY.patient_name_raw` | `psl.csv`, `rvz.csv` | Patient ID normalization from `Patient Last, First DOB` |
| `task_date` | `provider_tasks_YYYY_MM.task_date` | `SOURCE_PROVIDER_TASKS_HISTORY.activity_date` | `psl.csv`, `rvz.csv` | Date parsing from `DOS` (MM/DD/YY, MM/DD/YYYY to YYYY-MM-DD) |
| `notes` | `provider_tasks_YYYY_MM.notes` | `SOURCE_PROVIDER_TASKS_HISTORY.Notes` | `psl.csv`, `rvz.csv` | Direct mapping from `Notes` |
| `minutes_of_service` | `provider_tasks_YYYY_MM.minutes_of_service` | `SOURCE_PROVIDER_TASKS_HISTORY.minutes_raw` | `psl.csv`, `rvz.csv` | Numeric conversion from `Minutes` (e.g., "60-69" to 69) |
| `task_description` | `provider_tasks_YYYY_MM.task_description` | `SOURCE_PROVIDER_TASKS_HISTORY.service` | `psl.csv`, `rvz.csv` | Direct mapping from `Service`, cleaned |
| `billing_code` | `provider_tasks_YYYY_MM.billing_code` | `SOURCE_PROVIDER_TASKS_HISTORY.billing_code` | `psl.csv`, `rvz.csv` | Direct mapping from `Coding`, validated |
| `billing_code_description` | `provider_tasks_YYYY_MM.billing_code_description` | `task_billing_codes.description` | N/A (Lookup) | Lookup from `task_billing_codes` table |
| `source_system` | `provider_tasks_YYYY_MM.source_system` | N/A | N/A | Derived (e.g., 'psl', 'rvz') |
| `imported_at` | `provider_tasks_YYYY_MM.imported_at` | N/A | N/A | System timestamp |
| `patient_id` | `coordinator_tasks_YYYY_MM.patient_id` | `source_coordinator_tasks_history.patient_name_raw` | `cmlog.csv` | Patient ID normalization from `Pt Name` |
| `task_date` | `coordinator_tasks_YYYY_MM.task_date` | `source_coordinator_tasks_history.activity_date` | `cmlog.csv` | Date parsing from `Date Only` (MM/DD/YY, MM/DD/YYYY to YYYY-MM-DD) |
| `date` | `coordinator_tasks_YYYY_MM.date` | `source_coordinator_tasks_history.activity_date` | `cmlog.csv` | Alias of `task_date` |
| `activity_date` | `coordinator_tasks_YYYY_MM.activity_date` | `source_coordinator_tasks_history.activity_date` | `cmlog.csv` | Alias of `task_date` |
| `patient_name` | `tasks.patient_name` | `patients.first_name`, `patients.last_name` | `ZMO_Main.csv` | Lookup from `patients` table |
| `patient_id` | `tasks.patient_id` | `patients.patient_id` | `ZMO_Main.csv` | Direct mapping from `patients` table |
| `user_id` | `tasks.user_id` | `users.user_id` | N/A (Internal) | Direct mapping from `users` table |
| `full_name` | `tasks.full_name` | `users.full_name` | N/A (Internal) | Direct mapping from `users` table |
| `staff_code` | `tasks.staff_code` | `user_code_map.staff_code` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Lookup from `user_code_map` table |
| `role_id` | `tasks.role_id` | `user_roles.role_id` | N/A (Internal) | Direct mapping from `user_roles` table |
| `task_date` | `tasks.task_date` | `coordinator_tasks_YYYY_MM.task_date`, `provider_tasks_YYYY_MM.task_date` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `task_type` | `tasks.task_type` | `coordinator_tasks_YYYY_MM.task_type` | `cmlog.csv` | Direct mapping from coordinator tasks |
| `duration_minutes` | `tasks.duration_minutes` | `coordinator_tasks_YYYY_MM.duration_minutes`, `provider_tasks_YYYY_MM.minutes_of_service` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `service_code` | `tasks.service_code` | `provider_tasks_YYYY_MM.billing_code` | `psl.csv`, `rvz.csv` | Direct mapping from provider tasks |
| `notes` | `tasks.notes` | `coordinator_tasks_YYYY_MM.notes`, `provider_tasks_YYYY_MM.notes` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `task_state` | `tasks.task_state` | N/A | N/A | Derived from internal logic/workflow |
| `provider_id` | `provider_weekly_summary_with_billing.provider_id` | `provider_tasks_YYYY_MM.provider_id` | `psl.csv`, `rvz.csv` | Aggregation from provider tasks |
| `provider_name` | `provider_weekly_summary_with_billing.provider_name` | `users.full_name` (lookup via `provider_id`) | N/A (Lookup) | Lookup from `users` table |
| `week_start_date` | `provider_weekly_summary_with_billing.week_start_date` | N/A | N/A | Derived from `task_date` (week start) |
| `week_end_date` | `provider_weekly_summary_with_billing.week_end_date` | N/A | N/A | Derived from `task_date` (week end) |
| `year` | `provider_weekly_summary_with_billing.year` | N/A | N/A | Derived from `task_date` (year) |
| `week_number` | `provider_weekly_summary_with_billing.week_number` | N/A | N/A | Derived from `task_date` (week number) |
| `total_tasks_completed` | `provider_weekly_summary_with_billing.total_tasks_completed` | `provider_tasks_YYYY_MM.provider_task_id` | `psl.csv`, `rvz.csv` | Count aggregation of provider tasks |
| `total_time_spent_minutes` | `provider_weekly_summary_with_billing.total_time_spent_minutes` | `provider_tasks_YYYY_MM.minutes_of_service` | `psl.csv`, `rvz.csv` | Sum aggregation of `minutes_of_service` |
| `billing_code` | `provider_weekly_summary_with_billing.billing_code` | `provider_tasks_YYYY_MM.billing_code` | `psl.csv`, `rvz.csv` | Aggregation of billing codes from provider tasks |
| `billing_code_description` | `provider_weekly_summary_with_billing.billing_code_description` | `task_billing_codes.description` | N/A (Lookup) | Lookup from `task_billing_codes` table |
| `status` | `provider_weekly_summary_with_billing.status` | N/A | N/A | Derived from internal logic/workflow |
| `paid` | `provider_weekly_summary_with_billing.paid` | `provider_task_billing_status.is_paid` | N/A | Direct mapping/aggregation from billing status |
| `created_date` | `provider_weekly_summary_with_billing.created_date` | N/A | N/A | System timestamp |
| `updated_date` | `provider_weekly_summary_with_billing.updated_date` | N/A | N/A | System timestamp |
| `billing_status_id` | `provider_task_billing_status.billing_status_id` | N/A | N/A | Auto-generated/Sequence ID |
| `provider_task_id` | `provider_task_billing_status.provider_task_id` | `provider_tasks_YYYY_MM.provider_task_id` | N/A | Direct mapping |
| `provider_id` | `provider_task_billing_status.provider_id` | `provider_tasks_YYYY_MM.provider_id` | `psl.csv`, `rvz.csv` | Direct mapping |
| `provider_name` | `provider_task_billing_status.provider_name` | `users.full_name` (lookup via `provider_id`) | N/A (Lookup) | Lookup from `users` table |
| `patient_name` | `provider_task_billing_status.patient_name` | `patients.first_name`, `patients.last_name` | `ZMO_Main.csv` | Lookup from `patients` table |
| `task_date` | `provider_task_billing_status.task_date` | `provider_tasks_YYYY_MM.task_date` | `psl.csv`, `rvz.csv` | Direct mapping |
| `billing_week` | `provider_task_billing_status.billing_week` | N/A | N/A | Derived from `task_date` (week number) |
| `week_start_date` | `provider_task_billing_status.week_start_date` | N/A | N/A | Derived from `task_date` (week start) |
| `week_end_date` | `provider_task_billing_status.week_end_date` | N/A | N/A | Derived from `task_date` (week end) |
| `task_description` | `provider_task_billing_status.task_description` | `provider_tasks_YYYY_MM.task_description` | `psl.csv`, `rvz.csv` | Direct mapping |
| `minutes_of_service` | `provider_task_billing_status.minutes_of_service` | `provider_tasks_YYYY_MM.minutes_of_service` | `psl.csv`, `rvz.csv` | Direct mapping |
| `billing_code` | `provider_task_billing_status.billing_code` | `provider_tasks_YYYY_MM.billing_code` | `psl.csv`, `rvz.csv` | Direct mapping |
| `billing_code_description` | `provider_task_billing_status.billing_code_description` | `task_billing_codes.description` | N/A (Lookup) | Lookup from `task_billing_codes` table |
| `billing_status` | `provider_task_billing_status.billing_status` | N/A | N/A | Derived from internal logic/workflow |
| `is_billed` | `provider_task_billing_status.is_billed` | N/A | N/A | Derived from internal logic/workflow |
| `is_invoiced` | `provider_task_billing_status.is_invoiced` | N/A | N/A | Derived from internal logic/workflow |
| `is_claim_submitted` | `provider_task_billing_status.is_claim_submitted` | N/A | N/A | Derived from internal logic/workflow |
| `is_insurance_processed` | `provider_task_billing_status.is_insurance_processed` | N/A | N/A | Derived from internal logic/workflow |
| `is_approved_to_pay` | `provider_task_billing_status.is_approved_to_pay` | N/A | N/A | Derived from internal logic/workflow |
| `is_paid` | `provider_task_billing_status.is_paid` | N/A | N/A | Derived from internal logic/workflow |
| `is_carried_over` | `provider_task_billing_status.is_carried_over` | N/A | N/A | Derived from internal logic/workflow |

**3. Care Coordinator Dashboard Traceability**
| Dashboard Column | Production Table.Column | Staging Table.Column | CSV Source(s) | Transformation/Aggregation Notes |
|------------------|-------------------------|----------------------|---------------|----------------------------------|
| `user_id` | `users.user_id` | `source_users.user_id` | N/A (Internal) | User ID generation/lookup |
| `username` | `users.username` | `source_users.username` | N/A (Internal) | User data entry/lookup |
| `full_name` | `users.full_name` | `source_users.full_name` | N/A (Internal) | User data entry/lookup |
| `patient_id` | `patient_assignments.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `provider_id` | `patient_assignments.provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `coordinator_id` | `patient_assignments.coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `patient_id` | `patients.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `patients.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `patients.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `patients.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `status` | `patients.status` | `SOURCE_PATIENT_DATA.Pt Status` | `ZMO_Main.csv` | Direct mapping from `Pt Status`, default 'Active' if null |
| `address_street` | `patients.address_street` | `SOURCE_PATIENT_DATA.Street` | `ZMO_Main.csv` | Direct mapping from `Street`, cleaned |
| `address_city` | `patients.address_city` | `SOURCE_PATIENT_DATA.City` | `ZMO_Main.csv` | Direct mapping from `City`, cleaned |
| `address_state` | `patients.address_state` | `SOURCE_PATIENT_DATA.State` | `ZMO_Main.csv` | Direct mapping from `State`, cleaned |
| `address_zip` | `patients.address_zip` | `SOURCE_PATIENT_DATA.Zip` | `ZMO_Main.csv` | Direct mapping from `Zip`, cleaned |
| `phone_primary` | `patients.phone_primary` | `SOURCE_PATIENT_DATA.Phone` | `ZMO_Main.csv` | Direct mapping from `Phone`, cleaned |
| `email` | `patients.email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `facility` | `patients.facility` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Direct mapping from `Fac` (if exists), lookup in `facilities` table |
| `current_facility_id` | `patients.current_facility_id` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Facility ID lookup from `facilities` table based on `Fac` |
| `last_visit_date` | `patients.last_visit_date` | N/A | `cmlog.csv`, `psl.csv`, `rvz.csv` | Aggregated from latest `activity_date` in tasks |
| `service_type` | `patients.service_type` | N/A | `psl.csv`, `rvz.csv` | Derived from `Service` in provider tasks |
| `appointment_contact_name` | `patients.appointment_contact_name` | `SOURCE_PATIENT_DATA.Contact Name` | `ZMO_Main.csv` | Direct mapping from `Contact Name` |
| `appointment_contact_phone` | `patients.appointment_contact_phone` | `SOURCE_PATIENT_DATA.Contact Phone` | `ZMO_Main.csv` | Direct mapping from `Contact Phone` |
| `medical_contact_name` | `patients.medical_contact_name` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_phone` | `patients.medical_contact_phone` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `patient_id` | `patient_panel.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `patient_panel.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `patient_panel.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `patient_panel.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `gender` | `patient_panel.gender` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `phone_primary` | `patient_panel.phone_primary` | `SOURCE_PATIENT_DATA.Phone` | `ZMO_Main.csv` | Direct mapping from `Phone`, cleaned |
| `email` | `patient_panel.email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `address_street` | `patient_panel.address_street` | `SOURCE_PATIENT_DATA.Street` | `ZMO_Main.csv` | Direct mapping from `Street`, cleaned |
| `address_city` | `patient_panel.address_city` | `SOURCE_PATIENT_DATA.City` | `ZMO_Main.csv` | Direct mapping from `City`, cleaned |
| `address_state` | `patient_panel.address_state` | `SOURCE_PATIENT_DATA.State` | `ZMO_Main.csv` | Direct mapping from `State`, cleaned |
| `address_zip` | `patient_panel.address_zip` | `SOURCE_PATIENT_DATA.Zip` | `ZMO_Main.csv` | Direct mapping from `Zip`, cleaned |
| `emergency_contact_name` | `patient_panel.emergency_contact_name` | `SOURCE_PATIENT_DATA.Contact Name` | `ZMO_Main.csv` | Direct mapping from `Contact Name` |
| `emergency_contact_phone` | `patient_panel.emergency_contact_phone` | `SOURCE_PATIENT_DATA.Contact Phone` | `ZMO_Main.csv` | Direct mapping from `Contact Phone` |
| `insurance_primary` | `patient_panel.insurance_primary` | `SOURCE_PATIENT_DATA.Ins1` | `ZMO_Main.csv` | Direct mapping from `Ins1`, cleaned |
| `insurance_policy_number` | `patient_panel.insurance_policy_number` | `SOURCE_PATIENT_DATA.Policy` | `ZMO_Main.csv` | Direct mapping from `Policy`, cleaned |
| `medical_records_requested` | `patient_panel.medical_records_requested` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `referral_documents_received` | `patient_panel.referral_documents_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `insurance_cards_received` | `patient_panel.insurance_cards_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `emed_signature_received` | `patient_panel.emed_signature_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `hypertension` | `patient_panel.hypertension` | `SOURCE_PATIENT_DATA.Hypertension` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `mental_health_concerns` | `patient_panel.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `dementia` | `patient_panel.dementia` | `SOURCE_PATIENT_DATA.Dementia` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `appointment_contact_name` | `patient_panel.appointment_contact_name` | `SOURCE_PATIENT_DATA.Contact Name` | `ZMO_Main.csv` | Direct mapping from `Contact Name` |
| `appointment_contact_phone` | `patient_panel.appointment_contact_phone` | `SOURCE_PATIENT_DATA.Contact Phone` | `ZMO_Main.csv` | Direct mapping from `Contact Phone` |
| `appointment_contact_email` | `patient_panel.appointment_contact_email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_name` | `patient_panel.medical_contact_name` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_phone` | `patient_panel.medical_contact_phone` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_email` | `patient_panel.medical_contact_email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `primary_care_provider` | `patient_panel.primary_care_provider` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `pcp_last_seen` | `patient_panel.pcp_last_seen` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `active_specialists` | `patient_panel.active_specialists` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `chronic_conditions_provider` | `patient_panel.chronic_conditions_provider` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `clinical_biometric` | `patient_panel.clinical_biometric` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `provider_mh_schizophrenia` | `patient_panel.provider_mh_schizophrenia` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_depression` | `patient_panel.provider_mh_depression` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_anxiety` | `patient_panel.provider_mh_anxiety` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_stress` | `patient_panel.provider_mh_stress` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_adhd` | `patient_panel.provider_mh_adhd` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_bipolar` | `patient_panel.provider_mh_bipolar` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_suicidal` | `patient_panel.provider_mh_suicidal` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `annual_well_visit` | `patient_panel.annual_well_visit` | `SOURCE_PATIENT_DATA.Last Annual Wellness Visit` | `ZMO_Main.csv` | Direct mapping from relevant column |
| `facility` | `patient_panel.facility` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Direct mapping from `Fac` (if exists), lookup in `facilities` table |
| `current_facility_id` | `patient_panel.current_facility_id` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Facility ID lookup from `facilities` table based on `Fac` |
| `provider_id` | `patient_panel.provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `coordinator_id` | `patient_panel.coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `provider_name` | `patient_panel.provider_name` | `users.full_name` (lookup via `provider_id`) | N/A (Lookup) | Lookup from `users` table |
| `coordinator_name` | `patient_panel.coordinator_name` | `users.full_name` (lookup via `coordinator_id`) | N/A (Lookup) | Lookup from `users` table |
| `initial_tv_completed_date` | `patient_panel.initial_tv_completed_date` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Date parsing from `Initial TV Date` |
| `initial_tv_provider` | `patient_panel.initial_tv_provider` | `SOURCE_PATIENT_DATA.Initial TV Prov` | `ZMO_Main.csv` | Direct mapping from `Initial TV Prov` |
| `assigned_coordinator_id` | `patient_panel.assigned_coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `assigned_provider_id` | `patient_panel.assigned_provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `eligibility_status` | `patient_panel.eligibility_status` | N/A | N/A | To be derived from workflow/status (currently NULL) |
| `eligibility_notes` | `patient_panel.eligibility_notes` | N/A | N/A | To be derived from workflow/status (currently NULL) |
| `eligibility_verified` | `patient_panel.eligibility_verified` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `emed_chart_created` | `patient_panel.emed_chart_created` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `chart_id` | `patient_panel.chart_id` | N/A | N/A | To be derived from external system/workflow (currently NULL) |
| `facility_confirmed` | `patient_panel.facility_confirmed` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `chart_notes` | `patient_panel.chart_notes` | N/A | N/A | To be derived from workflow/status (currently NULL) |
| `intake_call_completed` | `patient_panel.intake_call_completed` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `intake_notes` | `patient_panel.intake_notes` | N/A | N/A | To be derived from workflow/status (currently NULL) |
| `coordinator_task_id` | `coordinator_tasks_YYYY_MM.coordinator_task_id` | N/A | N/A | Auto-generated/Sequence ID |
| `task_id` | `coordinator_tasks_YYYY_MM.task_id` | N/A | N/A | Auto-generated/Sequence ID |
| `patient_id` | `coordinator_tasks_YYYY_MM.patient_id` | `source_coordinator_tasks_history.patient_name_raw` | `cmlog.csv` | Patient ID normalization from `Pt Name` |
| `coordinator_id` | `coordinator_tasks_YYYY_MM.coordinator_id` | `source_coordinator_tasks_history.staff_code` | `cmlog.csv` | Mapped via `user_code_map` from `Staff` |
| `task_date` | `coordinator_tasks_YYYY_MM.task_date` | `source_coordinator_tasks_history.activity_date` | `cmlog.csv` | Date parsing from `Date Only` (MM/DD/YY, MM/DD/YYYY to YYYY-MM-DD) |
| `duration_minutes` | `coordinator_tasks_YYYY_MM.duration_minutes` | `source_coordinator_tasks_history.minutes_raw` | `cmlog.csv` | Numeric conversion from `Mins B` |
| `task_type` | `coordinator_tasks_YYYY_MM.task_type` | `source_coordinator_tasks_history.task_type` | `cmlog.csv` | Direct mapping from `Type`, cleaned |
| `notes` | `coordinator_tasks_YYYY_MM.notes` | `source_coordinator_tasks_history.notes` | `cmlog.csv` | Direct mapping from `Notes`, cleaned |
| `source_system` | `coordinator_tasks_YYYY_MM.source_system` | N/A | N/A | Derived (e.g., 'cmlog') |
| `imported_at` | `coordinator_tasks_YYYY_MM.imported_at` | N/A | N/A | System timestamp |
| `coordinator_name` | `coordinator_tasks_YYYY_MM.coordinator_name` | `users.full_name` (lookup via `coordinator_id`) | N/A (Lookup) | Lookup from `users` table |
| `patient_id` | `workflow_instances.patient_id` | `patients.patient_id` | `ZMO_Main.csv` | Direct mapping from `patients` table |
| `patient_name` | `tasks.patient_name` | `patients.first_name`, `patients.last_name` | `ZMO_Main.csv` | Lookup from `patients` table |
| `patient_id` | `tasks.patient_id` | `patients.patient_id` | `ZMO_Main.csv` | Direct mapping from `patients` table |
| `user_id` | `tasks.user_id` | `users.user_id` | N/A (Internal) | Direct mapping from `users` table |
| `full_name` | `tasks.full_name` | `users.full_name` | N/A (Internal) | Direct mapping from `users` table |
| `staff_code` | `tasks.staff_code` | `user_code_map.staff_code` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Lookup from `user_code_map` table |
| `role_id` | `tasks.role_id` | `user_roles.role_id` | N/A (Internal) | Direct mapping from `user_roles` table |
| `task_date` | `tasks.task_date` | `coordinator_tasks_YYYY_MM.task_date`, `provider_tasks_YYYY_MM.task_date` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `task_type` | `tasks.task_type` | `coordinator_tasks_YYYY_MM.task_type` | `cmlog.csv` | Direct mapping from coordinator tasks |
| `duration_minutes` | `tasks.duration_minutes` | `coordinator_tasks_YYYY_MM.duration_minutes`, `provider_tasks_YYYY_MM.minutes_of_service` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `service_code` | `tasks.service_code` | `provider_tasks_YYYY_MM.billing_code` | `psl.csv`, `rvz.csv` | Direct mapping from provider tasks |
| `notes` | `tasks.notes` | `coordinator_tasks_YYYY_MM.notes`, `provider_tasks_YYYY_MM.notes` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `task_state` | `tasks.task_state` | N/A | N/A | Derived from internal logic/workflow |
| `code_id` | `task_billing_codes.code_id` | N/A | N/A | Internal table (static data) |
| `task_description` | `task_billing_codes.task_description` | N/A | N/A | Internal table (static data) |
| `billing_code` | `task_billing_codes.billing_code` | N/A | N/A | Internal table (static data) |
| `description` | `task_billing_codes.description` | N/A | N/A | Internal table (static data) |
| `patient_id` | `coordinator_monthly_summary_YYYY_MM.patient_id` | `coordinator_tasks_YYYY_MM.patient_id` | `cmlog.csv` | Aggregation from coordinator tasks |
| `total_minutes` | `coordinator_monthly_summary_YYYY_MM.total_minutes` | `coordinator_tasks_YYYY_MM.duration_minutes` | `cmlog.csv` | Sum aggregation of `duration_minutes` |
| `coordinator_id` | `coordinator_monthly_summary_YYYY_MM.coordinator_id` | `coordinator_tasks_YYYY_MM.coordinator_id` | `cmlog.csv` | Aggregation from coordinator tasks |
| `billing_code` | `coordinator_monthly_summary_YYYY_MM.billing_code` | N/A | N/A | Derived from `task_type` / internal logic |
| `billing_code_description` | `coordinator_monthly_summary_YYYY_MM.billing_code_description` | `task_billing_codes.description` | N/A (Lookup) | Lookup from `task_billing_codes` table |

**4. Patient Onboarding Dashboard Traceability**
| Dashboard Column | Production Table.Column | Staging Table.Column | CSV Source(s) | Transformation/Aggregation Notes |
|------------------|-------------------------|----------------------|---------------|----------------------------------|
| `onboarding_id` | `onboarding_patients.onboarding_id` | N/A | N/A | Auto-generated/Sequence ID |
| `patient_id` | `onboarding_patients.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `onboarding_patients.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `onboarding_patients.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `onboarding_patients.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `phone_primary` | `onboarding_patients.phone_primary` | `SOURCE_PATIENT_DATA.Phone` | `ZMO_Main.csv` | Direct mapping from `Phone`, cleaned |
| `email` | `onboarding_patients.email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `gender` | `onboarding_patients.gender` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `emergency_contact_name` | `onboarding_patients.emergency_contact_name` | `SOURCE_PATIENT_DATA.Contact Name` | `ZMO_Main.csv` | Direct mapping from `Contact Name` |
| `emergency_contact_phone` | `onboarding_patients.emergency_contact_phone` | `SOURCE_PATIENT_DATA.Contact Phone` | `ZMO_Main.csv` | Direct mapping from `Contact Phone` |
| `address_street` | `onboarding_patients.address_street` | `SOURCE_PATIENT_DATA.Street` | `ZMO_Main.csv` | Direct mapping from `Street`, cleaned |
| `address_city` | `onboarding_patients.address_city` | `SOURCE_PATIENT_DATA.City` | `ZMO_Main.csv` | Direct mapping from `City`, cleaned |
| `address_state` | `onboarding_patients.address_state` | `SOURCE_PATIENT_DATA.State` | `ZMO_Main.csv` | Direct mapping from `State`, cleaned |
| `address_zip` | `onboarding_patients.address_zip` | `SOURCE_PATIENT_DATA.Zip` | `ZMO_Main.csv` | Direct mapping from `Zip`, cleaned |
| `insurance_provider` | `onboarding_patients.insurance_provider` | `SOURCE_PATIENT_DATA.Ins1` | `ZMO_Main.csv` | Direct mapping from `Ins1`, cleaned |
| `policy_number` | `onboarding_patients.policy_number` | `SOURCE_PATIENT_DATA.Policy` | `ZMO_Main.csv` | Direct mapping from `Policy`, cleaned |
| `group_number` | `onboarding_patients.group_number` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `referral_source` | `onboarding_patients.referral_source` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `referring_provider` | `onboarding_patients.referring_provider` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `referral_date` | `onboarding_patients.referral_date` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `patient_status` | `onboarding_patients.patient_status` | `SOURCE_PATIENT_DATA.Pt Status` | `ZMO_Main.csv` | Direct mapping from `Pt Status`, default 'Active' if null |
| `facility_assignment` | `onboarding_patients.facility_assignment` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Direct mapping from `Fac`, cleaned |
| `assigned_pot_user_id` | `onboarding_patients.assigned_pot_user_id` | N/A | N/A | Internal assignment logic (currently NULL) |
| `stage1_complete` | `onboarding_patients.stage1_complete` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `stage5_complete` | `onboarding_patients.stage5_complete` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `created_date` | `onboarding_patients.created_date` | N/A | N/A | System timestamp |
| `updated_date` | `onboarding_patients.updated_date` | N/A | N/A | System timestamp |
| `completed_date` | `onboarding_patients.completed_date` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `eligibility_status` | `onboarding_patients.eligibility_status` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `eligibility_notes` | `onboarding_patients.eligibility_notes` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `eligibility_verified` | `onboarding_patients.eligibility_verified` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `emed_chart_created` | `onboarding_patients.emed_chart_created` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `chart_id` | `onboarding_patients.chart_id` | N/A | N/A | To be derived from external system/workflow (currently NULL) |
| `facility_confirmed` | `onboarding_patients.facility_confirmed` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `chart_notes` | `onboarding_patients.chart_notes` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `intake_call_completed` | `onboarding_patients.intake_call_completed` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `intake_notes` | `onboarding_patients.intake_notes` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `medical_records_requested` | `onboarding_patients.medical_records_requested` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `referral_documents_received` | `onboarding_patients.referral_documents_received` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `emed_signature_received` | `onboarding_patients.emed_signature_received` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `tv_scheduled` | `onboarding_patients.tv_scheduled` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Boolean derived from `Initial TV Date` presence |
| `tv_date` | `onboarding_patients.tv_date` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Direct mapping from `Initial TV Date` |
| `tv_time` | `onboarding_patients.tv_time` | N/A | N/A | To be derived from `Initial TV Date`/`Initial TV Time` (if available) |
| `patient_notified` | `onboarding_patients.patient_notified` | `SOURCE_PATIENT_DATA.CM Notified` | `ZMO_Main.csv` | Boolean derived from `CM Notified` presence |
| `initial_tv_completed` | `onboarding_patients.initial_tv_completed` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Boolean derived from `Initial TV Date` presence |
| `assigned_provider_user_id` | `onboarding_patients.assigned_provider_user_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `assigned_coordinator_user_id` | `onboarding_patients.assigned_coordinator_user_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `initial_tv_provider` | `onboarding_patients.initial_tv_provider` | `SOURCE_PATIENT_DATA.Initial TV Prov` | `ZMO_Main.csv` | Direct mapping from `Initial TV Prov` |
| `visit_type` | `onboarding_patients.visit_type` | N/A | N/A | Derived from task data / other sources (currently NULL) |
| `billing_code` | `onboarding_patients.billing_code` | N/A | N/A | Derived from task data / other sources (currently NULL) |
| `duration_minutes` | `onboarding_patients.duration_minutes` | N/A | N/A | Derived from task data / other sources (currently NULL) |
| `hypertension` | `onboarding_patients.hypertension` | `SOURCE_PATIENT_DATA.Hypertension` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `mental_health_concerns` | `onboarding_patients.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `dementia` | `onboarding_patients.dementia` | `SOURCE_PATIENT_DATA.Dementia` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `annual_well_visit` | `onboarding_patients.annual_well_visit` | `SOURCE_PATIENT_DATA.Last Annual Wellness Visit` | `ZMO_Main.csv` | Direct mapping from relevant column |
| `patient_id` | `patients.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `patients.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `patients.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `patients.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `gender` | `patients.gender` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `phone_primary` | `patients.phone_primary` | `SOURCE_PATIENT_DATA.Phone` | `ZMO_Main.csv` | Direct mapping from `Phone`, cleaned |
| `email` | `patients.email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `address_street` | `patients.address_street` | `SOURCE_PATIENT_DATA.Street` | `ZMO_Main.csv` | Direct mapping from `Street`, cleaned |
| `address_city` | `patients.address_city` | `SOURCE_PATIENT_DATA.City` | `ZMO_Main.csv` | Direct mapping from `City`, cleaned |
| `address_state` | `patients.address_state` | `SOURCE_PATIENT_DATA.State` | `ZMO_Main.csv` | Direct mapping from `State`, cleaned |
| `address_zip` | `patients.address_zip` | `SOURCE_PATIENT_DATA.Zip` | `ZMO_Main.csv` | Direct mapping from `Zip`, cleaned |
| `emergency_contact_name` | `patients.emergency_contact_name` | `SOURCE_PATIENT_DATA.Contact Name` | `ZMO_Main.csv` | Direct mapping from `Contact Name` |
| `emergency_contact_phone` | `patients.emergency_contact_phone` | `SOURCE_PATIENT_DATA.Contact Phone` | `ZMO_Main.csv` | Direct mapping from `Contact Phone` |
| `insurance_primary` | `patients.insurance_primary` | `SOURCE_PATIENT_DATA.Ins1` | `ZMO_Main.csv` | Direct mapping from `Ins1`, cleaned |
| `insurance_policy_number` | `patients.insurance_policy_number` | `SOURCE_PATIENT_DATA.Policy` | `ZMO_Main.csv` | Direct mapping from `Policy`, cleaned |
| `medical_records_requested` | `patients.medical_records_requested` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `referral_documents_received` | `patients.referral_documents_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `insurance_cards_received` | `patients.insurance_cards_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `emed_signature_received` | `patients.emed_signature_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `hypertension` | `patients.hypertension` | `SOURCE_PATIENT_DATA.Hypertension` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `mental_health_concerns` | `patients.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `dementia` | `patients.dementia` | `SOURCE_PATIENT_DATA.Dementia` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `appointment_contact_name` | `patients.appointment_contact_name` | `SOURCE_PATIENT_DATA.Contact Name` | `ZMO_Main.csv` | Direct mapping from `Contact Name` |
| `appointment_contact_phone` | `patients.appointment_contact_phone` | `SOURCE_PATIENT_DATA.Contact Phone` | `ZMO_Main.csv` | Direct mapping from `Contact Phone` |
| `appointment_contact_email` | `patients.appointment_contact_email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_name` | `patients.medical_contact_name` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_phone` | `patients.medical_contact_phone` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_email` | `patients.medical_contact_email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `primary_care_provider` | `patients.primary_care_provider` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `pcp_last_seen` | `patients.pcp_last_seen` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `last_annual_wellness_visit` | `patients.last_annual_wellness_visit` | `SOURCE_PATIENT_DATA.Last Annual Wellness Visit` | `ZMO_Main.csv` | Direct mapping from relevant column |
| `assigned_coordinator_id` | `patients.assigned_coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `enrollment_date` | `patients.enrollment_date` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `created_date` | `patients.created_date` | N/A | N/A | System timestamp |
| `status` | `patients.status` | `SOURCE_PATIENT_DATA.Pt Status` | `ZMO_Main.csv` | Direct mapping from `Pt Status`, default 'Active' if null |
| `patient_id` | `patient_panel.patient_id` | `SOURCE_PATIENT_DATA.LAST FIRST DOB` | `ZMO_Main.csv` | Patient ID normalization (LAST-FIRST-DOB) |
| `first_name` | `patient_panel.first_name` | `SOURCE_PATIENT_DATA.First` | `ZMO_Main.csv` | Direct mapping from `First`, cleaned |
| `last_name` | `patient_panel.last_name` | `SOURCE_PATIENT_DATA.Last` | `ZMO_Main.csv` | Direct mapping from `Last`, cleaned |
| `date_of_birth` | `patient_panel.date_of_birth` | `SOURCE_PATIENT_DATA.DOB` | `ZMO_Main.csv` | Date parsing from `DOB` |
| `gender` | `patient_panel.gender` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `phone_primary` | `patient_panel.phone_primary` | `SOURCE_PATIENT_DATA.Phone` | `ZMO_Main.csv` | Direct mapping from `Phone`, cleaned |
| `email` | `patient_panel.email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `address_street` | `patient_panel.address_street` | `SOURCE_PATIENT_DATA.Street` | `ZMO_Main.csv` | Direct mapping from `Street`, cleaned |
| `address_city` | `patient_panel.address_city` | `SOURCE_PATIENT_DATA.City` | `ZMO_Main.csv` | Direct mapping from `City`, cleaned |
| `address_state` | `patient_panel.address_state` | `SOURCE_PATIENT_DATA.State` | `ZMO_Main.csv` | Direct mapping from `State`, cleaned |
| `address_zip` | `patient_panel.address_zip` | `SOURCE_PATIENT_DATA.Zip` | `ZMO_Main.csv` | Direct mapping from `Zip`, cleaned |
| `emergency_contact_name` | `patient_panel.emergency_contact_name` | `SOURCE_PATIENT_DATA.Contact Name` | `ZMO_Main.csv` | Direct mapping from `Contact Name` |
| `emergency_contact_phone` | `patient_panel.emergency_contact_phone` | `SOURCE_PATIENT_DATA.Contact Phone` | `ZMO_Main.csv` | Direct mapping from `Contact Phone` |
| `insurance_primary` | `patient_panel.insurance_primary` | `SOURCE_PATIENT_DATA.Ins1` | `ZMO_Main.csv` | Direct mapping from `Ins1`, cleaned |
| `insurance_policy_number` | `patient_panel.insurance_policy_number` | `SOURCE_PATIENT_DATA.Policy` | `ZMO_Main.csv` | Direct mapping from `Policy`, cleaned |
| `medical_records_requested` | `patient_panel.medical_records_requested` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `referral_documents_received` | `patient_panel.referral_documents_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `insurance_cards_received` | `patient_panel.insurance_cards_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `emed_signature_received` | `patient_panel.emed_signature_received` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `hypertension` | `patient_panel.hypertension` | `SOURCE_PATIENT_DATA.Hypertension` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `mental_health_concerns` | `patient_panel.mental_health_concerns` | `SOURCE_PATIENT_DATA.Mental Health Concerns` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `dementia` | `patient_panel.dementia` | `SOURCE_PATIENT_DATA.Dementia` | `ZMO_Main.csv` | Direct mapping from relevant column, boolean conversion |
| `appointment_contact_name` | `patient_panel.appointment_contact_name` | `SOURCE_PATIENT_DATA.Contact Name` | `ZMO_Main.csv` | Direct mapping from `Contact Name` |
| `appointment_contact_phone` | `patient_panel.appointment_contact_phone` | `SOURCE_PATIENT_DATA.Contact Phone` | `ZMO_Main.csv` | Direct mapping from `Contact Phone` |
| `appointment_contact_email` | `patient_panel.appointment_contact_email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_name` | `patient_panel.medical_contact_name` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_phone` | `patient_panel.medical_contact_phone` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `medical_contact_email` | `patient_panel.medical_contact_email` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `primary_care_provider` | `patient_panel.primary_care_provider` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `pcp_last_seen` | `patient_panel.pcp_last_seen` | N/A | N/A | To be derived from patient data/other sources (currently NULL) |
| `active_specialists` | `patient_panel.active_specialists` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `chronic_conditions_provider` | `patient_panel.chronic_conditions_provider` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `clinical_biometric` | `patient_panel.clinical_biometric` | N/A | N/A | To be derived from patient assessment data (currently NULL) |
| `provider_mh_schizophrenia` | `patient_panel.provider_mh_schizophrenia` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_depression` | `patient_panel.provider_mh_depression` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_anxiety` | `patient_panel.provider_mh_anxiety` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_stress` | `patient_panel.provider_mh_stress` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_adhd` | `patient_panel.provider_mh_adhd` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_bipolar` | `patient_panel.provider_mh_bipolar` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `provider_mh_suicidal` | `patient_panel.provider_mh_suicidal` | N/A | N/A | To be derived from patient assessment data (currently FALSE) |
| `annual_well_visit` | `patient_panel.annual_well_visit` | `SOURCE_PATIENT_DATA.Last Annual Wellness Visit` | `ZMO_Main.csv` | Direct mapping from relevant column |
| `facility` | `patient_panel.facility` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Direct mapping from `Fac` (if exists), lookup in `facilities` table |
| `current_facility_id` | `patient_panel.current_facility_id` | `SOURCE_PATIENT_DATA.Fac` | `ZMO_Main.csv` | Facility ID lookup from `facilities` table based on `Fac` |
| `provider_id` | `patient_panel.provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `coordinator_id` | `patient_panel.coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `provider_name` | `patient_panel.provider_name` | `users.full_name` (lookup via `provider_id`) | N/A (Lookup) | Lookup from `users` table |
| `coordinator_name` | `patient_panel.coordinator_name` | `users.full_name` (lookup via `coordinator_id`) | N/A (Lookup) | Lookup from `users` table |
| `initial_tv_completed_date` | `patient_panel.initial_tv_completed_date` | `SOURCE_PATIENT_DATA.Initial TV Date` | `ZMO_Main.csv` | Date parsing from `Initial TV Date` |
| `initial_tv_provider` | `patient_panel.initial_tv_provider` | `SOURCE_PATIENT_DATA.Initial TV Prov` | `ZMO_Main.csv` | Direct mapping from `Initial TV Prov` |
| `assigned_coordinator_id` | `patient_panel.assigned_coordinator_id` | `SOURCE_PATIENT_DATA.Assigned CM` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned CM` |
| `assigned_provider_id` | `patient_panel.assigned_provider_id` | `SOURCE_PATIENT_DATA.Assigned Reg Prov` | `ZMO_Main.csv` | Mapped via `user_code_map` from `Assigned Reg Prov` |
| `eligibility_status` | `patient_panel.eligibility_status` | N/A | N/A | To be derived from workflow/status (currently NULL) |
| `eligibility_notes` | `patient_panel.eligibility_notes` | N/A | N/A | To be derived from workflow/status (currently NULL) |
| `eligibility_verified` | `patient_panel.eligibility_verified` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `emed_chart_created` | `patient_panel.emed_chart_created` | N/A | N/A | To be derived from workflow/status (currently FALSE) |
| `chart_id` | `patient_panel.chart_id` | N/A | N/A | To be derived from external system/workflow (currently NULL) |
| `facility_confirmed` | `patient_panel.facility_confirmed` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `chart_notes` | `patient_panel.chart_notes` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `intake_call_completed` | `patient_panel.intake_call_completed` | N/A | N/A | Derived from workflow/status (currently FALSE) |
| `intake_notes` | `patient_panel.intake_notes` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `coordinator_task_id` | `coordinator_tasks_YYYY_MM.coordinator_task_id` | N/A | N/A | Auto-generated/Sequence ID |
| `task_id` | `coordinator_tasks_YYYY_MM.task_id` | N/A | N/A | Auto-generated/Sequence ID |
| `patient_id` | `coordinator_tasks_YYYY_MM.patient_id` | `source_coordinator_tasks_history.patient_name_raw` | `cmlog.csv` | Patient ID normalization from `Pt Name` |
| `coordinator_id` | `coordinator_tasks_YYYY_MM.coordinator_id` | `source_coordinator_tasks_history.staff_code` | `cmlog.csv` | Mapped via `user_code_map` from `Staff` |
| `task_date` | `coordinator_tasks_YYYY_MM.task_date` | `source_coordinator_tasks_history.activity_date` | `cmlog.csv` | Date parsing from `Date Only` (MM/DD/YY, MM/DD/YYYY to YYYY-MM-DD) |
| `duration_minutes` | `coordinator_tasks_YYYY_MM.duration_minutes` | `source_coordinator_tasks_history.minutes_raw` | `cmlog.csv` | Numeric conversion from `Mins B` |
| `task_type` | `coordinator_tasks_YYYY_MM.task_type` | `source_coordinator_tasks_history.type` | `cmlog.csv` | Direct mapping from `Type`, cleaned |
| `notes` | `coordinator_tasks_YYYY_MM.notes` | `source_coordinator_tasks_history.notes` | `cmlog.csv` | Direct mapping from `Notes`, cleaned |
| `source_system` | `coordinator_tasks_YYYY_MM.source_system` | N/A | N/A | Derived (e.g., 'cmlog') |
| `imported_at` | `coordinator_tasks_YYYY_MM.imported_at` | N/A | N/A | System timestamp |
| `coordinator_name` | `coordinator_tasks_YYYY_MM.coordinator_name` | `users.full_name` (lookup via `coordinator_id`) | N/A (Lookup) | Lookup from `users` table |
| `workflow_instances.instance_id` | `workflow_instances.instance_id` | N/A | N/A | Auto-generated/Sequence ID |
| `workflow_instances.workflow_status` | `workflow_instances.workflow_status` | N/A | N/A | Derived from internal logic/workflow |
| `workflow_instances.patient_id` | `workflow_instances.patient_id` | `patients.patient_id` | `ZMO_Main.csv` | Direct mapping from `patients` table |
| `workflow_steps.step_id` | `workflow_steps.step_id` | N/A | N/A | Internal table (static data) |
| `workflow_steps.step_order` | `workflow_steps.step_order` | N/A | N/A | Internal table (static data) |
| `workflow_steps.task_name` | `workflow_steps.task_name` | N/A | N/A | Internal table (static data) |
| `workflow_steps.deliverable` | `workflow_steps.deliverable` | N/A | N/A | Internal table (static data) |
| `onboarding_tasks.onboarding_id` | `onboarding_tasks.onboarding_id` | `onboarding_patients.onboarding_id` | N/A | Direct mapping from `onboarding_patients` table |
| `onboarding_tasks.workflow_step_id` | `onboarding_tasks.workflow_step_id` | `workflow_steps.step_id` | N/A | Direct mapping from `workflow_steps` table |
| `onboarding_tasks.task_name` | `onboarding_tasks.task_name` | `workflow_steps.task_name` | N/A | Direct mapping from `workflow_steps` table |
| `onboarding_tasks.task_stage` | `onboarding_tasks.task_stage` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `onboarding_tasks.task_order` | `onboarding_tasks.task_order` | `workflow_steps.step_order` | N/A | Direct mapping from `workflow_steps` table |
| `onboarding_tasks.status` | `onboarding_tasks.status` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `onboarding_tasks.created_date` | `onboarding_tasks.created_date` | N/A | N/A | System timestamp |
| `onboarding_tasks.updated_date` | `onboarding_tasks.updated_date` | N/A | N/A | System timestamp |
| `onboarding_tasks.completed_by_user_id` | `onboarding_tasks.completed_by_user_id` | `users.user_id` | N/A (Internal) | Direct mapping from `users` table |
| `onboarding_tasks.completed_date` | `onboarding_tasks.completed_date` | N/A | N/A | Derived from workflow/status (currently NULL) |
| `onboarding_tasks.eligibility_verified` | `onboarding_tasks.eligibility_verified` | `onboarding_patients.eligibility_verified` | `ZMO_Main.csv` | Direct mapping from `onboarding_patients` table |
| `onboarding_tasks.emed_chart_created` | `onboarding_tasks.emed_chart_created` | `onboarding_patients.emed_chart_created` | `ZMO_Main.csv` | Direct mapping from `onboarding_patients` table |
| `onboarding_tasks.provider_assigned` | `onboarding_tasks.provider_assigned` | N/A | N/A | Derived from `onboarding_patients.assigned_provider_user_id` presence |
| `onboarding_tasks.coordinator_assigned` | `onboarding_tasks.coordinator_assigned` | N/A | N/A | Derived from `onboarding_patients.assigned_coordinator_user_id` presence |
| `onboarding_tasks.intake_call_completed` | `onboarding_tasks.intake_call_completed` | `onboarding_patients.intake_call_completed` | `ZMO_Main.csv` | Direct mapping from `onboarding_patients` table |
| `onboarding_tasks.tv_scheduled` | `onboarding_tasks.tv_scheduled` | `onboarding_patients.tv_scheduled` | `ZMO_Main.csv` | Direct mapping from `onboarding_patients` table |
| `onboarding_tasks.initial_tv_completed` | `onboarding_tasks.initial_tv_completed` | `onboarding_patients.initial_tv_completed` | `ZMO_Main.csv` | Direct mapping from `onboarding_patients` table |
| `tasks.patient_name` | `tasks.patient_name` | `patients.first_name`, `patients.last_name` | `ZMO_Main.csv` | Lookup from `patients` table |
| `tasks.patient_id` | `tasks.patient_id` | `patients.patient_id` | `ZMO_Main.csv` | Direct mapping from `patients` table |
| `tasks.user_id` | `tasks.user_id` | `users.user_id` | N/A (Internal) | Direct mapping from `users` table |
| `tasks.full_name` | `tasks.full_name` | `users.full_name` | N/A (Internal) | Direct mapping from `users` table |
| `tasks.staff_code` | `tasks.staff_code` | `user_code_map.staff_code` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Lookup from `user_code_map` table |
| `tasks.role_id` | `tasks.role_id` | `user_roles.role_id` | N/A (Internal) | Direct mapping from `user_roles` table |
| `tasks.task_date` | `tasks.task_date` | `coordinator_tasks_YYYY_MM.task_date`, `provider_tasks_YYYY_MM.task_date` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `tasks.task_type` | `tasks.task_type` | `coordinator_tasks_YYYY_MM.task_type` | `cmlog.csv` | Direct mapping from coordinator tasks |
| `tasks.duration_minutes` | `tasks.duration_minutes` | `coordinator_tasks_YYYY_MM.duration_minutes`, `provider_tasks_YYYY_MM.minutes_of_service` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `tasks.service_code` | `tasks.service_code` | `provider_tasks_YYYY_MM.billing_code` | `psl.csv`, `rvz.csv` | Direct mapping from provider tasks |
| `tasks.notes` | `tasks.notes` | `coordinator_tasks_YYYY_MM.notes`, `provider_tasks_YYYY_MM.notes` | `cmlog.csv`, `psl.csv`, `rvz.csv` | Direct mapping from task tables |
| `tasks.task_state` | `tasks.task_state` | N/A | N/A | Derived from internal logic/workflow |
| `task_billing_codes.code_id` | `task_billing_codes.code_id` | N/A | N/A | Internal table (static data) |
| `task_billing_codes.task_description` | `task_billing_codes.task_description` | N/A | N/A | Internal table (static data) |
| `task_billing_codes.billing_code` | `task_billing_codes.billing_code` | N/A | N/A | Internal table (static data) |
| `task_billing_codes.description` | `task_billing_codes.description` | N/A | N/A | Internal table (static data) |
