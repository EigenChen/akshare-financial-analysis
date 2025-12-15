# -*- coding: utf-8 -*-
"""
测试更新后的港股适配层
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from hk_financial_adapter import get_hk_annual_data, extract_year_data_hk, get_value_from_row_hk

print("=" * 80)
print("测试更新后的港股适配层")
print("=" * 80)

symbol = "00700"
results = get_hk_annual_data(symbol, 2020, 2024)

print("\n获取结果:")
for k, v in results.items():
    if v is not None:
        print(f"  {k}: {type(v).__name__}, shape={v.shape if hasattr(v, 'shape') else 'N/A'}")
        if hasattr(v, 'columns'):
            print(f"    列名（前10个）: {list(v.columns)[:10]}")
    else:
        print(f"  {k}: None")

# 测试提取年份数据
if results['profit'] is not None:
    print("\n测试提取2024年利润表数据:")
    profit_2024 = extract_year_data_hk(results['profit'], 2024)
    if profit_2024 is not None:
        print(f"  成功提取，包含 {len(profit_2024)} 个字段")
        # 测试获取营业收入
        revenue = get_value_from_row_hk(profit_2024, 'OPERATE_INCOME', "-")
        print(f"  营业收入: {revenue} 亿元（港币）")
        
        # 测试获取归母净利润
        profit = get_value_from_row_hk(profit_2024, 'PARENT_NETPROFIT', "-")
        print(f"  归母净利润: {profit} 亿元（港币）")
    else:
        print("  未能提取2024年数据")

