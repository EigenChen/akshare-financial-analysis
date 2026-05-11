"""
AKShare 基础学习 - 获取财务数据

学习如何获取上市公司的财务数据，包括：
1. 财务指标数据
2. 资产负债表
3. 利润表
4. 现金流量表
"""

import akshare as ak
import pandas as pd

def get_financial_indicator(symbol, period="年报"):
    """
    获取财务指标数据
    
    参数:
        symbol: 股票代码，如 "000001" 或 "000001.SZ"
        period: 报告期类型，"年报" 或 "季报"（当前未使用，保留用于未来扩展）
    
    注意：根据测试，stock_financial_abstract_ths 接口需要使用不带交易所后缀的格式
    """
    print("=" * 60)
    print(f"获取股票 {symbol} 的财务指标数据（{period}）")
    print("=" * 60)
    
    # 去掉交易所后缀（stock_financial_abstract_ths 需要不带后缀的格式）
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    
    try:
        print(f"使用股票代码: {symbol_clean} (接口要求不带交易所后缀)")
        # 使用已验证可用的接口
        financial_data = ak.stock_financial_abstract_ths(symbol=symbol_clean)
        
        if financial_data is not None and not financial_data.empty:
            print(f"\n✓ 成功获取财务指标数据")
            print(f"数据形状: {financial_data.shape}")
            print(f"\n数据列名：")
            print(financial_data.columns.tolist())
            
            print(f"\n前5条数据：")
            print(financial_data.tail())
            
            return financial_data
        else:
            print("✗ 返回空数据")
            return None
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        print("\n提示：")
        print("1. 确认股票代码格式正确（不带交易所后缀）")
        print("2. 检查网络连接")
        print("3. 某些股票可能没有财务数据")
        return None

def get_balance_sheet(symbol):
    """
    获取资产负债表
    
    注意：根据测试，此接口需要使用带交易所后缀的格式，如 "000001.SZ"
    """
    print(f"\n{'=' * 60}")
    print(f"获取股票 {symbol} 的资产负债表")
    print("=" * 60)
    
    # 确保有交易所后缀（此接口需要带后缀的格式）
    symbol_with_suffix = symbol
    if '.' not in symbol:
        # 根据股票代码判断交易所：000/001/002开头是深交所，600/601/603等是上交所
        if symbol.startswith(('000', '001', '002', '300')):
            symbol_with_suffix = symbol + '.SZ'
        elif symbol.startswith(('600', '601', '603', '605', '688')):
            symbol_with_suffix = symbol + '.SH'
        else:
            # 默认尝试深交所
            symbol_with_suffix = symbol + '.SZ'
    
    try:
        print(f"使用股票代码: {symbol_with_suffix} (接口要求带交易所后缀)")
        balance_sheet = ak.stock_balance_sheet_by_report_em(symbol=symbol_with_suffix)
        
        if balance_sheet is not None and not balance_sheet.empty:
            print(f"\n✓ 成功获取资产负债表")
            print(f"数据形状: {balance_sheet.shape}")
            print(f"\n数据列名：")
            print(balance_sheet.columns.tolist())
            
            print(f"\n前5条数据：")
            print(balance_sheet.head())
            
            return balance_sheet
        else:
            print("✗ 返回空数据")
            return None
            
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return None

def get_profit_statement(symbol):
    """
    获取利润表
    
    注意：根据测试，此接口需要使用带交易所后缀的格式，如 "000001.SZ"
    """
    print(f"\n{'=' * 60}")
    print(f"获取股票 {symbol} 的利润表")
    print("=" * 60)
    
    # 确保有交易所后缀
    symbol_with_suffix = symbol
    if '.' not in symbol:
        if symbol.startswith(('000', '001', '002', '300')):
            symbol_with_suffix = symbol + '.SZ'
        elif symbol.startswith(('600', '601', '603', '605', '688')):
            symbol_with_suffix = symbol + '.SH'
        else:
            symbol_with_suffix = symbol + '.SZ'
    
    try:
        print(f"使用股票代码: {symbol_with_suffix} (接口要求带交易所后缀)")
        profit = ak.stock_profit_sheet_by_report_em(symbol=symbol_with_suffix)
        
        if profit is not None and not profit.empty:
            print(f"\n✓ 成功获取利润表")
            print(f"数据形状: {profit.shape}")
            print(f"\n数据列名：")
            print(profit.columns.tolist())
            
            print(f"\n前5条数据：")
            print(profit.head())
            
            return profit
        else:
            print("✗ 返回空数据")
            return None
            
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return None

def get_cash_flow(symbol):
    """
    获取现金流量表
    
    注意：根据测试，此接口需要使用带交易所后缀的格式，如 "000001.SZ"
    """
    print(f"\n{'=' * 60}")
    print(f"获取股票 {symbol} 的现金流量表")
    print("=" * 60)
    
    # 确保有交易所后缀
    symbol_with_suffix = symbol
    if '.' not in symbol:
        if symbol.startswith(('000', '001', '002', '300')):
            symbol_with_suffix = symbol + '.SZ'
        elif symbol.startswith(('600', '601', '603', '605', '688')):
            symbol_with_suffix = symbol + '.SH'
        else:
            symbol_with_suffix = symbol + '.SZ'
    
    try:
        print(f"使用股票代码: {symbol_with_suffix} (接口要求带交易所后缀)")
        cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol_with_suffix)
        
        if cash_flow is not None and not cash_flow.empty:
            print(f"\n✓ 成功获取现金流量表")
            print(f"数据形状: {cash_flow.shape}")
            print(f"\n数据列名：")
            print(cash_flow.columns.tolist())
            
            print(f"\n前5条数据：")
            print(cash_flow.head())
            
            return cash_flow
        else:
            print("✗ 返回空数据")
            return None
            
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return None

def main():
    # 示例：获取平安银行（000001）的财务数据
    # 注意：脚本会自动处理股票代码格式
    # - 财务指标接口需要不带后缀: "000001"
    # - 三大报表接口需要带后缀: "000001.SZ"
    symbol = "000001"
    
    print("提示：本示例使用平安银行（000001）作为演示")
    print("脚本会自动处理股票代码格式（根据接口要求）\n")
    
    # 1. 获取财务指标
    financial_data = get_financial_indicator(symbol)
    
    # 2. 获取资产负债表
    balance_sheet = get_balance_sheet(symbol)
    
    # 3. 获取利润表
    profit = get_profit_statement(symbol)
    
    # 4. 获取现金流量表
    cash_flow = get_cash_flow(symbol)
    
    print("\n" + "=" * 60)
    print("学习要点：")
    print("1. 不同接口返回的数据格式可能不同")
    print("2. 股票代码格式可能需要调整（带或不带交易所后缀）")
    print("3. 数据通常按报告期排序，最新数据可能在最后")
    print("4. 某些接口可能需要特定的参数格式")
    print("=" * 60)

if __name__ == "__main__":
    main()

