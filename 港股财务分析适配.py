# -*- coding: utf-8 -*-
"""
港股财务分析适配层

将港股财务数据接口适配到现有的A股财务分析框架
"""

import akshare as ak
import pandas as pd
from typing import Optional, Dict
from datetime import datetime

def is_hk_stock(symbol: str) -> bool:
    """
    判断是否为港股代码
    
    参数:
        symbol: 股票代码
    
    返回:
        如果是港股返回True，否则返回False
    """
    symbol_clean = symbol.replace('.HK', '').replace('.SZ', '').replace('.SH', '')
    # 港股代码通常是5位数字
    return len(symbol_clean) == 5 and symbol_clean.isdigit()

def get_hk_annual_data(symbol: str, start_year: int = 2015, end_year: int = 2024) -> Dict:
    """
    获取港股指定年份范围的年报数据
    
    参数:
        symbol: 港股代码（5位数字，如 "00700"）
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        包含财务分析指标数据的字典
        注意：港股接口返回的是分析指标，不是完整的三大报表
    """
    symbol_clean = symbol.replace('.HK', '')
    
    results = {
        'analysis_indicator': None,  # 财务分析指标（主要数据源）
        'financial_indicator': None,  # 财务指标（补充数据）
        'profit': None,  # 利润表（从分析指标中提取）
        'cash_flow': None,  # 现金流量表（部分数据）
        'balance_sheet': None,  # 资产负债表（部分数据）
    }
    
    try:
        # 获取财务分析指标（主要数据源）
        print("正在获取港股财务分析指标数据...")
        analysis_indicator = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol_clean)
        if analysis_indicator is not None and not analysis_indicator.empty:
            results['analysis_indicator'] = analysis_indicator
            print(f"[OK] 财务分析指标数据获取成功，共 {len(analysis_indicator)} 条记录")
            
            # 从分析指标中提取利润表相关数据
            profit_data = extract_profit_from_hk_indicator(analysis_indicator)
            if profit_data is not None:
                results['profit'] = profit_data
                print(f"[OK] 利润表数据提取成功")
        else:
            print("[FAIL] 财务分析指标数据获取失败或为空")
        
        # 获取财务指标（补充数据）
        print("正在获取港股财务指标数据...")
        try:
            financial_indicator = ak.stock_hk_financial_indicator_em(symbol=symbol_clean)
            if financial_indicator is not None and not financial_indicator.empty:
                results['financial_indicator'] = financial_indicator
                print(f"[OK] 财务指标数据获取成功，共 {len(financial_indicator)} 条记录")
        except Exception as e:
            print(f"[WARNING] 财务指标数据获取失败: {e}")
        
    except Exception as e:
        print(f"[FAIL] 获取港股数据失败: {e}")
        import traceback
        traceback.print_exc()
    
    return results

