# -*- coding: utf-8 -*-
"""
港股财务分析

基于AKShare港股接口生成财务分析报告
注意：由于港股接口返回的数据有限，只能生成部分sheet
"""

import akshare as ak
import pandas as pd
import os
import time
from datetime import datetime
from typing import Optional, Dict
import sys

# 导入港股适配层
from hk_financial_adapter import (
    is_hk_stock, get_hk_annual_data, extract_year_data_hk, 
    get_value_from_row_hk, get_hk_symbol_name
)

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def calculate_hk_revenue_metrics(symbol: str, start_year: int, end_year: int):
    """
    计算港股营收基本数据指标
    
    参数:
        symbol: 港股代码
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        包含所有指标数据的DataFrame
    """
    print("=" * 80)
    print(f"开始计算 {symbol} 的营收基本数据（{start_year}-{end_year}）")
    print("=" * 80)
    
    # 获取数据
    data = get_hk_annual_data(symbol, start_year, end_year)
    
    if data['analysis_indicator'] is None:
        print("[FAIL] 数据获取不完整，无法计算")
        return None
    
    # 准备结果数据
    metrics = {
        '科目': [],
    }
    
    # 初始化年份列
    for year in range(start_year, end_year + 1):
        metrics[str(year)] = []
    
    # 初始化科目名称
    metrics['科目'] = [
        '收入（亿元）',
        '归母净利润（亿元）',
        '净利润率（%）',
        '毛利率（%）',
        '净利率（%）',
        'ROE（%）',
        'ROA（%）',
        'ROIC（%）',
    ]
    
    # 初始化所有年份的数据列表
    for year in range(start_year, end_year + 1):
        for _ in range(len(metrics['科目'])):
            metrics[str(year)].append("-")
    
    # 逐年计算指标
    for year in range(start_year, end_year + 1):
        print(f"\n处理 {year} 年数据...")
        
        # 获取该年份的数据
        indicator_row = extract_year_data_hk(data['analysis_indicator'], year)
        
        if indicator_row is None:
            print(f"  [WARNING] {year} 年数据缺失")
            continue
        
        # 1. 收入（亿元）
        revenue = get_value_from_row_hk(indicator_row, 'OPERATE_INCOME', "-")
        if revenue == "-":
            print(f"  [WARNING] {year} 年营业收入数据缺失")
            continue
        metrics[str(year)][0] = revenue
        
        # 2. 归母净利润（亿元）
        parent_net_profit = get_value_from_row_hk(indicator_row, 'HOLDER_PROFIT', "-")
        if parent_net_profit == "-":
            print(f"  [WARNING] {year} 年归母净利润数据缺失")
            continue
        metrics[str(year)][1] = parent_net_profit
        
        # 3. 净利润率（%）
        if revenue != "-" and revenue != 0:
            net_profit_margin = round((parent_net_profit / revenue * 100), 2)
            metrics[str(year)][2] = net_profit_margin
        
        # 4. 毛利率（%）
        gross_profit_ratio = get_value_from_row_hk(indicator_row, 'GROSS_PROFIT_RATIO', "-", is_percentage=True)
        if gross_profit_ratio != "-":
            metrics[str(year)][3] = gross_profit_ratio
        
        # 5. 净利率（%）
        net_profit_ratio = get_value_from_row_hk(indicator_row, 'NET_PROFIT_RATIO', "-", is_percentage=True)
        if net_profit_ratio != "-":
            metrics[str(year)][4] = net_profit_ratio
        
        # 6. ROE（%）
        roe = get_value_from_row_hk(indicator_row, 'ROE_YEARLY', "-", is_percentage=True)
        if roe == "-":
            roe = get_value_from_row_hk(indicator_row, 'ROE_AVG', "-", is_percentage=True)
        if roe != "-":
            metrics[str(year)][5] = roe
        
        # 7. ROA（%）
        roa = get_value_from_row_hk(indicator_row, 'ROA', "-", is_percentage=True)
        if roa != "-":
            metrics[str(year)][6] = roa
        
        # 8. ROIC（%）
        roic = get_value_from_row_hk(indicator_row, 'ROIC_YEARLY', "-", is_percentage=True)
        if roic != "-":
            metrics[str(year)][7] = roic
        
        print(f"  [OK] {year} 年数据计算完成")
    
    # 创建DataFrame
    result_df = pd.DataFrame(metrics)
    return result_df

