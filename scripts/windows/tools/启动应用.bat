@echo off
chcp 65001 >nul
echo 正在启动财务分析工具...
cd /d "%~dp0\..\..\.."
streamlit run "apps\a_share\a_share_streamlit_app.py"
pause
