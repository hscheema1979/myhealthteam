# PowerShell script to backup and refresh all patient-related tables
# Usage: Run this script nightly to backup and refresh patient data

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Backup and refresh patients table
sqlite3 .\production.db "CREATE TABLE IF NOT EXISTS patients_old_$timestamp AS SELECT * FROM patients;"
sqlite3 .\production.db ".read src\sql\populate_patients.sql"

# Backup and refresh patient_assignments table
sqlite3 .\production.db "CREATE TABLE IF NOT EXISTS patient_assignments_old_$timestamp AS SELECT * FROM patient_assignments;"
sqlite3 .\production.db ".read src\sql\populate_patient_assignments.sql"

# Backup and refresh patient_visits table
sqlite3 .\production.db "CREATE TABLE IF NOT EXISTS patient_visits_old_$timestamp AS SELECT * FROM patient_visits;"
sqlite3 .\production.db ".read src\sql\patient_visits_refresh.sql"

# Backup and refresh patient_panel table
sqlite3 .\production.db "CREATE TABLE IF NOT EXISTS patient_panel_old_$timestamp AS SELECT * FROM patient_panel;"
sqlite3 .\production.db ".read src\sql\patient_panel_refresh.sql"

# Backup and refresh patient_region_mapping table
sqlite3 .\production.db "CREATE TABLE IF NOT EXISTS patient_region_mapping_old_$timestamp AS SELECT * FROM patient_region_mapping;"
sqlite3 .\production.db ".read src\sql\populate_patient_region_mapping.sql"

# Backup and refresh facility info in patient_panel
sqlite3 .\production.db "CREATE TABLE IF NOT EXISTS patient_panel_facility_old_$timestamp AS SELECT * FROM patient_panel;"
sqlite3 .\production.db ".read src\sql\update_patient_panel_facility.sql"

Write-Host "Patient data refresh complete. Backups created with timestamp $timestamp."
