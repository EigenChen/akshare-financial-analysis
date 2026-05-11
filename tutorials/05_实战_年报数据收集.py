"""
AKShare 实战 - 批量收集年报数据

这是一个实战示例，展示如何：
1. 批量获取多只股票的年报数据
2. 数据清洗和整理
3. 保存为结构化文件
"""

import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

# 资产负债表字段映射（常用字段）
BALANCE_SHEET_FIELD_MAPPING = {
    'ACCOUNTS_PAYABLE': '应付账款',
    'ADVANCE_RECEIVABLES': '预收账款',  # 预收款项
    'CONTRACT_LIAB': '合同负债',
    'ACCOUNTS_RECE': '应收账款',
    'MONETARYFUNDS': '货币资金',
    'INVENTORY': '存货',
    'TOTAL_CURRENT_ASSETS': '流动资产总计',
    'TOTAL_NONCURRENT_ASSETS': '非流动资产总计',
    'TOTAL_ASSETS': '资产总计',
    'TOTAL_PARENT_EQUITY': '归属于母公司所有者权益合计',
    'TOTAL_LIABILITIES': '负债总计',
    'SHORT_LOAN': '短期借款',
    'LONG_LOAN': '长期借款',
    'BOND_PAYABLE': '应付债券',
}

def ensure_dir(directory):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_stock_annual_data(symbol, save_dir="data"):
    """
    获取单只股票的年报数据并保存
    
    参数:
        symbol: 股票代码（会自动处理格式）
        save_dir: 保存目录
    """
    print(f"\n正在获取 {symbol} 的年报数据...")
    
    try:
        # 创建保存目录
        ensure_dir(save_dir)
        stock_dir = os.path.join(save_dir, symbol)
        ensure_dir(stock_dir)
        
        # 处理股票代码格式
        symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
        symbol_with_suffix = symbol
        if '.' not in symbol:
            if symbol.startswith(('000', '001', '002', '300')):
                symbol_with_suffix = symbol + '.SZ'
            elif symbol.startswith(('600', '601', '603', '605', '688')):
                symbol_with_suffix = symbol + '.SH'
            else:
                symbol_with_suffix = symbol + '.SZ'
        
        results = {}
        
        # 1. 获取财务指标（使用不带后缀的格式）
        try:
            financial = ak.stock_financial_abstract_ths(symbol=symbol_clean)
            if financial is not None and not financial.empty:
                results['financial_indicator'] = financial
                filepath = os.path.join(stock_dir, f"{symbol}_财务指标.csv")
                financial.to_csv(filepath, index=False, encoding='utf-8-sig')
                print(f"  ✓ 财务指标: {len(financial)} 条记录")
        except Exception as e:
            print(f"  ✗ 财务指标获取失败: {e}")
        
        # 2. 获取资产负债表（使用带后缀的格式）
        try:
            balance = ak.stock_balance_sheet_by_report_em(symbol=symbol_with_suffix)
            if balance is not None and not balance.empty:
                if '报告期' in balance.columns:
                    annual_balance = balance[
                        balance['报告期'].str.contains('12-31', na=False)
                    ]
                else:
                    annual_balance = balance
                
                results['balance_sheet'] = annual_balance
                filepath = os.path.join(stock_dir, f"{symbol}_资产负债表.csv")
                annual_balance.to_csv(filepath, index=False, encoding='utf-8-sig')
                print(f"  ✓ 资产负债表: {len(annual_balance)} 条记录")
        except Exception as e:
            print(f"  ✗ 资产负债表获取失败: {e}")
        
        # 3. 获取利润表（使用带后缀的格式）
        try:
            profit = ak.stock_profit_sheet_by_report_em(symbol=symbol_with_suffix)
            if profit is not None and not profit.empty:
                if '报告期' in profit.columns:
                    annual_profit = profit[
                        profit['报告期'].str.contains('12-31', na=False)
                    ]
                else:
                    annual_profit = profit
                
                results['profit'] = annual_profit
                filepath = os.path.join(stock_dir, f"{symbol}_利润表.csv")
                annual_profit.to_csv(filepath, index=False, encoding='utf-8-sig')
                print(f"  ✓ 利润表: {len(annual_profit)} 条记录")
        except Exception as e:
            print(f"  ✗ 利润表获取失败: {e}")
        
        # 4. 获取现金流量表（使用带后缀的格式）
        try:
            cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol_with_suffix)
            if cash_flow is not None and not cash_flow.empty:
                if '报告期' in cash_flow.columns:
                    annual_cash_flow = cash_flow[
                        cash_flow['报告期'].str.contains('12-31', na=False)
                    ]
                else:
                    annual_cash_flow = cash_flow
                
                results['cash_flow'] = annual_cash_flow
                filepath = os.path.join(stock_dir, f"{symbol}_现金流量表.csv")
                annual_cash_flow.to_csv(filepath, index=False, encoding='utf-8-sig')
                print(f"  ✓ 现金流量表: {len(annual_cash_flow)} 条记录")
        except Exception as e:
            print(f"  ✗ 现金流量表获取失败: {e}")
        
        return results
        
    except Exception as e:
        print(f"  ✗ 获取 {symbol} 数据失败: {e}")
        return None

