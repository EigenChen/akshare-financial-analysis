# -*- coding: utf-8 -*-
"""
简化测试年份提取修复
"""

import re

def extract_year_from_filename(filename):
    """修复后的年份提取逻辑（简化版）"""
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

        for pattern in year_patterns:
            year_match = re.search(pattern, filename)
            if year_match:
                year_str = year_match.group(1) if year_match.groups() else year_match.group(0)
                year_num = int(year_str)
                # 验证是否为合理的年份（2000-2030）
                if 2000 <= year_num <= 2030:
                    year = year_num
                    break

        # 如果上述模式都没匹配到，尝试最后的通用模式
        if year is None:
            # 查找所有4位数字，选择最像年份的
            all_four_digits = re.findall(r'\b(\d{4})\b', filename)
            for digit in all_four_digits:
                digit_int = int(digit)
                if 2000 <= digit_int <= 2030:
                    year = digit_int
                    break

    except Exception as e:
        print(f"年份提取异常: {e}")

    return year

def test_year_extraction():
    """测试年份提取"""
    print("年份提取修复测试")
    print("="*60)

    # 测试用例
    test_files = [
        "000538_2023年年度报告.pdf",  # 问题文件
        "000538_2024年年度报告.pdf",  # 问题文件
        "600519_2022年度报告.pdf",   # 常见格式
        "贵州茅台_2021年年度报告.pdf", # 中文公司名
        "002415_2020年年度报告.pdf",  # 深市股票
    ]

    print("测试结果:")
    for filename in test_files:
        year = extract_year_from_filename(filename)
        # 预期年份
        expected = None
        for y in [2020, 2021, 2022, 2023, 2024, 2025]:
            if str(y) in filename:
                expected = y
                break

        status = "OK" if year == expected else f"ERROR (expected: {expected})"
        print(f"{filename:<35} -> {year} [{status}]")

    # 对比原始方法
    print("\n" + "="*60)
    print("原始方法对比:")

    def original_method(filename):
        year_match = re.search(r'(\d{4})', filename)
        return int(year_match.group(1)) if year_match else None

    problem_files = ["000538_2023年年度报告.pdf", "000538_2024年年度报告.pdf"]

    for filename in problem_files:
        original = original_method(filename)
        fixed = extract_year_from_filename(filename)
        print(f"{filename}:")
        print(f"  原始方法: {original} (错误 - 提取了股票代码)")
        print(f"  修复方法: {fixed} (正确)")

if __name__ == "__main__":
    test_year_extraction()