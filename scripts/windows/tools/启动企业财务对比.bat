@echo off
chcp 65001 >nul
echo 正在启动企业财务对比工具...
cd /d "%~dp0\..\..\.."
streamlit run "apps\tools\company_compare_app.py"
pause