def batch_collect_annual_data(symbols, save_dir="data", delay=1):
    """
    批量收集多只股票的年报数据
    
    参数:
        symbols: 股票代码列表，如 ["000001", "000002"]
        save_dir: 保存目录
        delay: 每次请求之间的延时（秒），避免请求过快
    """
    print("=" * 60)
    print(f"开始批量收集 {len(symbols)} 只股票的年报数据")
    print("=" * 60)
    
    results_summary = {
        'success': [],
        'failed': []
    }
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] 处理股票: {symbol}")
        
        result = get_stock_annual_data(symbol, save_dir)
        
        if result:
            results_summary['success'].append(symbol)
        else:
            results_summary['failed'].append(symbol)
        
        # 添加延时，避免请求过快
        if i < len(symbols):
            time.sleep(delay)
    
    # 保存汇总信息
    summary_file = os.path.join(save_dir, "收集汇总.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"数据收集完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"成功: {len(results_summary['success'])} 只\n")
        f.write(f"失败: {len(results_summary['failed'])} 只\n\n")
        f.write("成功的股票:\n")
        for symbol in results_summary['success']:
            f.write(f"  {symbol}\n")
        f.write("\n失败的股票:\n")
        for symbol in results_summary['failed']:
            f.write(f"  {symbol}\n")
    
    print("\n" + "=" * 60)
    print("批量收集完成！")
    print(f"成功: {len(results_summary['success'])} 只")
    print(f"失败: {len(results_summary['failed'])} 只")
    print(f"汇总信息已保存到: {summary_file}")
    print("=" * 60)
    
    return results_summary

def main():
    # 示例：收集几只股票的年报数据
    # 你可以修改这个列表来收集你感兴趣的股票
    
    # 示例股票列表（平安银行、万科A、贵州茅台）
    test_symbols = ["000001", "000002", "600519"]
    
    print("本示例将收集以下股票的年报数据：")
    for symbol in test_symbols:
        print(f"  - {symbol}")
    
    confirm = input("\n是否开始收集？(y/n): ")
    if confirm.lower() != 'y':
        print("已取消")
        return
    
    # 开始批量收集
    results = batch_collect_annual_data(
        symbols=test_symbols,
        save_dir="data/annual_reports",
        delay=2  # 每次请求间隔2秒，避免请求过快
    )
    
    print("\n提示：")
    print("1. 数据已保存到 data/annual_reports/ 目录")
    print("2. 每只股票的数据保存在单独的文件夹中")
    print("3. 可以根据需要调整延时时间，避免被限制访问")

if __name__ == "__main__":
    main()