def calculate_hk_growth_metrics(symbol: str, start_year: int, end_year: int):
    """
    计算港股增长率指标
    """
    print("\n" + "=" * 80)
    print(f"开始计算 {symbol} 的增长率数据（{start_year}-{end_year}）")
    print("=" * 80)
    
    data = get_hk_annual_data(symbol, start_year, end_year)
    
    if data['analysis_indicator'] is None:
        print("[FAIL] 数据获取不完整，无法计算")
        return None
    
    metrics = {
        '科目': [],
    }
    
    for year in range(start_year, end_year + 1):
        metrics[str(year)] = []
    
    metrics['最近5年'] = []
    metrics['最近3年'] = []
    
    metrics['科目'] = [
        '收入增长率（%）',
        '归母净利润增长率（%）'
    ]
    
    # 初始化数据
    for year in range(start_year, end_year + 1):
        metrics[str(year)].append("-")
        metrics[str(year)].append("-")
    
    metrics['最近5年'].append("-")
    metrics['最近5年'].append("-")
    metrics['最近3年'].append("-")
    metrics['最近3年'].append("-")
    
    # 存储每年的值
    revenue_values = {}
    profit_values = {}
    
    # 获取所有年份的数据
    for year in range(start_year, end_year + 1):
        indicator_row = extract_year_data_hk(data['analysis_indicator'], year)
        if indicator_row is None:
            continue
        
        revenue = get_value_from_row_hk(indicator_row, 'OPERATE_INCOME', "-")
        if revenue != "-":
            revenue_values[year] = revenue
        
        profit = get_value_from_row_hk(indicator_row, 'HOLDER_PROFIT', "-")
        if profit != "-":
            profit_values[year] = profit
    
    # 计算各年份的增长率
    for year in range(start_year, end_year + 1):
        if year == start_year:
            continue
        
        # 收入增长率
        if year in revenue_values and (year - 1) in revenue_values:
            prev_revenue = revenue_values[year - 1]
            curr_revenue = revenue_values[year]
            if prev_revenue != 0:
                revenue_growth = round(((curr_revenue - prev_revenue) / prev_revenue * 100), 2)
                metrics[str(year)][0] = revenue_growth
        
        # 归母净利润增长率
        if year in profit_values and (year - 1) in profit_values:
            prev_profit = profit_values[year - 1]
            curr_profit = profit_values[year]
            if prev_profit != 0:
                profit_growth = round(((curr_profit - prev_profit) / prev_profit * 100), 2)
                metrics[str(year)][1] = profit_growth
    
    # 计算复合增长率
    if end_year in revenue_values and (end_year - 5) in revenue_values:
        start_revenue = revenue_values[end_year - 5]
        end_revenue = revenue_values[end_year]
        if start_revenue > 0 and end_revenue > 0:
            ratio = end_revenue / start_revenue
            if ratio > 0:
                cagr_5_revenue = (pow(ratio, 1/5) - 1) * 100
                if not isinstance(cagr_5_revenue, complex):
                    metrics['最近5年'][0] = round(cagr_5_revenue, 2)
    
    if end_year in profit_values and (end_year - 5) in profit_values:
        start_profit = profit_values[end_year - 5]
        end_profit = profit_values[end_year]
        if start_profit > 0 and end_profit > 0:
            ratio = end_profit / start_profit
            if ratio > 0:
                cagr_5_profit = (pow(ratio, 1/5) - 1) * 100
                if not isinstance(cagr_5_profit, complex):
                    metrics['最近5年'][1] = round(cagr_5_profit, 2)
    
    if end_year in revenue_values and (end_year - 3) in revenue_values:
        start_revenue = revenue_values[end_year - 3]
        end_revenue = revenue_values[end_year]
        if start_revenue > 0 and end_revenue > 0:
            ratio = end_revenue / start_revenue
            if ratio > 0:
                cagr_3_revenue = (pow(ratio, 1/3) - 1) * 100
                if not isinstance(cagr_3_revenue, complex):
                    metrics['最近3年'][0] = round(cagr_3_revenue, 2)
    
    if end_year in profit_values and (end_year - 3) in profit_values:
        start_profit = profit_values[end_year - 3]
        end_profit = profit_values[end_year]
        if start_profit > 0 and end_profit > 0:
            ratio = end_profit / start_profit
            if ratio > 0:
                cagr_3_profit = (pow(ratio, 1/3) - 1) * 100
                if not isinstance(cagr_3_profit, complex):
                    metrics['最近3年'][1] = round(cagr_3_profit, 2)
    
    columns_order = ['科目'] + [str(year) for year in range(start_year, end_year + 1)] + ['最近5年', '最近3年']
    result_df = pd.DataFrame(metrics)
    result_df = result_df[columns_order]
    
    return result_df

