"""
AKShare 基础学习 - 获取年报数据

专门学习如何获取上市公司的年报数据，这是估值分析的核心数据源。
包括：
1. 年报财务数据
2. 年报报告期信息
3. 历年数据对比
"""

import akshare as ak
import pandas as pd
from datetime import datetime

def get_annual_reports_list(symbol):
    """
    获取指定股票的所有年报报告期列表
    
    参数:
        symbol: 股票代码，如 "000001"
    """
    print("=" * 60)
    print(f"获取股票 {symbol} 的年报报告期列表")
    print("=" * 60)
    
    try:
        # 方法1：通过财务指标接口获取报告期
        financial_data = ak.stock_financial_analysis_indicator(symbol=symbol)
        
        if financial_data is not None and not financial_data.empty:
            # 提取报告期列（通常名为 '报告期' 或类似）
            # 需要根据实际返回的数据结构调整
            print(f"\n✓ 成功获取数据，共 {len(financial_data)} 条记录")
            print(f"\n数据列名：{financial_data.columns.tolist()}")
            
            # 尝试找到报告期相关的列
            date_columns = [col for col in financial_data.columns 
                          if any(keyword in col.lower() for keyword in ['日期', '报告期', 'date', 'period'])]
            
            if date_columns:
                print(f"\n找到报告期相关列：{date_columns}")
                # 筛选年报数据（通常年报在12月31日）
                for col in date_columns:
                    print(f"\n{col} 的唯一值（前10个）：")
                    print(financial_data[col].unique()[:10])
            
            return financial_data
        else:
            print("✗ 未获取到数据")
            return None
            
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return None

def get_annual_financial_data(symbol, start_year=None, end_year=None):
    """
    获取指定年份范围的年报财务数据
    
    参数:
        symbol: 股票代码
        start_year: 起始年份，如 2018
        end_year: 结束年份，如 2023
    """
    print("=" * 60)
    print(f"获取股票 {symbol} 的年报财务数据")
    if start_year and end_year:
        print(f"年份范围: {start_year} - {end_year}")
    print("=" * 60)
    
    try:
        # 获取财务指标数据
        financial_data = ak.stock_financial_analysis_indicator(symbol=symbol)
        
        if financial_data is None or financial_data.empty:
            print("✗ 未获取到数据")
            return None
        
        print(f"\n✓ 成功获取原始数据，共 {len(financial_data)} 条记录")
        
        # 显示数据结构
        print(f"\n数据列名：")
        for i, col in enumerate(financial_data.columns, 1):
            print(f"  {i}. {col}")
        
        # 尝试筛选年报数据
        # 注意：需要根据实际数据结构调整筛选逻辑
        annual_data = financial_data.copy()
        
        # 如果数据中有报告期列，筛选12月31日的数据（年报）
        date_columns = [col for col in financial_data.columns 
                       if any(keyword in col.lower() for keyword in ['日期', '报告期', 'date', 'period'])]
        
        if date_columns:
            for col in date_columns:
                # 尝试筛选年报（包含12-31的数据）
                if financial_data[col].dtype == 'object':
                    annual_data = annual_data[
                        annual_data[col].str.contains('12-31', na=False) | 
                        annual_data[col].str.contains('年报', na=False)
                    ]
        
        # 按年份筛选
        if start_year or end_year:
            # 这里需要根据实际数据格式调整
            print(f"\n提示：年份筛选需要根据实际数据格式实现")
        
        print(f"\n筛选后的年报数据，共 {len(annual_data)} 条记录")
        print("\n年报数据预览：")
        print(annual_data.head(10))
        
        return annual_data
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_annual_three_statements(symbol):
    """
    获取年报的三大财务报表
    
    参数:
        symbol: 股票代码（会自动添加交易所后缀）
    """
    print("=" * 60)
    print(f"获取股票 {symbol} 的年报三大财务报表")
    print("=" * 60)
    
    # 确保有交易所后缀（三大报表接口需要带后缀）
    symbol_with_suffix = symbol
    if '.' not in symbol:
        if symbol.startswith(('000', '001', '002', '300')):
            symbol_with_suffix = symbol + '.SZ'
        elif symbol.startswith(('600', '601', '603', '605', '688')):
            symbol_with_suffix = symbol + '.SH'
        else:
            symbol_with_suffix = symbol + '.SZ'
    
    results = {}
    
    try:
        # 1. 资产负债表
        print("\n1. 获取资产负债表...")
        balance_sheet = ak.stock_balance_sheet_by_report_em(symbol=symbol_with_suffix)
        if balance_sheet is not None and not balance_sheet.empty:
            # 筛选年报（12月31日）
            annual_balance = balance_sheet[
                balance_sheet['报告期'].str.contains('12-31', na=False)
            ] if '报告期' in balance_sheet.columns else balance_sheet
            results['balance_sheet'] = annual_balance
            print(f"   ✓ 资产负债表: {len(annual_balance)} 条年报记录")
        
        # 2. 利润表
        print("\n2. 获取利润表...")
        profit = ak.stock_profit_sheet_by_report_em(symbol=symbol_with_suffix)
        if profit is not None and not profit.empty:
            annual_profit = profit[
                profit['报告期'].str.contains('12-31', na=False)
            ] if '报告期' in profit.columns else profit
            results['profit'] = annual_profit
            print(f"   ✓ 利润表: {len(annual_profit)} 条年报记录")
        
        # 3. 现金流量表
        print("\n3. 获取现金流量表...")
        cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol_with_suffix)
        if cash_flow is not None and not cash_flow.empty:
            annual_cash_flow = cash_flow[
                cash_flow['报告期'].str.contains('12-31', na=False)
            ] if '报告期' in cash_flow.columns else cash_flow
            results['cash_flow'] = annual_cash_flow
            print(f"   ✓ 现金流量表: {len(annual_cash_flow)} 条年报记录")
        
        return results
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    # 示例：获取平安银行（000001）的年报数据
    symbol = "000001"
    
    print("提示：本示例使用平安银行（000001）作为演示")
    print("你可以修改 symbol 变量来获取其他股票的数据\n")
    
    # 1. 获取年报报告期列表
    reports = get_annual_reports_list(symbol)
    
    # 2. 获取年报财务数据
    annual_data = get_annual_financial_data(symbol, start_year=2018, end_year=2023)
    
    # 3. 获取三大财务报表的年报数据
    three_statements = get_annual_three_statements(symbol)
    
    if three_statements:
        print("\n" + "=" * 60)
        print("三大财务报表数据已获取")
        print("=" * 60)
        for key, value in three_statements.items():
            if value is not None and not value.empty:
                print(f"\n{key}:")
                print(value.head())
    
    print("\n" + "=" * 60)
    print("学习要点：")
    print("1. 年报数据通常在报告期为 12-31 的记录中")
    print("2. 不同接口返回的数据结构可能不同，需要灵活处理")
    print("3. 建议先查看数据结构，再编写筛选逻辑")
    print("4. 可以结合多个接口获取更完整的财务数据")
    print("=" * 60)

if __name__ == "__main__":
    main()

