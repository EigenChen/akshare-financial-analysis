# -*- coding: utf-8 -*-
"""
详细测试港股财务报表接口
"""
import akshare as ak
import pandas as pd
import sys

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

symbol = "00700"  # 腾讯控股

print("=" * 80)
print(f"详细测试港股财务报表接口 - 股票代码: {symbol}")
print("=" * 80)

# 1. 测试 stock_financial_hk_report_em
print("\n1. 测试 stock_financial_hk_report_em")
print("-" * 80)
try:
    report = ak.stock_financial_hk_report_em(symbol=symbol)
    print(f"返回类型: {type(report)}")
    if report is not None:
        print(f"是否为空: {report.empty if hasattr(report, 'empty') else 'N/A'}")
        if hasattr(report, 'shape'):
            print(f"数据形状: {report.shape}")
        if hasattr(report, 'columns'):
            print(f"列名: {list(report.columns)}")
            print(f"\n前3行数据:")
            print(report.head(3))
    else:
        print("返回值为 None")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

# 2. 测试 stock_financial_hk_analysis_indicator_em
print("\n2. 测试 stock_financial_hk_analysis_indicator_em")
print("-" * 80)
try:
    indicator = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol)
    print(f"返回类型: {type(indicator)}")
    if indicator is not None:
        print(f"是否为空: {indicator.empty if hasattr(indicator, 'empty') else 'N/A'}")
        if hasattr(indicator, 'shape'):
            print(f"数据形状: {indicator.shape}")
        if hasattr(indicator, 'columns'):
            print(f"列名: {list(indicator.columns)}")
            print(f"\n前3行数据:")
            print(indicator.head(3))
    else:
        print("返回值为 None")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

# 3. 测试 stock_hk_financial_indicator_em
print("\n3. 测试 stock_hk_financial_indicator_em")
print("-" * 80)
try:
    financial = ak.stock_hk_financial_indicator_em(symbol=symbol)
    print(f"返回类型: {type(financial)}")
    if financial is not None:
        print(f"是否为空: {financial.empty if hasattr(financial, 'empty') else 'N/A'}")
        if hasattr(financial, 'shape'):
            print(f"数据形状: {financial.shape}")
        if hasattr(financial, 'columns'):
            print(f"列名: {list(financial.columns)}")
            print(f"\n前3行数据:")
            print(financial.head(3))
    else:
        print("返回值为 None")
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

# 4. 尝试其他可能的接口
print("\n4. 查找其他可能的港股财务报表接口")
print("-" * 80)
hk_methods = [m for m in dir(ak) if 'hk' in m.lower() and ('financial' in m.lower() or 'profit' in m.lower() or 'balance' in m.lower() or 'cashflow' in m.lower() or 'report' in m.lower())]
print(f"找到的港股相关接口: {hk_methods}")

# 5. 总结
print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print("如果接口返回空数据，可能的原因:")
print("1. 该股票代码格式不正确")
print("2. 接口需要其他参数")
print("3. 数据源暂时不可用")
print("4. 该股票可能没有财务数据")

