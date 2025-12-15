@echo off
chcp 65001 >nul
echo ========================================
echo   港股财务分析工具 - Streamlit Web 界面
echo ========================================
echo.
echo 正在启动应用...
echo.
streamlit run streamlit_app_hk.py
pause

