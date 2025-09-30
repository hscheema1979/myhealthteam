$months = @("2025_09")

foreach ($month in $months) {
    $content = Get-Content 'd:\Git\myhealthteam2\Streamlit\sandbox\src\sql\populate_provider_coordinator_tasks_by_month.sql'
    $content = $content -replace '\{YYYY_MM\}', $month
    $content | Out-File -FilePath "temp_$month.sql" -Encoding UTF8
    cmd /c "sqlite3 d:\Git\myhealthteam2\Streamlit\sandbox\production.db < temp_$month.sql"
    Remove-Item "temp_$month.sql"
    Write-Host "Processed $month"
}