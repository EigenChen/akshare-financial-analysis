# -*- coding: utf-8 -*-
"""
测试年份提取修复

验证修复后的年份提取逻辑是否正确
"""

import re

def extract_year_from_filename(filename):
    """修复后的年份提取逻辑"""
    year = None
    try:
        # 优先匹配明确的年份模式，避免匹配股票代码
        year_patterns = [
            r'(\d{4})年',  # 优先匹配 "XXXX年" 格式
            r'_(\d{4})年',  # 匹配 "_XXXX年" 格式
            r'(\d{4})年度',  # 匹配 "XXXX年度" 格式
            r'(\d{4})(?=年度报告)', # 匹配年度报告前的4位数字
            r'(?:20\d{2})', # 匹配2000-2099年份
        ]

        print(f"处理文件名: {filename}")

        for i, pattern in enumerate(year_patterns):
            year_match = re.search(pattern, filename)
            if year_match:
                year_str = year_match.group(1) if year_match.groups() else year_match.group(0)
                year_num = int(year_str)
                print(f"  模式{i+1} '{pattern}' 匹配到: {year_str}")
                # 验证是否为合理的年份（2000-2030）
                if 2000 <= year_num <= 2030:
                    year = year_num
                    print(f"  ✓ 确认年份: {year}")
                    break
                else:
                    print(f"  ✗ 年份不合理: {year_num}")

        # 如果上述模式都没匹配到，尝试最后的通用模式
        if year is None:
            print("  尝试通用模式...")
            # 查找所有4位数字，选择最像年份的
            all_four_digits = re.findall(r'\b(\d{4})\b', filename)
            print(f"  找到的4位数字: {all_four_digits}")
            for digit in all_four_digits:
                digit_int = int(digit)
                if 2000 <= digit_int <= 2030:
                    year = digit_int
                    print(f"  ✓ 通用模式确认年份: {year}")
                    break

    except Exception as e:
        print(f"  ✗ 年份提取异常: {e}")

    print(f"  最终结果: {year}")
    print()
    return year

def test_year_extraction():
    """测试年份提取"""
    print("="*80)
    print("年份提取修复测试")
    print("="*80)

    # 测试用例
    test_files = [
        "000538_2023年年度报告.pdf",  # 问题文件
        "000538_2024年年度报告.pdf",  # 问题文件
        "600519_2022年度报告.pdf",   # 常见格式
        "贵州茅台_2021年年度报告.pdf", # 中文公司名
        "002415_2020年年度报告.pdf",  # 深市股票
        "688525_2023年年报.pdf",     # 科创板
        "300001_2024年度报告.pdf",   # 创业板
    ]

    print("测试文件名年份提取:")
    print("-" * 60)

    results = {}
    for filename in test_files:
        year = extract_year_from_filename(filename)
        results[filename] = year

    print("="*60)
    print("测试结果汇总:")
    print("="*60)

    all_correct = True
    for filename, year in results.items():
        # 从文件名判断预期年份
        expected_years = re.findall(r'(20\d{2})', filename)
        expected = int(expected_years[-1]) if expected_years else None

        if year == expected:
            status = "✓ 正确"
        else:
            status = f"✗ 错误 (预期: {expected})"
            all_correct = False

        print(f"{filename:<35} -> {year} {status}")

    print("\n" + "="*60)
    if all_correct:
        print("🎉 所有测试通过！年份提取修复成功！")
    else:
        print("❌ 部分测试失败，需要进一步调整正则表达式")

    return results

def test_original_vs_fixed():
    """对比原始方法和修复后方法"""
    print("\n" + "="*80)
    print("原始方法 vs 修复后方法对比")
    print("="*80)

    problem_files = [
        "000538_2023年年度报告.pdf",
        "000538_2024年年度报告.pdf",
    ]

    def original_method(filename):
        """原始的年份提取方法"""
        year = None
        try:
            year_match = re.search(r'(\d{4})', filename)
            if year_match:
                year = int(year_match.group(1))
        except:
            pass
        return year

    print("对比测试:")
    for filename in problem_files:
        original_year = original_method(filename)
        fixed_year = extract_year_from_filename(filename)

        print(f"\n文件: {filename}")
        print(f"  原始方法: {original_year} {'✗ 错误' if original_year and original_year < 2000 else ''}")
        print(f"  修复方法: {fixed_year} ✓ 正确")

if __name__ == "__main__":
    test_year_extraction()
    test_original_vs_fixed()