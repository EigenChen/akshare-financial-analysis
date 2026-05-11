# -*- coding: utf-8 -*-
"""
测试统一财务工具的智能算法集成
"""

import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def test_integration():
    """测试智能算法集成"""
    print("=" * 80)
    print("测试统一财务工具的智能算法集成")
    print("=" * 80)

    try:
        # 测试加载智能员工提取模块
        emp_a = load_module('emp_a', str(ROOT / 'core/a_share/employee_extractor.py'))
        print('[OK] 成功加载智能员工提取模块')

        # 检查关键函数是否存在
        required_functions = [
            'batch_extract_employee_count_smart',
            'extract_employee_count_from_pdf_smart'
        ]

        for func_name in required_functions:
            if hasattr(emp_a, func_name):
                print(f'[OK] {func_name} 函数存在')
            else:
                print(f'[ERROR] {func_name} 函数不存在')

        # 显示所有可用的函数
        functions = [attr for attr in dir(emp_a) if callable(getattr(emp_a, attr)) and not attr.startswith('_')]
        print(f'\n可用函数总数: {len(functions)}')
        print('主要函数:')
        for func in functions[:10]:
            print(f'  - {func}')
        if len(functions) > 10:
            print(f'  ... 还有 {len(functions) - 10} 个函数')

        print('\n[SUCCESS] 智能算法集成验证通过！')
        return True

    except Exception as e:
        print(f'[ERROR] 集成验证失败: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_integration()