$content = Get-Content 'd:\Git\myhealthteam2\Streamlit\sandbox\src\sql\populate_provider_coordinator_tasks_by_month.sql'
$content = $content -replace ' \{ YYYY_MM \}', '2025_07'
$content = $content -replace '\{YYYY_MM\}', '2025_07'
$content | Out-File -FilePath temp.sql -Encoding UTF8
cmd /c 'sqlite3 d:\Git\myhealthteam2\Streamlit\sandbox\production.db < temp.sql'
Remove-Item temp.sql