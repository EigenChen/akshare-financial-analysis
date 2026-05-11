@echo off
chcp 65001 >nul
echo ========================================
echo  统一财务工具（A股 + 港股）
echo ========================================
echo.
echo 正在启动 Streamlit 应用...
echo.
cd /d "%~dp0\..\..\.."
streamlit run "apps\portal\unified_portal.py"
pause
