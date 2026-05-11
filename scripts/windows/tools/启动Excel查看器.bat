@echo off
chcp 65001 >nul
echo 正在启动财务分析Excel查看器...
cd /d "%~dp0\..\..\.."
streamlit run "apps\tools\excel_viewer_app.py"
pause
