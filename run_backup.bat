@echo off
cd /d "D:\Git\myhealthteam2\Streamlit"
PowerShell -ExecutionPolicy Bypass -File "scripts\backup_now.ps1"
echo Backup completed at %date% %time%