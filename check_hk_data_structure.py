# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

symbol = "00700"

print("=" * 80)
print("分析港股三大报表数据结构")
print("=" * 80)

# 1. 利润表
print("\n1. 利润表数据结构:")
profit = ak.stock_financial_hk_report_em(stock=symbol, symbol="利润表", indicator="年度")
print(f"数据形状: {profit.shape}")
print(f"列名: {list(profit.columns)}")
print(f"\n前10行数据:")
print(profit[['REPORT_DATE', 'STD_ITEM_NAME', 'AMOUNT']].head(10))
print(f"\n利润表科目名称（前30个）:")
items = profit['STD_ITEM_NAME'].unique()[:30]
for i, item in enumerate(items, 1):
    print(f"  {i:2d}. {item}")

# 2. 资产负债表
print("\n2. 资产负债表数据结构:")
balance = ak.stock_financial_hk_report_em(stock=symbol, symbol="资产负债表", indicator="年度")
print(f"数据形状: {balance.shape}")
print(f"\n资产负债表科目名称（前30个）:")
items = balance['STD_ITEM_NAME'].unique()[:30]
for i, item in enumerate(items, 1):
    print(f"  {i:2d}. {item}")

# 3. 现金流量表
print("\n3. 现金流量表数据结构:")
cashflow = ak.stock_financial_hk_report_em(stock=symbol, symbol="现金流量表", indicator="年度")
print(f"数据形状: {cashflow.shape}")
print(f"\n现金流量表科目名称（前30个）:")
items = cashflow['STD_ITEM_NAME'].unique()[:30]
for i, item in enumerate(items, 1):
    print(f"  {i:2d}. {item}")

# 4. 检查报告期格式
print("\n4. 报告期格式:")
print(f"利润表报告期示例: {profit['REPORT_DATE'].unique()[:5]}")
print(f"会计年度示例: {profit['FISCAL_YEAR'].unique()[:5]}")

