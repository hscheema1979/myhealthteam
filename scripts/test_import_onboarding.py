import importlib, sys
sys.path.append(r'd:\Git\myhealthteam2\Streamlit')
mod = importlib.import_module('src.dashboards.onboarding_dashboard')
print('Imported onboarding_dashboard OK')
