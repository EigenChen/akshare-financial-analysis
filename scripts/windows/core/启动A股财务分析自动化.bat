@echo off
chcp 65001 >nul
echo 正在启动A股财务分析自动化工具...
cd /d "%~dp0\..\..\.."
streamlit run "apps\a_share\a_share_pipeline_app.py"
pause
