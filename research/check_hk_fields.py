# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data = ak.stock_financial_hk_analysis_indicator_em(symbol='00700')
print("字段列表:")
for i, col in enumerate(data.columns.tolist(), 1):
    print(f"{i:2d}. {col}")

print("\n示例数据（前3行）:")
if len(data) > 0:
    key_cols = ['REPORT_DATE', 'OPERATE_INCOME', 'HOLDER_PROFIT', 'GROSS_PROFIT', 
                'ROE_AVG', 'ROA', 'ROIC_YEARLY', 'FISCAL_YEAR', 'CURRENCY']
    available_cols = [col for col in key_cols if col in data.columns]
    print(data[available_cols].head(3))

