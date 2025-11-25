@echo off
cd /d "D:\Git\myhealthteam2\Streamlit"
echo Auto-commit script started at %time% > scripts\autocommit.log
python scripts\autocommit.py >> scripts\autocommit.log 2>&1
echo Auto-commit script finished at %time% >> scripts\autocommit.log
echo. >> scripts\autocommit.log