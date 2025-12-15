# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import sys
import inspect

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

symbol = "00700"

print("=" * 80)
print("测试 stock_financial_hk_report_em 接口")
print("=" * 80)

# 检查接口签名
try:
    func = ak.stock_financial_hk_report_em
    sig = inspect.signature(func)
    print(f"\n接口签名: {sig}")
    print(f"参数: {list(sig.parameters.keys())}")
except Exception as e:
    print(f"获取签名失败: {e}")

# 测试不同的参数组合
print("\n测试不同的参数组合:")
print("-" * 80)

# 测试1: 只传symbol
print("\n1. 测试: stock_financial_hk_report_em(symbol='00700')")
try:
    result = ak.stock_financial_hk_report_em(symbol=symbol)
    print(f"   返回类型: {type(result)}")
    if result is not None:
        if hasattr(result, 'empty'):
            print(f"   是否为空: {result.empty}")
        if hasattr(result, 'shape'):
            print(f"   数据形状: {result.shape}")
        if hasattr(result, 'columns') and len(result.columns) > 0:
            print(f"   列名: {list(result.columns)[:10]}...")  # 只显示前10个
            print(f"\n   前3行数据:")
            print(result.head(3))
    else:
        print("   返回值为 None")
except Exception as e:
    print(f"   错误: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 尝试其他可能的参数
print("\n2. 检查接口文档或源码...")
try:
    # 尝试查看函数的文档字符串
    doc = func.__doc__
    if doc:
        print("   函数文档:")
        print(f"   {doc[:500]}...")  # 只显示前500字符
except:
    print("   无法获取函数文档")

# 测试3: 尝试其他港股代码
print("\n3. 测试其他港股代码:")
test_symbols = ["03690", "09988"]
for test_symbol in test_symbols:
    try:
        result = ak.stock_financial_hk_report_em(symbol=test_symbol)
        if result is not None and hasattr(result, 'empty'):
            print(f"   {test_symbol}: 空={result.empty}, 形状={result.shape if hasattr(result, 'shape') else 'N/A'}")
        else:
            print(f"   {test_symbol}: 返回 None")
    except Exception as e:
        print(f"   {test_symbol}: 错误 - {e}")

print("\n" + "=" * 80)
print("结论:")
print("=" * 80)
print("如果 stock_financial_hk_report_em 返回空数据，可能的原因:")
print("1. 接口需要其他参数（如报告期、报告类型等）")
print("2. 接口可能已废弃或数据源不可用")
print("3. 该接口可能只返回特定类型的数据")
print("\n建议:")
print("1. 查看AKShare官方文档")
print("2. 查看AKShare GitHub仓库的Issue")
print("3. 考虑使用其他数据源（如港交所官网、Wind、同花顺等）")

