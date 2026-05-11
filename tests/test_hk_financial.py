"""
测试AKShare港股财务报表接口

用于验证港股财务报表数据获取接口是否可用，以及数据结构
"""

import akshare as ak
import pandas as pd

def test_hk_financial_interfaces(symbol="00700"):
    """
    测试港股财务报表接口
    
    参数:
        symbol: 港股代码（5位数字），默认00700（腾讯控股）
    """
    print("=" * 80)
    print(f"测试港股财务报表接口 - 股票代码: {symbol}")
    print("=" * 80)
    
    results = {}
    
    # 1. 测试港股财务报表接口
    print("\n1. 测试 stock_financial_hk_report_em（港股财务报表）...")
    try:
        report = ak.stock_financial_hk_report_em(symbol=symbol)
        if report is not None and not report.empty:
            print(f"   [OK] 成功获取数据，共 {len(report)} 条记录")
            print(f"   数据形状: {report.shape}")
            print(f"   列名: {report.columns.tolist()}")
            print(f"\n   前5条数据:")
            print(report.head())
            results['report'] = report
        else:
            print("   [FAIL] 返回空数据")
    except Exception as e:
        print(f"   [FAIL] 接口调用失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 测试港股财务分析指标接口
    print("\n2. 测试 stock_financial_hk_analysis_indicator_em（港股财务分析指标）...")
    try:
        indicator = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol)
        if indicator is not None and not indicator.empty:
            print(f"   ✓ 成功获取数据，共 {len(indicator)} 条记录")
            print(f"   数据形状: {indicator.shape}")
            print(f"   列名: {indicator.columns.tolist()}")
            print(f"\n   前5条数据:")
            print(indicator.head())
            results['indicator'] = indicator
        else:
            print("   [FAIL] 返回空数据")
    except Exception as e:
        print(f"   [FAIL] 接口调用失败: {e}")
    
    # 3. 测试港股财务指标接口
    print("\n3. 测试 stock_financial_hk_financial_indicator_em（港股财务指标）...")
    try:
        financial = ak.stock_financial_hk_financial_indicator_em(symbol=symbol)
        if financial is not None and not financial.empty:
            print(f"   ✓ 成功获取数据，共 {len(financial)} 条记录")
            print(f"   数据形状: {financial.shape}")
            print(f"   列名: {financial.columns.tolist()}")
            print(f"\n   前5条数据:")
            print(financial.head())
            results['financial'] = financial
        else:
            print("   [FAIL] 返回空数据")
    except Exception as e:
        print(f"   [FAIL] 接口调用失败: {e}")
    
    # 4. 尝试查找利润表和现金流量表接口
    print("\n4. 查找利润表和现金流量表相关接口...")
    
    # 检查是否有利润表接口
    profit_interfaces = [
        'stock_financial_hk_profit_em',
        'stock_hk_profit_sheet',
        'stock_hk_profit',
    ]
    
    for interface_name in profit_interfaces:
        if hasattr(ak, interface_name):
            print(f"   找到接口: {interface_name}")
            try:
                func = getattr(ak, interface_name)
                profit = func(symbol=symbol)
                if profit is not None and not profit.empty:
                    print(f"   [OK] {interface_name} 成功获取数据")
                    print(f"   数据形状: {profit.shape}")
                    print(f"   列名: {profit.columns.tolist()}")
                    results['profit'] = profit
                    break
            except Exception as e:
                print(f"   [FAIL] {interface_name} 调用失败: {e}")
    
    # 检查是否有现金流量表接口
    cashflow_interfaces = [
        'stock_financial_hk_cashflow_em',
        'stock_hk_cashflow_sheet',
        'stock_hk_cashflow',
    ]
    
    for interface_name in cashflow_interfaces:
        if hasattr(ak, interface_name):
            print(f"   找到接口: {interface_name}")
            try:
                func = getattr(ak, interface_name)
                cashflow = func(symbol=symbol)
                if cashflow is not None and not cashflow.empty:
                    print(f"   [OK] {interface_name} 成功获取数据")
                    print(f"   数据形状: {cashflow.shape}")
                    print(f"   列名: {cashflow.columns.tolist()}")
                    results['cashflow'] = cashflow
                    break
            except Exception as e:
                print(f"   [FAIL] {interface_name} 调用失败: {e}")
    
    # 5. 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"成功获取的接口: {list(results.keys())}")
    
    if results:
        print("\n建议:")
        print("1. 检查返回数据的字段名，与A股字段进行映射")
        print("2. 确认数据单位（港币 vs 人民币）")
        print("3. 检查报告期格式")
        print("4. 根据实际数据结构调整数据提取逻辑")
    else:
        print("\n[WARNING] 未能成功获取任何数据")
        print("可能的原因:")
        print("1. 接口名称可能不同，需要查看AKShare最新文档")
        print("2. 接口可能需要其他参数")
        print("3. 该股票可能没有财务数据")
        print("\n建议:")
        print("1. 查看AKShare官方文档中的港股相关接口")
        print("2. 在AKShare GitHub仓库中搜索港股财务报表相关Issue")
        print("3. 考虑使用其他数据源（如港交所官网、Wind、同花顺等）")
    
    return results

def compare_with_a_stock():
    """
    对比A股和港股接口的差异
    """
    print("\n" + "=" * 80)
    print("对比A股和港股接口")
    print("=" * 80)
    
    # A股接口
    print("\nA股接口（参考）:")
    print("- stock_balance_sheet_by_report_em(symbol='600519.SH')")
    print("- stock_profit_sheet_by_report_em(symbol='600519.SH')")
    print("- stock_cash_flow_sheet_by_report_em(symbol='600519.SH')")
    
    # 港股接口
    print("\n港股接口（需要验证）:")
    print("- stock_financial_hk_report_em(symbol='00700')")
    print("- stock_financial_hk_profit_em(symbol='00700')  # 需要验证是否存在")
    print("- stock_financial_hk_cashflow_em(symbol='00700')  # 需要验证是否存在")

def main():
    """
    主函数
    """
    # 测试腾讯控股（00700）
    print("测试港股：腾讯控股（00700）")
    results = test_hk_financial_interfaces("00700")
    
    # 对比说明
    compare_with_a_stock()
    
    # 如果测试成功，可以尝试其他港股
    if results:
        print("\n" + "=" * 80)
        print("可以尝试测试其他港股:")
        print("=" * 80)
        print("- 03690 (美团)")
        print("- 09988 (阿里巴巴-SW)")
        print("- 01810 (小米集团-W)")
        print("- 02318 (中国平安)")

if __name__ == "__main__":
    main()

