# Enhanced PowerShell script to import CSV files to database


param(
    [switch]$AllMonths = $false,
    [switch]$SkipPatients = $false,
    [switch]$Coordinators = $false,
    [switch]$Providers = $false,
    [string[]]$Files = @(),
    [string]$DatabasePath = ".\sheets_data.db",
    [string]$StartDate = ""
)

[string]$YearMonth = (Get-Date -Format 'yyyy_MM')

# Import combined cmlog.csv to source_coordinator_tasks_history
Write-Host "Importing combined cmlog.csv to source_coordinator_tasks_history..."
if (Test-Path "$PSScriptRoot/../downloads/cmlog.csv") {
	$output = python "$PSScriptRoot/../src/utils/csv_to_sql.py" "$PSScriptRoot/../downloads/cmlog.csv" -s $DatabasePath -t "source_coordinator_tasks_history" --skip-empty-columns 2>&1
	if ($LASTEXITCODE -ne 0) {
		Write-Host "ERROR: Python import failed for cmlog.csv: $($output)" -ForegroundColor Red
		exit 1
	}
	$rowCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM source_coordinator_tasks_history;" 2>$null
	if (-not $rowCount -or $rowCount -eq 0) {
		Write-Host "WARNING: Table source_coordinator_tasks_history was created but is empty after import!" -ForegroundColor Yellow
	}
 else {
		Write-Host "Coordinator history imported ($rowCount rows)"
	}
	# Apply strict StartDate filter (normalize MM/DD/YYYY and MM/DD/YY to YYYY-MM-DD before compare)
	if ($StartDate -and $StartDate -match '^\d{4}-\d{2}-\d{2}$') {
		$sql = @"
DELETE FROM source_coordinator_tasks_history
WHERE (
  CASE
    WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
    WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER))
    ELSE NULL
  END
) < '$StartDate';
"@
		sqlite3 $DatabasePath $sql 2>$null
		$remaining = sqlite3 $DatabasePath "SELECT COUNT(*) FROM source_coordinator_tasks_history;" 2>$null
		Write-Host "Coordinator history filtered by StartDate=$StartDate (remaining: $remaining)" -ForegroundColor Cyan
	}
}

# Import combined psl.csv (with RVZ appended) to SOURCE_PROVIDER_TASKS_HISTORY
Write-Host "Importing combined psl.csv (with RVZ appended) to SOURCE_PROVIDER_TASKS_HISTORY..."
if (Test-Path "$PSScriptRoot/../downloads/psl.csv") {
	$output = python "$PSScriptRoot/../src/utils/csv_to_sql.py" "$PSScriptRoot/../downloads/psl.csv" -s $DatabasePath -t "SOURCE_PROVIDER_TASKS_HISTORY" --skip-empty-columns 2>&1
	if ($LASTEXITCODE -ne 0) {
		Write-Host "ERROR: Python import failed for psl.csv: $($output)" -ForegroundColor Red
		exit 1
	}
	$rowCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM SOURCE_PROVIDER_TASKS_HISTORY;" 2>$null
	if (-not $rowCount -or $rowCount -eq 0) {
		Write-Host "WARNING: Table SOURCE_PROVIDER_TASKS_HISTORY was created but is empty after import!" -ForegroundColor Yellow
	}
 else {
		Write-Host "Provider history imported ($rowCount rows)"
	}
	# Apply strict StartDate filter on DOS
	if ($StartDate -and $StartDate -match '^\d{4}-\d{2}-\d{2}$') {
		$sqlProv = @"
DELETE FROM SOURCE_PROVIDER_TASKS_HISTORY
WHERE (
  CASE
    WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
    WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER))
    ELSE NULL
  END
) < '$StartDate';
"@
		sqlite3 $DatabasePath $sqlProv 2>$null
		$remainingProv = sqlite3 $DatabasePath "SELECT COUNT(*) FROM SOURCE_PROVIDER_TASKS_HISTORY;" 2>$null
		Write-Host "Provider history filtered by StartDate=$StartDate (remaining: $remainingProv)" -ForegroundColor Cyan
	}
}

