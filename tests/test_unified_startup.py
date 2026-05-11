# -*- coding: utf-8 -*-
"""
检查统一财务工具是否能正常启动（模拟导入测试）
"""

import sys
import os
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_module(name, path):
    """动态加载模块"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def test_unified_tool_startup():
    """测试统一财务工具启动依赖"""
    print("=" * 80)
    print("测试统一财务工具启动依赖")
    print("=" * 80)

    # 检查关键文件是否存在
    key_files = [
        "A股财务分析自动化.py",
        "core/hk/financial_analysis_full.py",
        "core/hk/financial_adapter.py",
        "core/tools/report_downloader.py",
        "core/a_share/employee_extractor.py",
        "core/hk/employee_extractor.py"
    ]

    print("1. 检查关键文件存在性:")
    for file in key_files:
        if os.path.exists(file):
            print(f"  [OK] {file}")
        else:
            print(f"  [ERROR] {file} - 文件不存在")

    print("\n2. 测试模块加载:")
    try:
        # 测试智能员工提取模块加载
        emp_a = load_module("emp_a", str(ROOT / "core/a_share/employee_extractor.py"))
        print("  [OK] 智能员工提取模块加载成功")

        # 验证关键函数
        if hasattr(emp_a, 'batch_extract_employee_count_smart'):
            print("  [OK] batch_extract_employee_count_smart 函数可用")
        else:
            print("  [ERROR] batch_extract_employee_count_smart 函数不可用")

        print("\n3. 测试函数调用兼容性:")
        # 检查函数签名
        import inspect
        sig = inspect.signature(emp_a.batch_extract_employee_count_smart)
        params = list(sig.parameters.keys())
        print(f"  函数参数: {params}")

        # 检查必需参数
        required_params = ['pdf_dir', 'stock_code', 'use_smart']
        missing_params = []
        for param in required_params:
            if param not in params:
                missing_params.append(param)

        if not missing_params:
            print("  [OK] 函数参数兼容性检查通过")
        else:
            print(f"  [WARNING] 缺少参数: {missing_params}")

    except Exception as e:
        print(f"  [ERROR] 模块加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n[SUCCESS] 统一财务工具启动依赖检查完成！")
    return True

if __name__ == "__main__":
    test_unified_tool_startup()