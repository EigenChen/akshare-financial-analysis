# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from hk_financial_adapter import convert_hk_long_to_wide

symbol = "00700"

print("=" * 80)
print("调试港股字段映射")
print("=" * 80)

# 获取利润表长格式数据
profit_long = ak.stock_financial_hk_report_em(stock=symbol, symbol="利润表", indicator="年度")
print(f"\n长格式数据形状: {profit_long.shape}")
print(f"长格式列名: {list(profit_long.columns)}")

# 转换为宽格式
profit_wide = convert_hk_long_to_wide(profit_long, '利润表')
print(f"\n宽格式数据形状: {profit_wide.shape}")
print(f"宽格式列名（前20个）: {list(profit_wide.columns)[:20]}")

# 检查是否包含营业收入相关列
print("\n检查营业收入相关列:")
for col in profit_wide.columns:
    if '收入' in str(col) or '营业额' in str(col) or 'OPERATE_INCOME' in str(col):
        print(f"  找到: {col}")
        if 'REPORT_DATE' in profit_wide.columns:
            print(f"    2024年值: {profit_wide[profit_wide['REPORT_DATE'].astype(str).str.contains('2024', na=False)][col].values}")

# 检查是否包含归母净利润相关列
print("\n检查归母净利润相关列:")
for col in profit_wide.columns:
    if '溢利' in str(col) or '利润' in str(col) or 'PARENT_NETPROFIT' in str(col):
        print(f"  找到: {col}")
        if 'REPORT_DATE' in profit_wide.columns:
            print(f"    2024年值: {profit_wide[profit_wide['REPORT_DATE'].astype(str).str.contains('2024', na=False)][col].values}")