# If explicit files are provided, process only those
if ($Files.Count -gt 0) {
	Write-Host "Importing specified files only..." -ForegroundColor Cyan
	foreach ($file in $Files) {
		$base = Split-Path $file -Leaf
		if ($base -match 'coordinator_tasks_(\d{4}_\d{2})\.csv') {
			if (-not $Providers) {
				$m = $matches[1]
				$table = "SOURCE_CM_TASKS_${m}"
				Write-Host "Importing coordinator data for $m..."
				$output = python "$PSScriptRoot/../src/utils/csv_to_sql.py" $file -s $DatabasePath -t $table --skip-empty-columns 2>&1
				if ($LASTEXITCODE -ne 0) {
					Write-Host "ERROR: Python import failed for $($file): $($output)" -ForegroundColor Red
					exit 1
				}
				$rowCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $table;" 2>$null
				if (-not $rowCount -or $rowCount -eq 0) {
					Write-Host "WARNING: Table $table was created but is empty after import!" -ForegroundColor Yellow
				}
				else {
					Write-Host "Coordinator data imported to $table ($rowCount rows)"
				}
				if ($StartDate -and $StartDate -match '^\d{4}-\d{2}-\d{2}$') {
					$sql = @"
DELETE FROM $table WHERE (CASE WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER)) WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER)) ELSE NULL END) < '$StartDate';
"@
					sqlite3 $DatabasePath $sql 2>$null
					$rem = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $table;" 2>$null
					Write-Host "Filtered $table by StartDate=$StartDate (remaining: $rem)" -ForegroundColor Cyan
				}
			}
		}
		elseif ($base -match 'provider_tasks_(\d{4}_\d{2})\.csv') {
			if (-not $Coordinators) {
				$m = $matches[1]
				$table = "SOURCE_PSL_TASKS_${m}"
				Write-Host "Importing provider data for $m..."
				$output = python "$PSScriptRoot/../src/utils/csv_to_sql.py" $file -s $DatabasePath -t $table --skip-empty-columns 2>&1
				if ($LASTEXITCODE -ne 0) {
					Write-Host "ERROR: Python import failed for $($file): $($output)" -ForegroundColor Red
					exit 1
				}
				$rowCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $table;" 2>$null
				if (-not $rowCount -or $rowCount -eq 0) {
					Write-Host "WARNING: Table $table was created but is empty after import!" -ForegroundColor Yellow
				}
				else {
					Write-Host "Provider data imported to $table ($rowCount rows)"
				}
				if ($StartDate -and $StartDate -match '^\d{4}-\d{2}-\d{2}$') {
					$sql = @"
DELETE FROM $table WHERE (CASE WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER)) WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER)) ELSE NULL END) < '$StartDate';
"@
					sqlite3 $DatabasePath $sql 2>$null
					$rem = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $table;" 2>$null
					Write-Host "Filtered $table by StartDate=$StartDate (remaining: $rem)" -ForegroundColor Cyan
				}
			}
		}
		else {
			Write-Host "Unknown file type: $file" -ForegroundColor Red
		}
	}
	if (-not $SkipPatients) {
		Write-Host "Importing patient data..."
		python "$PSScriptRoot/../src/utils/csv_to_sql.py" "$PSScriptRoot/../downloads/patients/ZMO_Main.csv" -s $DatabasePath -t "SOURCE_PATIENT_DATA" --skip-empty-columns
		Write-Host "Patient data imported to SOURCE_PATIENT_DATA"
	}
	Write-Host ""
	Write-Host "Specified file import complete!"
}
elseif ($AllMonths) {
	Write-Host "Batch mode: Importing all available months..." -ForegroundColor Cyan
	$coordinatorFiles = Get-ChildItem "$PSScriptRoot/../downloads/monthly_CM/coordinator_tasks_*.csv"
	$providerFiles = Get-ChildItem "$PSScriptRoot/../downloads/monthly_PSL/provider_tasks_*.csv"
	$months = @()
	foreach ($f in $coordinatorFiles) {
		if ($f.Name -match 'coordinator_tasks_(\d{4}_\d{2})\.csv') { $months += $matches[1] }
	}
	foreach ($f in $providerFiles) {
		if ($f.Name -match 'provider_tasks_(\d{4}_\d{2})\.csv') { $months += $matches[1] }
	}
	$months = $months | Sort-Object -Unique
	foreach ($m in $months) {
		if ($Coordinators -or (-not $Providers)) {
			Write-Host "Importing coordinator data for $m..."
			$coordinatorFile = "$PSScriptRoot/../downloads/monthly_CM/coordinator_tasks_${m}.csv"
			$coordinatorTable = "SOURCE_CM_TASKS_${m}"
			$output = python "$PSScriptRoot/../src/utils/csv_to_sql.py" $coordinatorFile -s $DatabasePath -t $coordinatorTable --skip-empty-columns 2>&1
			if ($LASTEXITCODE -ne 0) {
				Write-Host "ERROR: Python import failed for $($coordinatorFile): $($output)" -ForegroundColor Red
				exit 1
			}
			$rowCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $coordinatorTable;" 2>$null
			if (-not $rowCount -or $rowCount -eq 0) {
				Write-Host "WARNING: Table $coordinatorTable was created but is empty after import!" -ForegroundColor Yellow
			}
			else {
				Write-Host "Coordinator data imported to $coordinatorTable ($rowCount rows)"
			}
			if ($StartDate -and $StartDate -match '^\d{4}-\d{2}-\d{2}$') {
				$sql = @"
DELETE FROM $coordinatorTable WHERE (CASE WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER)) WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER)) ELSE NULL END) < '$StartDate';
"@
				sqlite3 $DatabasePath $sql 2>$null
				$rem = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $coordinatorTable;" 2>$null
				Write-Host "Filtered $coordinatorTable by StartDate=$StartDate (remaining: $rem)" -ForegroundColor Cyan
			}
		}
		if ($Providers -or (-not $Coordinators)) {
			Write-Host "Importing provider data for $m..."
			$providerFile = "$PSScriptRoot/../downloads/monthly_PSL/provider_tasks_${m}.csv"
			$providerTable = "SOURCE_PSL_TASKS_${m}"
			$output = python "$PSScriptRoot/../src/utils/csv_to_sql.py" $providerFile -s $DatabasePath -t $providerTable --skip-empty-columns 2>&1
			if ($LASTEXITCODE -ne 0) {
				Write-Host "ERROR: Python import failed for $($providerFile): $($output)" -ForegroundColor Red
				exit 1
			}
			$rowCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $providerTable;" 2>$null
			if (-not $rowCount -or $rowCount -eq 0) {
				Write-Host "WARNING: Table $providerTable was created but is empty after import!" -ForegroundColor Yellow
			}
			else {
				Write-Host "Provider data imported to $providerTable ($rowCount rows)"
			}
			if ($StartDate -and $StartDate -match '^\d{4}-\d{2}-\d{2}$') {
				$sql = @"
DELETE FROM $providerTable WHERE (CASE WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER)) WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER)) ELSE NULL END) < '$StartDate';
"@
				sqlite3 $DatabasePath $sql 2>$null
				$rem = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $providerTable;" 2>$null
				Write-Host "Filtered $providerTable by StartDate=$StartDate (remaining: $rem)" -ForegroundColor Cyan
			}
		}
	}
	if (-not $SkipPatients) {
		Write-Host "Importing patient data..."
		python "$PSScriptRoot/../src/utils/csv_to_sql.py" "$PSScriptRoot/../downloads/patients/ZMO_Main.csv" -s $DatabasePath -t "SOURCE_PATIENT_DATA" --skip-empty-columns
		Write-Host "Patient data imported to SOURCE_PATIENT_DATA"
	}
	Write-Host ""
	Write-Host "Batch database import complete!"
}
else {
	Write-Host "Current month for import: $YearMonth" -ForegroundColor Cyan
	Write-Host "Starting database import process..."
	Write-Host "Database: $DatabasePath (staging mode)" -ForegroundColor Yellow

		if ($Coordinators -or (-not $Providers)) {
		$coordinatorFile = "$PSScriptRoot/../downloads/monthly_CM/coordinator_tasks_${YearMonth}.csv"
		$coordinatorTable = "SOURCE_CM_TASKS_${YearMonth}"
		Write-Host "Importing coordinator data for $YearMonth..."
		$output = python "$PSScriptRoot/../src/utils/csv_to_sql.py" $coordinatorFile -s $DatabasePath -t $coordinatorTable --skip-empty-columns 2>&1
		if ($LASTEXITCODE -ne 0) {
			Write-Host "ERROR: Python import failed for $($coordinatorFile): $($output)" -ForegroundColor Red
			exit 1
		}
		$rowCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $coordinatorTable;" 2>$null
		if (-not $rowCount -or $rowCount -eq 0) {
			Write-Host "WARNING: Table $coordinatorTable was created but is empty after import!" -ForegroundColor Yellow
		}
		else {
			Write-Host "Coordinator data imported to $coordinatorTable ($rowCount rows)"
		}
		if ($StartDate -and $StartDate -match '^\d{4}-\d{2}-\d{2}$') {
			$sql = @"
DELETE FROM $coordinatorTable WHERE (CASE WHEN "Date Only" GLOB '??/??/????' THEN substr("Date Only",7,4) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER)) WHEN "Date Only" GLOB '??/??/??' THEN '20' || substr("Date Only",7,2) || '-' || printf('%02d', CAST(substr("Date Only",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("Date Only",4,2) AS INTEGER)) ELSE NULL END) < '$StartDate';
"@
			sqlite3 $DatabasePath $sql 2>$null
			$rem = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $coordinatorTable;" 2>$null
			Write-Host "Filtered $coordinatorTable by StartDate=$StartDate (remaining: $rem)" -ForegroundColor Cyan
		}
	}
		if ($Providers -or (-not $Coordinators)) {
		$providerFile = "$PSScriptRoot/../downloads/monthly_PSL/provider_tasks_${YearMonth}.csv"
		$providerTable = "SOURCE_PSL_TASKS_${YearMonth}"
		Write-Host "Importing provider data for $YearMonth..."
		$output = python "$PSScriptRoot/../src/utils/csv_to_sql.py" $providerFile -s $DatabasePath -t $providerTable --skip-empty-columns 2>&1
		if ($LASTEXITCODE -ne 0) {
			Write-Host "ERROR: Python import failed for $($providerFile): $($output)" -ForegroundColor Red
			exit 1
		}
		$rowCount = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $providerTable;" 2>$null
		if (-not $rowCount -or $rowCount -eq 0) {
			Write-Host "WARNING: Table $providerTable was created but is empty after import!" -ForegroundColor Yellow
		}
		else {
			Write-Host "Provider data imported to $providerTable ($rowCount rows)"
		}
		if ($StartDate -and $StartDate -match '^\d{4}-\d{2}-\d{2}$') {
			$sql = @"
DELETE FROM $providerTable WHERE (CASE WHEN "DOS" GLOB '??/??/????' THEN substr("DOS",7,4) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER)) WHEN "DOS" GLOB '??/??/??' THEN '20' || substr("DOS",7,2) || '-' || printf('%02d', CAST(substr("DOS",1,2) AS INTEGER)) || '-' || printf('%02d', CAST(substr("DOS",4,2) AS INTEGER)) ELSE NULL END) < '$StartDate';
"@
			sqlite3 $DatabasePath $sql 2>$null
			$rem = sqlite3 $DatabasePath "SELECT COUNT(*) FROM $providerTable;" 2>$null
			Write-Host "Filtered $providerTable by StartDate=$StartDate (remaining: $rem)" -ForegroundColor Cyan
		}
	}

	if (-not $SkipPatients) {
		Write-Host "Importing patient data..."
		python "$PSScriptRoot/../src/utils/csv_to_sql.py" "$PSScriptRoot/../downloads/patients/ZMO_Main.csv" -s $DatabasePath -t "SOURCE_PATIENT_DATA" --skip-empty-columns
		Write-Host "Patient data imported to SOURCE_PATIENT_DATA"
	}

	Write-Host ""
	Write-Host "Database import complete!"
}

