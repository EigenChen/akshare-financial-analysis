# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

symbol = "00700"

print("=" * 80)
print("查看港股报表实际字段名")
print("=" * 80)

# 利润表
profit = ak.stock_financial_hk_report_em(stock=symbol, symbol="利润表", indicator="年度")
print("\n利润表科目（包含'收入'或'营业额'或'营运'）:")
items = profit[profit['STD_ITEM_NAME'].str.contains('收入|营业额|营运', na=False)]['STD_ITEM_NAME'].unique()
for item in items:
    print(f"  - {item}")

print("\n利润表科目（包含'溢利'或'利润'）:")
items2 = profit[profit['STD_ITEM_NAME'].str.contains('溢利|利润', na=False)]['STD_ITEM_NAME'].unique()
for item in items2[:15]:
    print(f"  - {item}")

print("\n利润表科目（包含'费用'或'开支'）:")
items3 = profit[profit['STD_ITEM_NAME'].str.contains('费用|开支', na=False)]['STD_ITEM_NAME'].unique()
for item in items3:
    print(f"  - {item}")

# 资产负债表
balance = ak.stock_financial_hk_report_em(stock=symbol, symbol="资产负债表", indicator="年度")
print("\n资产负债表科目（包含'资产'）:")
items4 = balance[balance['STD_ITEM_NAME'].str.contains('资产', na=False)]['STD_ITEM_NAME'].unique()
for item in items4[:15]:
    print(f"  - {item}")

print("\n资产负债表科目（包含'现金'或'货币'）:")
items5 = balance[balance['STD_ITEM_NAME'].str.contains('现金|货币', na=False)]['STD_ITEM_NAME'].unique()
for item in items5:
    print(f"  - {item}")

# 现金流量表
cashflow = ak.stock_financial_hk_report_em(stock=symbol, symbol="现金流量表", indicator="年度")
print("\n现金流量表科目（包含'经营'或'现金'）:")
items6 = cashflow[cashflow['STD_ITEM_NAME'].str.contains('经营|现金', na=False)]['STD_ITEM_NAME'].unique()
for item in items6[:15]:
    print(f"  - {item}")

