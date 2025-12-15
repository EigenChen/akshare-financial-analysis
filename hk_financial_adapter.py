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
    获取港股指定年份范围的年报数据（完整三大报表）
    
    参数:
        symbol: 港股代码（5位数字，如 "00700"）
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        包含利润表、现金流量表、资产负债表数据和中文名称映射的字典
    """
    symbol_clean = symbol.replace('.HK', '')
    
    results = {
        'profit': None,  # 利润表
        'cash_flow': None,  # 现金流量表
        'balance_sheet': None,  # 资产负债表
        'analysis_indicator': None,  # 财务分析指标（补充数据）
        'profit_chinese_mapping': {},  # 利润表中文字段映射
        'cash_flow_chinese_mapping': {},  # 现金流量表中文字段映射
        'balance_sheet_chinese_mapping': {},  # 资产负债表中文字段映射
    }
    
    try:
        # 获取利润表
        print("正在获取港股利润表数据...")
        profit_long = ak.stock_financial_hk_report_em(stock=symbol_clean, symbol="利润表", indicator="年度")
        if profit_long is not None and not profit_long.empty:
            # 将长格式转换为宽格式
            profit_wide, profit_mapping = convert_hk_long_to_wide(profit_long, '利润表')
            if profit_wide is not None:
                results['profit'] = profit_wide
                results['profit_chinese_mapping'] = profit_mapping
                print(f"[OK] 利润表数据获取成功，共 {len(profit_wide)} 条记录")
        else:
            print("[FAIL] 利润表数据获取失败或为空")
        
        # 获取现金流量表
        print("正在获取港股现金流量表数据...")
        cashflow_long = ak.stock_financial_hk_report_em(stock=symbol_clean, symbol="现金流量表", indicator="年度")
        if cashflow_long is not None and not cashflow_long.empty:
            # 将长格式转换为宽格式
            cashflow_wide, cashflow_mapping = convert_hk_long_to_wide(cashflow_long, '现金流量表')
            if cashflow_wide is not None:
                results['cash_flow'] = cashflow_wide
                results['cash_flow_chinese_mapping'] = cashflow_mapping
                print(f"[OK] 现金流量表数据获取成功，共 {len(cashflow_wide)} 条记录")
        else:
            print("[FAIL] 现金流量表数据获取失败或为空")
        
        # 获取资产负债表
        print("正在获取港股资产负债表数据...")
        balance_long = ak.stock_financial_hk_report_em(stock=symbol_clean, symbol="资产负债表", indicator="年度")
        if balance_long is not None and not balance_long.empty:
            # 将长格式转换为宽格式
            balance_wide, balance_mapping = convert_hk_long_to_wide(balance_long, '资产负债表')
            if balance_wide is not None:
                results['balance_sheet'] = balance_wide
                results['balance_sheet_chinese_mapping'] = balance_mapping
                print(f"[OK] 资产负债表数据获取成功，共 {len(balance_wide)} 条记录")
        else:
            print("[FAIL] 资产负债表数据获取失败或为空")
        
        # 获取财务分析指标（补充数据，用于验证）
        print("正在获取港股财务分析指标数据...")
        try:
            analysis_indicator = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol_clean)
            if analysis_indicator is not None and not analysis_indicator.empty:
                results['analysis_indicator'] = analysis_indicator
                print(f"[OK] 财务分析指标数据获取成功，共 {len(analysis_indicator)} 条记录")
        except Exception as e:
            print(f"[WARNING] 财务分析指标数据获取失败: {e}")
        
    except Exception as e:
        print(f"[FAIL] 获取港股数据失败: {e}")
        import traceback
        traceback.print_exc()
    
    return results

def convert_hk_long_to_wide(df_long: pd.DataFrame, sheet_type: str) -> tuple:
    """
    将港股长格式数据转换为宽格式（类似A股格式）
    
    参数:
        df_long: 长格式DataFrame（每个科目一行）
        sheet_type: 报表类型（"利润表"、"资产负债表"、"现金流量表"）
    
    返回:
        (宽格式DataFrame, 中文名称映射字典)
        宽格式DataFrame：每个科目一列，每行一个报告期
        中文名称映射字典：{英文字段名: 中文科目名}
    """
    if df_long is None or df_long.empty:
        return None, {}
    
    # 检查必要的列
    if 'STD_ITEM_NAME' not in df_long.columns or 'AMOUNT' not in df_long.columns:
        return None, {}
    
    # 获取报告期列
    date_col = None
    for col in ['REPORT_DATE', 'STD_REPORT_DATE', 'FISCAL_YEAR']:
        if col in df_long.columns:
            date_col = col
            break
    
    if date_col is None:
        return None, {}
    
    # 使用pivot将长格式转换为宽格式
    try:
        # 先进行字段映射（在pivot之前）
        # 创建一个映射后的科目名称列
        df_long_mapped = df_long.copy()
        df_long_mapped['MAPPED_ITEM_NAME'] = df_long_mapped['STD_ITEM_NAME']
        
        # 获取映射表
        column_mapping = get_hk_column_mapping(sheet_type)
        
        # 创建反向映射：英文字段名 -> 中文科目名
        chinese_name_mapping = {}
        
        # 应用映射（只映射匹配的科目）
        for hk_name, a_name in column_mapping.items():
            mask = df_long_mapped['STD_ITEM_NAME'] == hk_name
            if mask.any():
                df_long_mapped.loc[mask, 'MAPPED_ITEM_NAME'] = a_name
                # 记录映射关系（如果有多个中文名映射到同一英文字段，保留第一个）
                if a_name not in chinese_name_mapping:
                    chinese_name_mapping[a_name] = hk_name
        
        # 对于未映射的科目，使用原始中文名称作为英文字段名（保留中文）
        for idx, row in df_long_mapped.iterrows():
            mapped_name = row['MAPPED_ITEM_NAME']
            if mapped_name == row['STD_ITEM_NAME']:  # 未映射的科目
                chinese_name = row['STD_ITEM_NAME']
                # 如果这个中文名称还没有映射，就使用它自己
                if mapped_name not in chinese_name_mapping:
                    chinese_name_mapping[mapped_name] = chinese_name
        
        # 创建透视表：报告期为行，映射后的科目名称为列，金额为值
        # 如果有多个源科目映射到同一目标列，取第一个非空值
        df_wide = df_long_mapped.pivot_table(
            index=date_col,
            columns='MAPPED_ITEM_NAME',
            values='AMOUNT',
            aggfunc='first'  # 如果有重复，取第一个
        )
        
        # 重置索引，将报告期变为列
        df_wide = df_wide.reset_index()
        
        # 重命名报告期列
        if date_col in df_wide.columns:
            df_wide.rename(columns={date_col: 'REPORT_DATE'}, inplace=True)
        
        return df_wide, chinese_name_mapping
        
    except Exception as e:
        print(f"[WARNING] 转换长格式到宽格式失败: {e}")
        import traceback
        traceback.print_exc()
        return None, {}

def get_hk_column_mapping(sheet_type: str) -> Dict[str, str]:
    """
    获取港股科目名到A股字段名的映射表
    
    参数:
        sheet_type: 报表类型
    
    返回:
        映射字典
    """
    if sheet_type == '利润表':
        return {
            '营运收入': 'OPERATE_INCOME',  # 营业收入（优先）
            '股东应占溢利': 'PARENT_NETPROFIT',  # 归母净利润
            '除税后溢利': 'NET_PROFIT',  # 净利润
            '持续经营业务税后利润': 'NET_PROFIT',  # 净利润（备选）
            '毛利': 'GROSS_PROFIT',  # 毛利润
            '营运支出': 'OPERATE_COST',  # 营业成本
            '销售及分销费用': 'SALE_EXPENSE',  # 销售费用
            '行政开支': 'MANAGE_EXPENSE',  # 管理费用
            '研发费用': 'RESEARCH_EXPENSE',  # 研发费用（如果存在）
            '融资成本': 'FINANCE_EXPENSE',  # 财务费用
            '利息收入': 'INTEREST_INCOME',  # 利息收入
            '利息支出': 'INTEREST_EXPENSE',  # 利息支出
            '投资收益': 'INVEST_INCOME',  # 投资收益
            '应占联营公司溢利': 'INVEST_INCOME',  # 投资收益（备选）
            '公允价值变动收益': 'FAIRVALUE_CHANGE_INCOME',  # 公允价值变动收益
            '经营溢利': 'OPERATE_PROFIT',  # 营业利润
        }
    elif sheet_type == '资产负债表':
        return {
            '总资产': 'TOTAL_ASSETS',  # 总资产
            '流动资产合计': 'TOTAL_CURRENT_ASSETS',  # 流动资产合计
            '非流动资产合计': 'TOTAL_NONCURRENT_ASSETS',  # 非流动资产合计
            '现金及等价物': 'MONETARYFUNDS',  # 货币资金
            '存货': 'INVENTORY',  # 存货
            '应收帐款': 'ACCOUNTS_RECE',  # 应收账款
            '预付款项': 'PREPAYMENT',  # 预付账款
            '预付款按金及其他应收款': 'PREPAYMENT',  # 预付账款（备选）
            '应付帐款': 'ACCOUNTS_PAYABLE',  # 应付账款
            '应付票据': 'NOTE_PAYABLE',  # 应付票据
            '预收账款': 'ADVANCE_RECEIVABLES',  # 预收账款
            '递延收入(流动)': 'ADVANCE_RECEIVABLES',  # 预收账款（备选）
            '总负债': 'TOTAL_LIABILITIES',  # 总负债
            '股东权益': 'TOTAL_PARENT_EQUITY',  # 归母净资产
            '净资产': 'TOTAL_PARENT_EQUITY',  # 归母净资产（备选）
            '物业厂房及设备': 'FIXED_ASSET',  # 固定资产
            '固定资产': 'FIXED_ASSET',  # 固定资产（备选）
            '在建工程': 'CIP',  # 在建工程
            '无形资产': 'INTANGIBLE_ASSET',  # 无形资产
            '商誉': 'GOODWILL',  # 商誉
            '短期借款': 'SHORT_LOAN',  # 短期借款
            '长期借款': 'LONG_LOAN',  # 长期借款
            '应付债券': 'BONDS_PAYABLE',  # 应付债券
            '应付职工薪酬': 'STAFF_SALARY_PAYABLE',  # 应付职工薪酬
            '合同资产': 'CONTRACT_ASSET',  # 合同资产
            '合同负债': 'CONTRACT_LIAB',  # 合同负债
        }
    elif sheet_type == '现金流量表':
        return {
            '经营业务现金净额': 'NETCASH_OPERATE',  # 经营净现金流（优先）
            '购建固定资产': 'CONSTRUCT_LONG_ASSET',  # CAPEX
            '支付给职工以及为职工支付的现金': 'PAY_STAFF_CASH',  # 支付给职工以及为职工支付的现金
            '已付职工薪酬': 'PAY_STAFF_CASH',  # 支付给职工以及为职工支付的现金（备选）
            '固定资产折旧': 'FIXED_ASSET_DEPR',  # 固定资产折旧
            '折旧及摊销': 'FIXED_ASSET_DEPR',  # 固定资产折旧（备选）
        }
    else:
        return {}

def map_hk_columns_to_a_stock(df: pd.DataFrame, sheet_type: str) -> pd.DataFrame:
    """
    将港股中文科目名称映射为A股英文字段名
    
    参数:
        df: 宽格式DataFrame（列名为中文科目名）
        sheet_type: 报表类型
    
    返回:
        映射后的DataFrame（列名为A股英文字段名）
    """
    # 港股科目名 -> A股字段名映射表
    if sheet_type == '利润表':
        column_mapping = {
            '营运收入': 'OPERATE_INCOME',  # 营业收入（优先）
            '营业额': 'OPERATE_INCOME',  # 营业收入（备选）
            '股东应占溢利': 'PARENT_NETPROFIT',  # 归母净利润
            '除税后溢利': 'NET_PROFIT',  # 净利润
            '持续经营业务税后利润': 'NET_PROFIT',  # 净利润（备选）
            '毛利': 'GROSS_PROFIT',  # 毛利润
            '营运支出': 'OPERATE_COST',  # 营业成本
            '销售及分销费用': 'SALE_EXPENSE',  # 销售费用
            '行政开支': 'MANAGE_EXPENSE',  # 管理费用
            '研发费用': 'RESEARCH_EXPENSE',  # 研发费用（如果存在）
            '融资成本': 'FINANCE_EXPENSE',  # 财务费用
            '利息收入': 'INTEREST_INCOME',  # 利息收入
            '利息支出': 'INTEREST_EXPENSE',  # 利息支出
            '投资收益': 'INVEST_INCOME',  # 投资收益
            '应占联营公司溢利': 'INVEST_INCOME',  # 投资收益（备选）
            '公允价值变动收益': 'FAIRVALUE_CHANGE_INCOME',  # 公允价值变动收益
            '经营溢利': 'OPERATE_PROFIT',  # 营业利润
        }
    elif sheet_type == '资产负债表':
        column_mapping = {
            '总资产': 'TOTAL_ASSETS',  # 总资产
            '流动资产合计': 'TOTAL_CURRENT_ASSETS',  # 流动资产合计
            '非流动资产合计': 'TOTAL_NONCURRENT_ASSETS',  # 非流动资产合计
            '现金及等价物': 'MONETARYFUNDS',  # 货币资金
            '存货': 'INVENTORY',  # 存货
            '应收帐款': 'ACCOUNTS_RECE',  # 应收账款
            '预付款项': 'PREPAYMENT',  # 预付账款
            '预付款按金及其他应收款': 'PREPAYMENT',  # 预付账款（备选）
            '应付帐款': 'ACCOUNTS_PAYABLE',  # 应付账款
            '应付票据': 'NOTE_PAYABLE',  # 应付票据
            '预收账款': 'ADVANCE_RECEIVABLES',  # 预收账款
            '递延收入(流动)': 'ADVANCE_RECEIVABLES',  # 预收账款（备选）
            '总负债': 'TOTAL_LIABILITIES',  # 总负债
            '股东权益': 'TOTAL_PARENT_EQUITY',  # 归母净资产
            '净资产': 'TOTAL_PARENT_EQUITY',  # 归母净资产（备选）
            '物业厂房及设备': 'FIXED_ASSET',  # 固定资产
            '固定资产': 'FIXED_ASSET',  # 固定资产（备选）
            '在建工程': 'CIP',  # 在建工程
            '无形资产': 'INTANGIBLE_ASSET',  # 无形资产
            '商誉': 'GOODWILL',  # 商誉
            '短期借款': 'SHORT_LOAN',  # 短期借款
            '长期借款': 'LONG_LOAN',  # 长期借款
            '应付债券': 'BONDS_PAYABLE',  # 应付债券
            '应付职工薪酬': 'STAFF_SALARY_PAYABLE',  # 应付职工薪酬
            '合同资产': 'CONTRACT_ASSET',  # 合同资产
            '合同负债': 'CONTRACT_LIAB',  # 合同负债
        }
    elif sheet_type == '现金流量表':
        column_mapping = {
            '经营业务现金净额': 'NETCASH_OPERATE',  # 经营净现金流（优先）
            '经营产生现金': 'NETCASH_OPERATE',  # 经营净现金流（备选）
            '购建固定资产': 'CONSTRUCT_LONG_ASSET',  # CAPEX
            '支付给职工以及为职工支付的现金': 'PAY_STAFF_CASH',  # 支付给职工以及为职工支付的现金
            '已付职工薪酬': 'PAY_STAFF_CASH',  # 支付给职工以及为职工支付的现金（备选）
            '固定资产折旧': 'FIXED_ASSET_DEPR',  # 固定资产折旧
            '折旧及摊销': 'FIXED_ASSET_DEPR',  # 固定资产折旧（备选）
        }
    else:
        column_mapping = {}
    
    # 重命名列
    rename_dict = {}
    for hk_col, a_col in column_mapping.items():
        if hk_col in df.columns:
            rename_dict[hk_col] = a_col
    
    if rename_dict:
        df = df.rename(columns=rename_dict)
    
    return df

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
        df: 数据框（宽格式，每行一个报告期）
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
        if date_col_name in col or 'REPORT_DATE' in col:
            date_col = col
            break
    
    if date_col is None:
        return None
    
    # 筛选指定年份的年报数据（12-31）
    year_str = str(year)
    
    # 尝试多种日期格式匹配
    filtered = df[
        df[date_col].astype(str).str.contains(year_str, na=False) &
        df[date_col].astype(str).str.contains('12-31', na=False)
    ]
    
    if not filtered.empty:
        return filtered.iloc[-1]  # 取最后一条（最新的）
    
    return None

def get_value_from_row_hk(row: pd.Series, column_name: str, default: str = "-", return_numeric: bool = True, is_percentage: bool = False):
    """
    从港股数据行中获取指定列的值
    
    参数:
        row: 数据行（宽格式，列名为A股英文字段名）
        column_name: 列名（A股英文字段名，如 'OPERATE_INCOME'）
        default: 默认值，如果数据缺失返回此值（通常为 "-"）
        return_numeric: 是否返回数值，False时返回字符串（用于缺失数据）
        is_percentage: 是否为百分比字段（如果是，不除以100000000）
    
    返回:
        数值（亿元或百分比），保留2位小数；如果数据缺失，返回 default（通常是 "-"）
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
        
        # 如果是百分比字段，直接返回
        if is_percentage:
            if return_numeric:
                return round(num_value, 2)
            else:
                return str(round(num_value, 2))
        
        # 转换为亿元（港股数据单位是元，需要除以100000000）
        if return_numeric:
            return round(num_value / 100000000, 2)
        else:
            return str(round(num_value / 100000000, 2))
    except (ValueError, TypeError):
        return default