def extract_profit_from_hk_indicator(analysis_indicator: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    从港股分析指标中提取利润表相关数据
    
    参数:
        analysis_indicator: 港股财务分析指标DataFrame
    
    返回:
        利润表格式的DataFrame（字段名映射为A股格式）
    """
    if analysis_indicator is None or analysis_indicator.empty:
        return None
    
    # 字段映射：港股字段 -> A股字段
    field_mapping = {
        'OPERATE_INCOME': 'OPERATE_INCOME',  # 营业收入
        'HOLDER_PROFIT': 'PARENT_NETPROFIT',  # 股东利润 -> 归母净利润
        'GROSS_PROFIT': 'GROSS_PROFIT',  # 毛利润
        'GROSS_PROFIT_RATIO': 'GROSS_PROFIT_RATIO',  # 毛利率
        'NET_PROFIT_RATIO': 'NET_PROFIT_RATIO',  # 净利率
        'REPORT_DATE': 'REPORT_DATE',  # 报告期
    }
    
    # 创建利润表DataFrame
    profit_data = pd.DataFrame()
    
    # 复制映射的字段
    for hk_field, a_field in field_mapping.items():
        if hk_field in analysis_indicator.columns:
            profit_data[a_field] = analysis_indicator[hk_field]
    
    # 添加报告期字段（如果存在）
    if 'REPORT_DATE' in analysis_indicator.columns:
        profit_data['REPORT_DATE'] = analysis_indicator['REPORT_DATE']
    elif 'FISCAL_YEAR' in analysis_indicator.columns:
        # 如果没有REPORT_DATE，尝试从FISCAL_YEAR构造
        profit_data['REPORT_DATE'] = analysis_indicator['FISCAL_YEAR']
    
    return profit_data if not profit_data.empty else None

def extract_year_data_hk(df: pd.DataFrame, year: int, date_col_name: str = 'REPORT_DATE') -> Optional[pd.Series]:
    """
    从港股数据框中提取指定年份的数据
    
    参数:
        df: 数据框
        year: 年份，如 2024
        date_col_name: 报告期列名
    
    返回:
        该年份的数据行（Series），如果没有则返回None
    """
    if df is None or df.empty:
        return None
    
    # 查找报告期列
    date_col = None
    for col in df.columns:
        if date_col_name in col or 'REPORT_DATE' in col or 'FISCAL_YEAR' in col:
            date_col = col
            break
    
    if date_col is None:
        return None
    
    # 筛选指定年份的年报数据
    year_str = str(year)
    
    # 尝试多种日期格式匹配
    filtered = df[
        df[date_col].astype(str).str.contains(year_str, na=False)
    ]
    
    # 如果是年报，通常包含12-31
    if 'FISCAL_YEAR' in df.columns:
        filtered = filtered[filtered['FISCAL_YEAR'].astype(str).str.contains('12-31', na=False)]
    
    if not filtered.empty:
        return filtered.iloc[-1]  # 取最后一条（最新的）
    
    return None

def get_value_from_row_hk(row: pd.Series, column_name: str, default: str = "-", return_numeric: bool = True):
    """
    从港股数据行中获取指定列的值，转换为数值（亿元）
    
    参数:
        row: 数据行
        column_name: 列名
        default: 默认值，如果数据缺失返回此值（通常为 "-"）
        return_numeric: 是否返回数值，False时返回字符串（用于缺失数据）
    
    返回:
        数值（亿元），保留2位小数；如果数据缺失，返回 default（通常是 "-"）
    """
    if row is None:
        return default
    
    if column_name not in row.index:
        return default
    
    value = row[column_name]
    try:
        num_value = float(value)
        if pd.isna(num_value):
            return default
        # 转换为亿元（港股数据单位可能是元，需要除以100000000）
        if return_numeric:
            return round(num_value / 100000000, 2)
        else:
            return str(round(num_value / 100000000, 2))
    except (ValueError, TypeError):
        return default

def get_hk_symbol_name(symbol: str) -> str:
    """
    获取港股名称
    
    参数:
        symbol: 港股代码，如 "00700"
    
    返回:
        股票名称
    """
    try:
        symbol_clean = symbol.replace('.HK', '')
        # 尝试从财务分析指标中获取名称
        try:
            indicator = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol_clean)
            if indicator is not None and not indicator.empty:
                if 'SECURITY_NAME_ABBR' in indicator.columns:
                    name = indicator['SECURITY_NAME_ABBR'].iloc[0]
                    if pd.notna(name):
                        return name
        except:
            pass
        
        # 如果获取失败，返回代码
        return symbol_clean
    except:
        return symbol.replace('.HK', '')

def get_annual_data_unified(symbol: str, start_year: int = 2015, end_year: int = 2024) -> Dict:
    """
    统一接口：自动识别A股或港股并获取数据
    
    参数:
        symbol: 股票代码
            - A股：6位数字，如 "600519" 或 "600519.SH"
            - 港股：5位数字，如 "00700"
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        包含财务数据的字典
    """
    if is_hk_stock(symbol):
        print(f"检测到港股代码: {symbol}")
        return get_hk_annual_data(symbol, start_year, end_year)
    else:
        print(f"检测到A股代码: {symbol}")
        # 导入A股数据获取函数
        from importlib import import_module
        import sys
        if '07_财务分析' in sys.modules:
            financial_module = sys.modules['07_财务分析']
            return financial_module.get_annual_data(symbol, start_year, end_year)
        else:
            # 如果模块未导入，直接调用
            import akshare as ak
            
            symbol_with_suffix = symbol
            if '.' not in symbol:
                if symbol.startswith(('000', '001', '002', '300')):
                    symbol_with_suffix = symbol + '.SZ'
                elif symbol.startswith(('600', '601', '603', '605', '688')):
                    symbol_with_suffix = symbol + '.SH'
                else:
                    symbol_with_suffix = symbol + '.SZ'
            
            results = {
                'profit': None,
                'cash_flow': None,
                'balance_sheet': None
            }
            
            try:
                profit = ak.stock_profit_sheet_by_report_em(symbol=symbol_with_suffix)
                if profit is not None and not profit.empty:
                    results['profit'] = profit
                
                cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol_with_suffix)
                if cash_flow is not None and not cash_flow.empty:
                    results['cash_flow'] = cash_flow
                
                balance_sheet = ak.stock_balance_sheet_by_report_em(symbol=symbol_with_suffix)
                if balance_sheet is not None and not balance_sheet.empty:
                    results['balance_sheet'] = balance_sheet
            except Exception as e:
                print(f"[FAIL] 获取A股数据失败: {e}")
            
            return results

# 港股字段映射表（用于文档参考）
HK_FIELD_MAPPING = {
    # 利润表字段
    'OPERATE_INCOME': '营业收入',
    'HOLDER_PROFIT': '归母净利润（股东利润）',
    'GROSS_PROFIT': '毛利润',
    'GROSS_PROFIT_RATIO': '毛利率',
    'NET_PROFIT_RATIO': '净利率',
    
    # 收益率指标
    'ROE_AVG': 'ROE（平均）',
    'ROE_YEARLY': 'ROE（年度）',
    'ROA': 'ROA',
    'ROIC_YEARLY': 'ROIC（年度）',
    
    # 其他指标
    'PER_NETCASH_OPERATE': '每股经营现金流',
    'DEBT_ASSET_RATIO': '资产负债率',
    'CURRENT_RATIO': '流动比率',
    'OCF_SALES': '经营现金流/销售收入',
    
    # 日期字段
    'REPORT_DATE': '报告期',
    'FISCAL_YEAR': '会计年度',
    'CURRENCY': '货币单位',
}

if __name__ == "__main__":
    # 测试港股数据获取
    print("=" * 80)
    print("测试港股数据获取")
    print("=" * 80)
    
    symbol = "00700"  # 腾讯控股
    results = get_hk_annual_data(symbol, 2020, 2024)
    
    print("\n获取结果:")
    for key, value in results.items():
        if value is not None:
            print(f"  {key}: {type(value).__name__}, shape: {value.shape if hasattr(value, 'shape') else 'N/A'}")
        else:
            print(f"  {key}: None")