Write-Host "Next steps:"
Write-Host "  1. Run SQL transformation scripts in src/sql/ (staging mode recommended)"
Write-Host "  2. Run: python ../src/utils/add_new_staff_mappings.py"
Write-Host "  3. Run: python ../src/utils/compare_csv_vs_database.py"
Write-Host ""
Write-Host "Usage:"
Write-Host "  .\3_import_to_database.ps1" -ForegroundColor Yellow
Write-Host "  .\3_import_to_database.ps1 -AllMonths" -ForegroundColor Yellow
Write-Host "  .\3_import_to_database.ps1 -SkipPatients" -ForegroundColor Yellow
Write-Host "  .\3_import_to_database.ps1 -Coordinators" -ForegroundColor Yellow
Write-Host "  .\3_import_to_database.ps1 -Providers" -ForegroundColor Yellow
Write-Host "  .\3_import_to_database.ps1 -Files <file1> <file2> ..." -ForegroundColor Yellow
Write-Host "  .\3_import_to_database.ps1 -StartDate <YYYY-MM-DD>" -ForegroundColor Yellow
Write-Host "-AllMonths: Import all available months (batch mode)"
Write-Host "-SkipPatients: Skip importing patient data"
Write-Host "-Coordinators: Only import coordinator data"
Write-Host "-Providers: Only import provider data"
Write-Host "-Files: Import only the specified files (auto-detects type by filename)"
Write-Host "-StartDate: Strict filter to include only rows with normalized date >= StartDate (YYYY-MM-DD)"