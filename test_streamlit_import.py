# -*- coding: utf-8 -*-
"""
测试在Streamlit环境中导入hk_financial_analysis_full模块
"""
import sys
import importlib.util

# 模拟Streamlit环境（导入streamlit模块）
try:
    import streamlit
    print("[OK] Streamlit模块已导入")
except ImportError:
    print("[WARNING] Streamlit模块未安装，但会测试导入逻辑")

# 测试导入hk_financial_analysis_full
print("\n测试导入 hk_financial_analysis_full.py...")
try:
    spec = importlib.util.spec_from_file_location("hk_financial_analysis", "hk_financial_analysis_full.py")
    hk_financial_analysis = importlib.util.module_from_spec(spec)
    sys.modules["hk_financial_analysis"] = hk_financial_analysis
    spec.loader.exec_module(hk_financial_analysis)
    print("[OK] 导入成功！")
except Exception as e:
    print(f"[FAIL] 导入失败: {e}")
    import traceback
    traceback.print_exc()

