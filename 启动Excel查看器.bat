@echo off
chcp 65001 >nul
echo ========================================
echo  财务分析Excel查看器
echo  功能：上传Excel文件，查看数据表格和图表
echo ========================================
echo.
echo 正在启动 Streamlit 应用...
echo.
call "%~dp0scripts\windows\tools\启动Excel查看器.bat"
