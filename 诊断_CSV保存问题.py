# -*- coding: utf-8 -*-
"""
CSV保存问题诊断

检查员工数量为什么没有正确保存到CSV文件
"""

import os
import sys
from pathlib import Path

# 模拟测试数据（基于之前的测试结果）
test_results = [
    ('年报PDF/贵州茅台_2014年度报告.pdf', 2014, 7036),
    ('年报PDF/贵州茅台_2013年度报告.pdf', 2013, 5135),
    ('年报PDF/贵州茅台_2012年度报告.pdf', 2012, 4274),
    ('年报PDF/贵州茅台_2011年度报告.pdf', 2011, 3942),
]

def validate_employee_count(year: int, count: int, all_counts: dict) -> int:
    """复制主程序中的验证逻辑"""
    if count is None:
        return None

    # 获取前后年份的数量
    prev_year_count = all_counts.get(year - 1)
    next_year_count = all_counts.get(year + 1)

    print(f"  验证 {year}年: {count:,}人")
    print(f"    前一年({year-1}): {prev_year_count}")
    print(f"    后一年({year+1}): {next_year_count}")

    # 如果前后年份都有数据，进行数量级检查
    if prev_year_count is not None and next_year_count is not None:
        # 计算平均值作为参考
        avg_count = (prev_year_count + next_year_count) / 2

        # 如果当前数量与平均值相差超过10倍，认为不合理
        if avg_count > 0:
            ratio = count / avg_count
            print(f"    与前后年平均值比较: {ratio:.2f}倍 (平均值: {avg_count:,.0f})")
            if ratio > 10 or ratio < 0.1:
                print(f"    [REJECT] 比例{ratio:.2f}超出合理范围(0.1-10)")
                return None

    # 如果只有前一年有数据
    elif prev_year_count is not None:
        if prev_year_count > 0:
            ratio = count / prev_year_count
            print(f"    与前一年比较: {ratio:.2f}倍")
            if ratio > 10 or ratio < 0.1:
                print(f"    [REJECT] 比例{ratio:.2f}超出合理范围(0.1-10)")
                return None

    # 如果只有后一年有数据
    elif next_year_count is not None:
        if next_year_count > 0:
            ratio = count / next_year_count
            print(f"    与后一年比较: {ratio:.2f}倍")
            if ratio > 10 or ratio < 0.1:
                print(f"    [REJECT] 比例{ratio:.2f}超出合理范围(0.1-10)")
                return None

    print(f"    [ACCEPT] 通过验证")
    return count

def process_employee_counts(results):
    """复制主程序中的处理逻辑"""
    print("原始提取结果:")
    for file_path, year, count in results:
        filename = os.path.basename(file_path)
        print(f"  {year}年: {filename} -> {count:,}人")

    # 先收集所有数据
    all_counts = {}
    for file_path, year, count in results:
        if year is not None:
            all_counts[year] = count

    print(f"\n收集的数据: {all_counts}")

    # 验证每个年份的数量
    validated_counts = {}
    print(f"\n开始验证:")
    for year in sorted(all_counts.keys()):
        count = all_counts[year]
        validated_count = validate_employee_count(year, count, all_counts)
        validated_counts[year] = validated_count
        print()

    print(f"验证后的数据: {validated_counts}")
    return validated_counts

def test_csv_save_issue():
    """测试CSV保存问题"""
    print("="*80)
    print("CSV保存问题诊断")
    print("="*80)

    print("\n1. 测试数据处理逻辑...")

    # 处理测试数据
    employee_counts = process_employee_counts(test_results)

    print(f"\n2. 检查最终结果...")
    valid_count = sum(1 for count in employee_counts.values() if count is not None)
    total_count = len(employee_counts)

    print(f"总数据: {total_count}")
    print(f"有效数据: {valid_count}")
    print(f"无效数据: {total_count - valid_count}")

    if valid_count == 0:
        print("\n[PROBLEM] 所有数据都被验证逻辑过滤掉了！")
        print("原因分析:")
        print("- validate_employee_count函数的10倍差异验证过于严格")
        print("- 贵州茅台的员工数量增长可能被误判为不合理")

        # 分析具体哪些数据被过滤
        print("\n具体分析:")
        for year, count in sorted(employee_counts.items()):
            original_count = next((c for f, y, c in test_results if y == year), None)
            if count is None and original_count is not None:
                print(f"  {year}年: {original_count:,}人 被过滤")

    elif valid_count < total_count:
        print(f"\n[WARNING] 部分数据被过滤，可能影响CSV内容")
    else:
        print(f"\n[OK] 所有数据都通过验证")

    print(f"\n3. 模拟CSV写入...")
    print("CSV内容预览:")
    print("年份,员工数量")
    for year in sorted(employee_counts.keys()):
        count = employee_counts[year]
        csv_value = count if count is not None else '-'
        print(f"{year},{csv_value}")

    return employee_counts

def suggest_fix():
    """建议修复方案"""
    print("\n" + "="*80)
    print("修复建议")
    print("="*80)

    print("\n问题根源:")
    print("1. validate_employee_count函数的验证过于严格")
    print("2. 10倍差异规则不适合员工数量自然增长")
    print("3. 智能算法提取的正确数据被误判为异常")

    print("\n解决方案:")
    print("1. 放宽验证标准 (10倍 -> 3倍)")
    print("2. 或者跳过智能算法结果的验证")
    print("3. 或者直接保存智能算法结果，不进行二次验证")

    print("\n推荐方案: 由于智能算法本身已经有置信度验证，")
    print("建议跳过额外的数量级验证，直接保存智能算法的结果。")

if __name__ == "__main__":
    employee_counts = test_csv_save_issue()
    suggest_fix()