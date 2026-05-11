# -*- coding: utf-8 -*-
"""
测试港股完整三大报表接口
"""
import akshare as ak
import pandas as pd
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

symbol = "00700"  # 腾讯控股

print("=" * 80)
print(f"测试港股完整三大报表接口 - 股票代码: {symbol}")
print("=" * 80)

results = {}

# 1. 测试资产负债表
print("\n1. 测试资产负债表...")
print("-" * 80)
try:
    balance_sheet = ak.stock_financial_hk_report_em(stock=symbol, symbol="资产负债表", indicator="年度")
    if balance_sheet is not None and not balance_sheet.empty:
        print(f"[OK] 资产负债表获取成功")
        print(f"数据形状: {balance_sheet.shape}")
        print(f"列名: {list(balance_sheet.columns)[:15]}...")  # 显示前15个列名
        print(f"\n前3行数据:")
        print(balance_sheet.head(3))
        results['balance_sheet'] = balance_sheet
    else:
        print("[FAIL] 资产负债表返回空数据")
except Exception as e:
    print(f"[FAIL] 资产负债表获取失败: {e}")
    import traceback
    traceback.print_exc()

# 2. 测试利润表
print("\n2. 测试利润表...")
print("-" * 80)
try:
    profit_sheet = ak.stock_financial_hk_report_em(stock=symbol, symbol="利润表", indicator="年度")
    if profit_sheet is not None and not profit_sheet.empty:
        print(f"[OK] 利润表获取成功")
        print(f"数据形状: {profit_sheet.shape}")
        print(f"列名: {list(profit_sheet.columns)[:15]}...")
        print(f"\n前3行数据:")
        print(profit_sheet.head(3))
        results['profit'] = profit_sheet
    else:
        print("[FAIL] 利润表返回空数据")
except Exception as e:
    print(f"[FAIL] 利润表获取失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 测试现金流量表
print("\n3. 测试现金流量表...")
print("-" * 80)
try:
    cashflow_sheet = ak.stock_financial_hk_report_em(stock=symbol, symbol="现金流量表", indicator="年度")
    if cashflow_sheet is not None and not cashflow_sheet.empty:
        print(f"[OK] 现金流量表获取成功")
        print(f"数据形状: {cashflow_sheet.shape}")
        print(f"列名: {list(cashflow_sheet.columns)[:15]}...")
        print(f"\n前3行数据:")
        print(cashflow_sheet.head(3))
        results['cashflow'] = cashflow_sheet
    else:
        print("[FAIL] 现金流量表返回空数据")
except Exception as e:
    print(f"[FAIL] 现金流量表获取失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试报告期类型
print("\n4. 测试报告期类型（indicator='报告期'）...")
print("-" * 80)
try:
    profit_report = ak.stock_financial_hk_report_em(stock=symbol, symbol="利润表", indicator="报告期")
    if profit_report is not None and not profit_report.empty:
        print(f"[OK] 报告期类型利润表获取成功")
        print(f"数据形状: {profit_report.shape}")
        print(f"列名: {list(profit_report.columns)[:10]}...")
    else:
        print("[FAIL] 报告期类型返回空数据")
except Exception as e:
    print(f"[FAIL] 报告期类型获取失败: {e}")

# 5. 总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print(f"成功获取的报表: {list(results.keys())}")

if results:
    print("\n[SUCCESS] 港股可以获取完整三大报表数据！")
    print("\n接口使用方法:")
    print("  资产负债表: ak.stock_financial_hk_report_em(stock='00700', symbol='资产负债表', indicator='年度')")
    print("  利润表: ak.stock_financial_hk_report_em(stock='00700', symbol='利润表', indicator='年度')")
    print("  现金流量表: ak.stock_financial_hk_report_em(stock='00700', symbol='现金流量表', indicator='年度')")
else:
    print("\n[FAIL] 未能获取任何报表数据")
    print("可能的原因:")
    print("1. 数据源暂时不可用")
    print("2. 接口参数不正确")
    print("3. 该股票可能没有财务数据")