def calculate_hk_roi_metrics(symbol: str, start_year: int, end_year: int):
    """
    计算港股收益率和杜邦分析指标
    """
    print("\n" + "=" * 80)
    print(f"开始计算 {symbol} 的收益率和杜邦分析数据（{start_year}-{end_year}）")
    print("=" * 80)
    
    data = get_hk_annual_data(symbol, start_year, end_year)
    
    if data['analysis_indicator'] is None:
        print("[FAIL] 数据获取不完整，无法计算")
        return None
    
    metrics = {
        '科目': [],
    }
    
    for year in range(start_year, end_year + 1):
        metrics[str(year)] = []
    
    metrics['科目'] = [
        'ROE(%)',
        'ROA(%)',
        'ROIC(%)',
        '销售净利率(%)',
    ]
    
    for year in range(start_year, end_year + 1):
        for _ in range(len(metrics['科目'])):
            metrics[str(year)].append("-")
    
    for year in range(start_year, end_year + 1):
        indicator_row = extract_year_data_hk(data['analysis_indicator'], year)
        if indicator_row is None:
            continue
        
        # ROE
        roe = get_value_from_row_hk(indicator_row, 'ROE_YEARLY', "-", is_percentage=True)
        if roe == "-":
            roe = get_value_from_row_hk(indicator_row, 'ROE_AVG', "-", is_percentage=True)
        if roe != "-":
            metrics[str(year)][0] = roe
        
        # ROA
        roa = get_value_from_row_hk(indicator_row, 'ROA', "-", is_percentage=True)
        if roa != "-":
            metrics[str(year)][1] = roa
        
        # ROIC
        roic = get_value_from_row_hk(indicator_row, 'ROIC_YEARLY', "-", is_percentage=True)
        if roic != "-":
            metrics[str(year)][2] = roic
        
        # 销售净利率
        net_profit_ratio = get_value_from_row_hk(indicator_row, 'NET_PROFIT_RATIO', "-", is_percentage=True)
        if net_profit_ratio != "-":
            metrics[str(year)][3] = net_profit_ratio
    
    result_df = pd.DataFrame(metrics)
    return result_df

def save_to_excel_hk(df, symbol, company_name, start_year, end_year, sheet_name, output_dir="output", timestamp=None):
    """
    保存港股数据到Excel文件
    """
    if df is None or df.empty:
        print(f"[FAIL] 没有数据可保存到 {sheet_name}")
        return None
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    symbol_clean = symbol.replace('.HK', '')
    filename = f"{company_name}_{start_year}-{end_year}_港股财务分析_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    try:
        if os.path.exists(filepath):
            time.sleep(0.1)
            with pd.ExcelWriter(filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"[OK] {sheet_name} 已追加/更新到现有Excel文件")
        else:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"[OK] 已创建新Excel文件")
        
        time.sleep(0.1)
        print(f"  文件路径: {filepath}")
        print(f"  Sheet名称: {sheet_name}")
        return filepath
        
    except Exception as e:
        print(f"[FAIL] 保存Excel文件失败: {e}")
        import traceback
        traceback.print_exc()
        return None

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
    print(f"分析年份: {start_year}-{end_year}\n")
    
    # 计算营收基本数据
    revenue_df = calculate_hk_revenue_metrics(symbol, start_year, end_year)
    if revenue_df is not None and not revenue_df.empty:
        print("\n" + "=" * 80)
        print(f"营收基本数据（{start_year}-{end_year}）")
        print("=" * 80)
        print(revenue_df.to_string(index=False))
        save_to_excel_hk(revenue_df, symbol, company_name, start_year, end_year, '营收基本数据', timestamp=timestamp)
    
    # 计算增长率数据
    growth_df = calculate_hk_growth_metrics(symbol, start_year, end_year)
    if growth_df is not None and not growth_df.empty:
        print("\n" + "=" * 80)
        print(f"增长率数据（{start_year}-{end_year}）")
        print("=" * 80)
        print(growth_df.to_string(index=False))
        save_to_excel_hk(growth_df, symbol, company_name, start_year, end_year, '增长', timestamp=timestamp)
    
    # 计算收益率和杜邦分析数据
    roi_df = calculate_hk_roi_metrics(symbol, start_year, end_year)
    if roi_df is not None and not roi_df.empty:
        print("\n" + "=" * 80)
        print(f"收益率和杜邦分析数据（{start_year}-{end_year}）")
        print("=" * 80)
        print(roi_df.to_string(index=False))
        save_to_excel_hk(roi_df, symbol, company_name, start_year, end_year, '收益率和杜邦分析', timestamp=timestamp)
    
    # 最终提示
    symbol_clean = symbol.replace('.HK', '')
    filename = f"{company_name}_{start_year}-{end_year}_港股财务分析_{timestamp}.xlsx"
    filepath = os.path.join("output", filename)
    if os.path.exists(filepath):
        print(f"\n{'='*80}")
        print(f"[OK] 数据已保存到: {filepath}")
        print(f"\n注意：由于港股接口数据有限，只能生成部分sheet：")
        print("1. 营收基本数据")
        print("2. 增长")
        print("3. 收益率和杜邦分析")
        print(f"{'='*80}")

if __name__ == "__main__":
    main()

