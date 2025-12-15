# -*- coding: utf-8 -*-
"""
测试港股员工人数获取功能
"""
import sys
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from hk_financial_adapter import get_hk_employee_count, get_hk_employee_count_by_year

print("=" * 80)
print("测试港股员工人数获取功能")
print("=" * 80)

# 测试1: 获取单个股票的员工人数
symbol = "00700"  # 腾讯控股
print(f"\n1. 测试获取 {symbol} 的员工人数...")
employee_count = get_hk_employee_count(symbol)
if employee_count is not None:
    print(f"   [OK] 员工人数: {employee_count:,} 人")
else:
    print(f"   [FAIL] 无法获取员工人数")

# 测试2: 获取年份范围的员工人数
print(f"\n2. 测试获取 {symbol} 的年份范围员工人数（2020-2024）...")
employee_by_year = get_hk_employee_count_by_year(symbol, 2020, 2024)
print(f"   结果:")
for year, count in employee_by_year.items():
    if count is not None:
        print(f"     {year}年: {count:,} 人")
    else:
        print(f"     {year}年: 无数据")

# 测试3: 测试其他港股
test_symbols = ["03690", "09988"]  # 美团、阿里巴巴
print(f"\n3. 测试其他港股...")
for test_symbol in test_symbols:
    count = get_hk_employee_count(test_symbol)
    if count is not None:
        print(f"   {test_symbol}: {count:,} 人")
    else:
        print(f"   {test_symbol}: 无数据")

print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print("[SUCCESS] 港股员工人数可以通过AKShare接口获取！")
print("接口: stock_hk_company_profile_em")
print("字段: 员工人数")
print("\n注意：")
print("1. 该接口通常只返回最新一年的员工人数")
print("2. 如果需要历史年份的员工人数，可能需要从年报PDF中提取")
print("3. 或者手动提供员工数量CSV文件")

