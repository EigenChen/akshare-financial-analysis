@echo off
chcp 65001 >nul
echo ========================================
echo  统一财务工具（A股 + 港股）
echo  功能：财务分析 / 报表下载 / 员工数量提取 / 年报PDF下载
echo ========================================
echo.
echo 正在启动 Streamlit 应用...
echo.
streamlit run "统一财务工具.py"
pause

