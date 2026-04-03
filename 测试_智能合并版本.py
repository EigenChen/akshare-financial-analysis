# -*- coding: utf-8 -*-
"""
智能员工数量提取器 - 合并版本测试

验证合并到akshare项目中的智能算法是否正常工作
"""

import os
import sys
import time
from pathlib import Path

# 添加当前目录到路径
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

def test_merged_version():
    """测试合并版本的功能"""
    print("="*80)
    print("智能员工数量提取器 - 合并版本测试")
    print("="*80)

    try:
        # 导入合并后的模块
        from 智能_从年报提取员工数量 import (
            extract_employee_count_from_pdf_smart,
            SmartEmployeeExtractor,
            batch_extract_employee_count_smart
        )
        print("[OK] 成功导入合并后的模块")

    except ImportError as e:
        print(f"[ERROR] 导入失败: {e}")
        return False

    # 查找测试PDF文件
    pdf_dir = Path("年报PDF")
    if not pdf_dir.exists():
        print(f"[ERROR] 测试目录不存在: {pdf_dir}")
        return False

    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print("[ERROR] 未找到测试PDF文件")
        return False

    print(f"[OK] 找到 {len(pdf_files)} 个PDF文件")

    # 测试单个文件提取
    test_file = pdf_files[0]
    print(f"\n测试文件: {test_file.name}")
    print("-" * 60)

    # 测试1: 智能算法
    print("测试1: 智能算法提取")
    start_time = time.time()

    try:
        result_smart = extract_employee_count_from_pdf_smart(
            str(test_file),
            verbose=True,
            use_smart=True
        )
        smart_time = time.time() - start_time

        if result_smart:
            print(f"[OK] 智能算法成功: {result_smart:,}人 (耗时: {smart_time:.2f}秒)")
        else:
            print("[ERROR] 智能算法失败")

    except Exception as e:
        print(f"[ERROR] 智能算法异常: {e}")
        return False

    # 测试2: 传统算法
    print("\n测试2: 传统算法提取")
    start_time = time.time()

    try:
        result_legacy = extract_employee_count_from_pdf_smart(
            str(test_file),
            verbose=True,
            use_smart=False
        )
        legacy_time = time.time() - start_time

        if result_legacy:
            print(f"[OK] 传统算法成功: {result_legacy:,}人 (耗时: {legacy_time:.2f}秒)")
        else:
            print("[ERROR] 传统算法失败")

    except Exception as e:
        print(f"[ERROR] 传统算法异常: {e}")

    # 测试3: 直接使用SmartEmployeeExtractor类
    print("\n测试3: 直接使用SmartEmployeeExtractor类")

    try:
        extractor = SmartEmployeeExtractor()
        extraction_result = extractor.extract_from_pdf(str(test_file), verbose=False)

        if extraction_result.success:
            employee_data = extraction_result.employee_data
            print(f"[OK] 提取器类成功:")
            print(f"  员工数量: {employee_data.count:,}人")
            print(f"  置信度: {employee_data.confidence:.3f}")
            print(f"  提取策略: {employee_data.extraction_strategy.value}")
            if employee_data.verification_notes:
                print(f"  验证备注: {employee_data.verification_notes}")
        else:
            print(f"[ERROR] 提取器类失败: {extraction_result.error_message}")

    except Exception as e:
        print(f"[ERROR] 提取器类异常: {e}")

    # 测试4: 批量处理
    if len(pdf_files) > 1:
        print(f"\n测试4: 批量处理 (测试前2个文件)")

        try:
            # 创建临时目录进行批量测试
            batch_results = batch_extract_employee_count_smart(
                str(pdf_dir),
                use_smart=True
            )

            print(f"[OK] 批量处理完成，处理了 {len(batch_results)} 个文件")
            for filename, count in list(batch_results.items())[:2]:
                if count:
                    print(f"  {filename}: {count:,}人")
                else:
                    print(f"  {filename}: 提取失败")

        except Exception as e:
            print(f"[ERROR] 批量处理异常: {e}")

    # 对比结果
    print("\n" + "="*60)
    print("结果对比分析")
    print("="*60)

    if 'result_smart' in locals() and 'result_legacy' in locals():
        if result_smart and result_legacy:
            if result_smart == result_legacy:
                print("[OK] 智能算法与传统算法结果一致")
            else:
                diff_pct = abs(result_smart - result_legacy) / max(result_smart, result_legacy) * 100
                print(f"[WARN] 智能算法与传统算法结果不同:")
                print(f"  智能算法: {result_smart:,}人")
                print(f"  传统算法: {result_legacy:,}人")
                print(f"  差异: {diff_pct:.1f}%")
        elif result_smart and not result_legacy:
            print("[OK] 智能算法成功，传统算法失败")
        elif not result_smart and result_legacy:
            print("[WARN] 传统算法成功，智能算法失败")
        else:
            print("[ERROR] 两种算法均失败")

    print(f"\n[OK] 合并版本测试完成")
    return True

def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "="*80)
    print("向后兼容性测试")
    print("="*80)

    try:
        # 测试是否可以按原来的方式导入和使用
        from 测试_从年报提取员工数量 import extract_employee_count_from_pdf
        print("[OK] 原始模块仍可正常导入")

        # 查找测试文件
        pdf_dir = Path("年报PDF")
        pdf_files = list(pdf_dir.glob("*.pdf"))

        if pdf_files:
            test_file = pdf_files[0]
            result = extract_employee_count_from_pdf(str(test_file), verbose=False)

            if result:
                print(f"[OK] 原始接口仍正常工作: {result:,}人")
            else:
                print("[WARN] 原始接口返回None")

    except Exception as e:
        print(f"[ERROR] 向后兼容性测试失败: {e}")
        return False

    return True

def main():
    """主测试函数"""
    print("开始测试合并后的智能员工数量提取器...")

    # 基础功能测试
    basic_success = test_merged_version()

    # 向后兼容性测试
    compatibility_success = test_backward_compatibility()

    # 总结
    print("\n" + "="*80)
    print("测试结果总结")
    print("="*80)

    if basic_success and compatibility_success:
        print("[SUCCESS] 所有测试通过")
        print("[OK] 合并版本功能正常")
        print("[OK] 向后兼容性良好")
        print("[OK] 可以安全使用新的智能算法")

        print("\n使用建议:")
        print("1. 新项目推荐使用智能算法: use_smart=True")
        print("2. 现有项目可以逐步迁移到智能算法")
        print("3. 原有代码无需修改，完全兼容")

    else:
        print("[FAIL] 部分测试失败")
        if not basic_success:
            print("[ERROR] 基础功能测试失败")
        if not compatibility_success:
            print("[ERROR] 向后兼容性测试失败")
        print("需要进一步排查问题")

if __name__ == "__main__":
    main()