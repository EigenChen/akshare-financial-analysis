"""
测试脚本 - 查找可用的财务数据接口

这个脚本用于测试不同的 AKShare 接口，找出哪些接口可以正常工作。
"""

import akshare as ak
import pandas as pd

def test_interface(interface_name, func, symbol_variants):
    """测试一个接口是否可用"""
    print(f"\n{'='*60}")
    print(f"测试接口: {interface_name}")
    print("="*60)
    
    for symbol in symbol_variants:
        try:
            print(f"\n尝试股票代码: {symbol}")
            result = func(symbol)
            
            if result is not None and not result.empty:
                print(f"  ✓ 成功！数据形状: {result.shape}")
                print(f"  列名: {result.columns.tolist()[:5]}...")  # 只显示前5个列名
                return result, symbol
            else:
                print(f"  ⚠ 返回空数据")
                
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 150:
                error_msg = error_msg[:150] + "..."
            print(f"  ✗ 失败: {error_msg}")
    
    return None, None

def main():
    symbol = "000001"  # 平安银行
    symbol_variants = [
        symbol,           # "000001"
        symbol + ".SZ",   # "000001.SZ"
        "sz" + symbol,    # "sz000001"
    ]
    
    print("="*60)
    print("AKShare 财务数据接口测试")
    print("="*60)
    print(f"\n测试股票: {symbol} (平安银行)")
    print(f"测试格式: {symbol_variants}\n")
    
    # 测试的接口列表
    interfaces_to_test = [
        # 财务指标相关
        ("stock_financial_analysis_indicator", 
         lambda s: ak.stock_financial_analysis_indicator(symbol=s)),
        
        # 三大报表
        ("stock_balance_sheet_by_report_em (资产负债表)", 
         lambda s: ak.stock_balance_sheet_by_report_em(symbol=s)),
        
        ("stock_profit_sheet_by_report_em (利润表)", 
         lambda s: ak.stock_profit_sheet_by_report_em(symbol=s)),
        
        ("stock_cash_flow_sheet_by_report_em (现金流量表)", 
         lambda s: ak.stock_cash_flow_sheet_by_report_em(symbol=s)),
        
        # 其他可能的接口
        ("stock_financial_abstract_ths", 
         lambda s: ak.stock_financial_abstract_ths(symbol=s)),
    ]
    
    successful_interfaces = []
    
    for interface_name, func in interfaces_to_test:
        result, working_symbol = test_interface(interface_name, func, symbol_variants)
        if result is not None:
            successful_interfaces.append((interface_name, working_symbol))
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    if successful_interfaces:
        print(f"\n✓ 找到 {len(successful_interfaces)} 个可用的接口：")
        for name, sym in successful_interfaces:
            print(f"  - {name} (使用格式: {sym})")
    else:
        print("\n✗ 没有找到可用的接口")
        print("\n可能的原因：")
        print("1. 网络连接问题")
        print("2. AKShare 版本需要更新")
        print("3. 接口名称已变更")
        print("4. 数据源暂时不可用")
        print("\n建议：")
        print("1. 检查网络连接")
        print("2. 更新 AKShare: pip install --upgrade akshare")
        print("3. 查看 AKShare 最新文档")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

