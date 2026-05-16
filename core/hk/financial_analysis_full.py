# -*- coding: utf-8 -*-
"""
港股财务分析(完整版)

基于AKShare港股接口生成完整的9个sheet财务分析报告
复用A股的计算逻辑,因为字段名已经统一映射
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# 检查是否在Streamlit环境中运行
def is_streamlit_env():
    """检查是否在Streamlit环境中运行"""
    try:
        import streamlit
        return True
    except ImportError:
        # 检查sys.modules中是否有streamlit相关模块
        return any('streamlit' in str(mod) for mod in sys.modules.keys())

# 只在非Streamlit环境且Windows系统下才替换stdout
if sys.platform == 'win32' and not is_streamlit_env():
    try:
        import io
        # 检查stdout是否已经有buffer属性(可能已经被替换)
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except (AttributeError, ValueError, TypeError):
        # 如果stdout已经被替换或无法替换,忽略错误
        pass

# 导入港股适配层
from core.hk.financial_adapter import (
    get_hk_annual_data, extract_year_data_hk,
    get_value_from_row_hk, get_hk_symbol_name,
    get_hk_employee_count, get_hk_employee_count_by_year,
    get_fiscal_year_end
)

# 模块级变量:存储当前处理的股票代码和年结日
_current_symbol = None
_current_fiscal_year_end = None

# 导入A股计算函数(字段名已统一,可以直接复用)
import importlib.util
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("financial_analysis", ROOT / "core/a_share/financial_analysis.py")
financial_analysis = importlib.util.module_from_spec(spec)
sys.modules["financial_analysis"] = financial_analysis
spec.loader.exec_module(financial_analysis)

# 导入A股的计算函数
calculate_revenue_metrics = financial_analysis.calculate_revenue_metrics
calculate_expense_metrics = financial_analysis.calculate_expense_metrics
calculate_growth_metrics = financial_analysis.calculate_growth_metrics
calculate_balance_sheet_metrics = financial_analysis.calculate_balance_sheet_metrics
calculate_wc_metrics = financial_analysis.calculate_wc_metrics
calculate_fixed_asset_metrics = financial_analysis.calculate_fixed_asset_metrics
calculate_roi_metrics = financial_analysis.calculate_roi_metrics
calculate_asset_turnover_metrics = financial_analysis.calculate_asset_turnover_metrics
calculate_per_capita_metrics = financial_analysis.calculate_per_capita_metrics
save_to_excel = financial_analysis.save_to_excel

# 但是需要替换数据获取函数
def get_annual_data_hk_wrapper(symbol, start_year=2015, end_year=2024):
    """
    港股数据获取包装函数,接口与A股一致
    同时设置当前处理的股票代码和年结日
    """
    global _current_symbol, _current_fiscal_year_end
    _current_symbol = symbol
    _current_fiscal_year_end = get_fiscal_year_end(symbol)

    # 打印年结日信息(方便调试)
    month, day = _current_fiscal_year_end
    if month != 12 or day != 31:
        print(f"[INFO] {symbol} 年结日为 {month:02d}-{day:02d}(非自然年)")

    return get_hk_annual_data(symbol, start_year, end_year)

def extract_year_data_hk_wrapper(df, year, date_col_name='REPORT_DATE'):
    """
    港股年份数据提取包装函数,接口与A股一致
    使用模块级变量获取当前股票的年结日
    """
    global _current_symbol, _current_fiscal_year_end
    return extract_year_data_hk(df, year, date_col_name,
                                fiscal_year_end=_current_fiscal_year_end,
                                symbol=_current_symbol)

def get_value_from_row_hk_wrapper(row, column_name, default="-", return_numeric=True):
    """
    港股字段值获取包装函数,接口与A股一致
    """
    return get_value_from_row_hk(row, column_name, default, return_numeric)

# 临时替换A股模块中的函数(仅用于港股计算)
original_get_annual_data = financial_analysis.get_annual_data
original_extract_year_data = financial_analysis.extract_year_data
original_get_value_from_row = financial_analysis.get_value_from_row

financial_analysis.get_annual_data = get_annual_data_hk_wrapper
financial_analysis.extract_year_data = extract_year_data_hk_wrapper
financial_analysis.get_value_from_row = get_value_from_row_hk_wrapper

# 港股员工数:只有最新年份有数据,历史年份留空
# 替换 calculate_per_capita_metrics 为港股专用版本
import pandas as pd

def calculate_per_capita_metrics_hk(symbol, start_year, end_year, employee_csv_path=None):
    """
    港股人均数据:历史年份留空,只有最新年份有员工数
    """
    print("\n" + "=" * 80)
    print(f"开始计算 {symbol} 的人均数据（{start_year}-{end_year}）")
    print("=" * 80)

    data = get_hk_annual_data(symbol, start_year, end_year)
    if data['balance_sheet'] is None or data['profit'] is None or data['cash_flow'] is None:
        print("✗ 资产负债表、利润表或现金流量表数据获取不完整，无法计算")
        return None

    # 按年获取员工数(只有最新年份有值,历史年份为None)
    emp_by_year = get_hk_employee_count_by_year(symbol, start_year, end_year)
    has_any = any(v is not None for v in emp_by_year.values())
    if not has_any:
        print("⚠ 无法获取任何年份的员工人数，人均数据将显示为 '-'")

    metrics = {'科目': []}
    for year in range(start_year, end_year + 1):
        metrics[str(year)] = []

    metrics['科目'] = ['人数', '人均收入（万元）', '人均归母净利润（万元）', '人均扣非净利润（万元）', '人均薪酬（万元）', '人均固定资产（万元）']
    for year in range(start_year, end_year + 1):
        for _ in range(6):
            metrics[str(year)].append("-")

    if not has_any:
        return pd.DataFrame(metrics)

    for year in range(start_year, end_year + 1):
        employee_count = emp_by_year.get(year)
        if employee_count is None:
            continue  # 历史年份留空

        profit_row = extract_year_data_hk(data['profit'], year)
        balance_row = extract_year_data_hk(data['balance_sheet'], year)
        if profit_row is None or balance_row is None:
            continue

        revenue = get_value_from_row_hk(profit_row, 'OPERATE_INCOME', "-")
        parent_profit = get_value_from_row_hk(profit_row, 'PARENT_NETPROFIT', "-")
        if revenue == "-" or parent_profit == "-":
            continue

        year_idx = year - start_year
        metrics[str(year)][0] = employee_count
        metrics[str(year)][1] = round(revenue / employee_count * 10000, 2)  # 亿元→万元
        metrics[str(year)][2] = round(parent_profit / employee_count * 10000, 2)
        metrics[str(year)][3] = "-"  # 扣非:港股不披露

        # 人均薪酬:应付职工薪酬/人数
        staff_payable = get_value_from_row_hk(balance_row, 'STAFF_SALARY_PAYABLE', 0)
        if staff_payable == "-":
            staff_payable = 0
        metrics[str(year)][4] = round(staff_payable / employee_count * 10000, 2)

        # 人均固定资产
        fixed_asset = get_value_from_row_hk(balance_row, 'FIXED_ASSET', "-")
        if fixed_asset != "-":
            metrics[str(year)][5] = round(fixed_asset / employee_count * 10000, 2)

    return pd.DataFrame(metrics)

# 替换人均数据计算
calculate_per_capita_metrics = calculate_per_capita_metrics_hk

def main():
    """
    主函数
    """
    # 港股代码和年份范围
    symbol = "00700"  # 腾讯控股
    start_year = 2020
    end_year = 2024

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # 获取股票名称
    company_name = get_hk_symbol_name(symbol)
    print(f"股票代码: {symbol}")
    print(f"公司名称: {company_name}")
    print(f"分析年份: {start_year}-{end_year}")
    print(f"货币单位: 港币（HKD）\n")

    # 计算营收基本数据
    print("\n" + "=" * 80)
    result_df = calculate_revenue_metrics(symbol, start_year, end_year)
    if result_df is not None and not result_df.empty:
        print("\n营收基本数据:")
        print(result_df.to_string(index=False))
        save_to_excel(result_df, symbol, company_name, start_year, end_year, '营收基本数据', timestamp=timestamp)

    # 计算费用构成数据
    expense_df = calculate_expense_metrics(symbol, start_year, end_year)
    if expense_df is not None and not expense_df.empty:
        print("\n费用构成数据:")
        print(expense_df.to_string(index=False))
        save_to_excel(expense_df, symbol, company_name, start_year, end_year, '费用构成', timestamp=timestamp)

    # 计算增长率数据
    growth_df = calculate_growth_metrics(symbol, start_year, end_year)
    if growth_df is not None and not growth_df.empty:
        print("\n增长率数据:")
        print(growth_df.to_string(index=False))
        save_to_excel(growth_df, symbol, company_name, start_year, end_year, '增长', timestamp=timestamp)

    # 计算资产负债数据
    balance_df = calculate_balance_sheet_metrics(symbol, start_year, end_year)
    if balance_df is not None and not balance_df.empty:
        print("\n资产负债数据:")
        print(balance_df.to_string(index=False))
        save_to_excel(balance_df, symbol, company_name, start_year, end_year, '资产负债', timestamp=timestamp)

    # 计算WC分析数据
    wc_df = calculate_wc_metrics(symbol, start_year, end_year)
    if wc_df is not None and not wc_df.empty:
        print("\nWC分析数据:")
        print(wc_df.to_string(index=False))
        save_to_excel(wc_df, symbol, company_name, start_year, end_year, 'WC分析', timestamp=timestamp)

    # 计算固定资产投入分析数据
    fixed_asset_df = calculate_fixed_asset_metrics(symbol, start_year, end_year)
    if fixed_asset_df is not None and not fixed_asset_df.empty:
        print("\n固定资产投入分析数据:")
        print(fixed_asset_df.to_string(index=False))
        save_to_excel(fixed_asset_df, symbol, company_name, start_year, end_year, '固定资产投入分析', timestamp=timestamp)

    # 计算收益率和杜邦分析数据
    roi_df = calculate_roi_metrics(symbol, start_year, end_year)
    if roi_df is not None and not roi_df.empty:
        print("\n收益率和杜邦分析数据:")
        print(roi_df.to_string(index=False))
        save_to_excel(roi_df, symbol, company_name, start_year, end_year, '收益率和杜邦分析', timestamp=timestamp)

    # 计算资产周转数据
    asset_turnover_df = calculate_asset_turnover_metrics(symbol, start_year, end_year)
    if asset_turnover_df is not None and not asset_turnover_df.empty:
        print("\n资产周转数据:")
        print(asset_turnover_df.to_string(index=False))
        save_to_excel(asset_turnover_df, symbol, company_name, start_year, end_year, '资产周转', timestamp=timestamp)

    # 计算人均数据（港股可能缺少员工人数数据）
    per_capita_df = calculate_per_capita_metrics(symbol, start_year, end_year, employee_csv_path=None)
    if per_capita_df is not None and not per_capita_df.empty:
        print("\n人均数据:")
        print(per_capita_df.to_string(index=False))
        save_to_excel(per_capita_df, symbol, company_name, start_year, end_year, '人均数据', timestamp=timestamp)

    # 添加港股特有说明到 Excel
    filename = f"{company_name}_{start_year}-{end_year}_港股财务分析_{timestamp}.xlsx"
    filepath = os.path.join("output", filename)
    if os.path.exists(filepath):
        append_hk_notes_to_excel(filepath)
        print(f"\n{'='*80}")
        print(f"[OK] 所有数据已保存到: {filepath}")
        print(f"包含9个sheet（部分sheet可能因数据缺失而显示为'-'）")
        print(f"货币单位: 港币（HKD）")
        print(f"{'='*80}")


def append_hk_notes_to_excel(filepath: str):
    """
    在生成的港股 Excel 文件中添加港股特有说明
    在第一个 Sheet 的最后几行添加注释
    """
    try:
        from openpyxl import load_workbook
        wb = load_workbook(filepath)

        # 港股特有差异说明
        notes = [
            "",
            "=== 港股报告特有说明 ===",
            "1. 货币单位：港币（HKD），非人民币",
            "2. 扣非净利润：港股不披露非经常性损益，该科目显示为'不适用'",
            "3. 研发费用：港股通常合并在'行政开支'中，不单独披露",
            "4. 应付票据：港股报表格式不同，通常无此科目",
            "5. 员工人数：港股接口只返回最新值，历史年份显示为'-'",
            "6. 人均数据：只有最新年份有员工数，历史年份人均指标显示为'-'",
            "7. 人均薪酬：港股资产负债表无'应付职工薪酬'科目，显示为'-'",
            "8. 年结日：部分港股公司非12月31日年结，已自动处理",
            "9. '-' 表示该科目在港股报表中无法获取或无法计算",
        ]

        for ws in wb.worksheets:
            max_row = ws.max_row + 2
            for i, note in enumerate(notes):
                ws.cell(row=max_row + i, column=1, value=note)

        wb.save(filepath)
        print("[OK] 已添加港股特有说明到 Excel 文件")

    except ImportError:
        print("[WARNING] openpyxl 未安装，无法添加港股说明")
    except Exception as e:
        print(f"[WARNING] 添加港股说明失败: {e}")

if __name__ == "__main__":
    main()