def get_hk_employee_count(symbol: str, year: Optional[int] = None) -> Optional[int]:
    """
    获取港股员工人数
    
    参数:
        symbol: 港股代码（5位数字，如 "00700"）
        year: 年份（可选，目前接口只返回最新数据）
    
    返回:
        员工人数（整数），如果获取失败返回None
    """
    symbol_clean = symbol.replace('.HK', '')
    
    try:
        # 使用港股公司概况接口获取员工人数
        profile = ak.stock_hk_company_profile_em(symbol=symbol_clean)
        
        if profile is not None and not profile.empty:
            # 查找员工人数字段
            if '员工人数' in profile.columns:
                employee_count = profile['员工人数'].iloc[0]
                try:
                    # 转换为整数
                    if pd.isna(employee_count):
                        return None
                    employee_count = int(float(employee_count))
                    return employee_count
                except (ValueError, TypeError):
                    return None
        
        return None
    except Exception as e:
        print(f"[WARNING] 获取港股员工人数失败: {e}")
        return None

def get_hk_employee_count_by_year(symbol: str, start_year: int, end_year: int) -> Dict[int, Optional[int]]:
    """
    获取港股指定年份范围的员工人数
    
    注意：港股接口通常只返回最新一年的员工人数，历史数据可能需要从年报PDF中提取
    
    参数:
        symbol: 港股代码
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        字典，格式为 {年份: 员工人数}，如果某年份数据不可用则为None
    """
    result = {}
    
    # 获取最新员工人数
    latest_count = get_hk_employee_count(symbol)
    
    # 目前接口只返回最新数据，所以所有年份都使用同一个值
    # 如果需要历史数据，需要从年报PDF中提取
    for year in range(start_year, end_year + 1):
        result[year] = latest_count
    
    return result

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

