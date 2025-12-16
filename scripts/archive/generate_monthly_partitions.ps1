param(
    [string]$DatabasePath = "production.db",
    [int]$StartYear = 2024,
    [int]$StartMonth = 1,
    [int]$EndYear = 2025,
    [int]$EndMonth = 12
)

function Get-MonthRange($sy, $sm, $ey, $em) {
    $months = @()
    $year = $sy; $month = $sm
    while (($year -lt $ey) -or ($year -eq $ey -and $month -le $em)) {
        $months += @{ Year = $year; Month = $month }
        $month += 1
        if ($month -gt 12) { $month = 1; $year += 1 }
    }
    return $months
}

$months = Get-MonthRange -sy $StartYear -sm $StartMonth -ey $EndYear -em $EndMonth

foreach ($m in $months) {
    $y = $m.Year; $mm = $m.Month.ToString('D2')
    $co_table = "coordinator_tasks_${y}_${mm}"
    $pr_table = "provider_tasks_${y}_${mm}"

    Write-Host "Creating partition tables: $co_table and $pr_table in $DatabasePath"
    $sql = @"
    BEGIN;
    CREATE TABLE IF NOT EXISTS $co_table AS SELECT * FROM coordinator_tasks WHERE 0;
    CREATE TABLE IF NOT EXISTS $pr_table AS SELECT * FROM provider_tasks WHERE 0;
    COMMIT;
"@
    sqlite3 $DatabasePath "$sql"
}

Write-Host "Partition generation complete."
