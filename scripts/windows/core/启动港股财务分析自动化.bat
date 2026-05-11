@echo off
chcp 65001 >nul
echo 正在启动港股财务分析自动化工具...
cd /d "%~dp0\..\..\.."
streamlit run "apps\hk\hk_pipeline_app.py"
pause
