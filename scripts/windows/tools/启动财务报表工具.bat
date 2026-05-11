@echo off
chcp 65001 >nul
echo 正在启动财务报表下载工具...
cd /d "%~dp0\..\..\.."
streamlit run "apps\tools\report_downloader_app.py"
pause
