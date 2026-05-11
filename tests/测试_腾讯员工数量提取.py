# -*- coding: utf-8 -*-
"""
测试腾讯控股（00700）员工数量提取功能

使用方法：
1. 确保年报PDF文件在指定目录中
2. 运行此脚本进行测试
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.hk.employee_extractor import (
    get_employee_extractor,
    extract_employee_count_by_company,
    extract_and_save_to_csv
)


def test_tencent_extractor():
    """测试腾讯控股的员工数量提取"""
    
    print("=" * 80)
    print("测试腾讯控股（00700）员工数量提取")
    print("=" * 80)
    
    # 测试参数
    pdf_dir = "年报PDF"
    symbol = "00700"
    start_year = 2020
    end_year = 2024
    
    # 检查PDF目录是否存在
    if not os.path.exists(pdf_dir):
        print(f"[ERROR] PDF目录不存在: {pdf_dir}")
        print("请确保年报PDF文件在指定目录中")
        return
    
    # 检查是否有PDF文件
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"[WARNING] 目录中没有找到PDF文件: {pdf_dir}")
        return
    
    print(f"\n[INFO] 找到 {len(pdf_files)} 个PDF文件")
    
    # 测试1: 检查提取器是否可用
    print("\n" + "-" * 80)
    print("测试1: 检查提取器")
    print("-" * 80)
    extractor = get_employee_extractor(symbol)
    if extractor:
        print(f"[OK] 找到 {extractor.company_name} ({extractor.symbol}) 的提取器")
    else:
        print(f"[FAIL] 未找到 {symbol} 的提取器")
        return
    
    # 测试2: 提取单个年份（如果有2024年的年报）
    print("\n" + "-" * 80)
    print("测试2: 提取单个PDF文件")
    print("-" * 80)
    
    # 查找2024年的年报
    test_year = 2024
    possible_names = [
        f"{symbol}_{test_year}年年度报告.pdf",
        f"{symbol}_{test_year}年度报告.pdf",
        f"{symbol}_{test_year}.pdf",
    ]
    
    test_pdf_path = None
    for filename in possible_names:
        pdf_path = os.path.join(pdf_dir, filename)
        if os.path.exists(pdf_path):
            test_pdf_path = pdf_path
            break
    
    if test_pdf_path:
        print(f"测试文件: {test_pdf_path}")
        count = extractor.extract(test_pdf_path, verbose=True)
        if count:
            print(f"\n[OK] 成功提取 {test_year} 年员工数量: {count:,} 人")
        else:
            print(f"\n[WARNING] 未能提取 {test_year} 年员工数量")
    else:
        print(f"[INFO] 未找到 {test_year} 年的年报PDF，跳过单文件测试")
    
    # 测试3: 批量提取多年数据
    print("\n" + "-" * 80)
    print(f"测试3: 批量提取 {start_year}-{end_year} 年数据")
    print("-" * 80)
    
    results = extract_employee_count_by_company(
        pdf_dir, symbol, start_year, end_year, verbose=True
    )
    
    # 显示结果
    print("\n" + "=" * 80)
    print("提取结果汇总")
    print("=" * 80)
    
    success_count = 0
    for year in sorted(results.keys()):
        count = results[year]
        if count:
            print(f"{year}年: {count:,} 人 ✓")
            success_count += 1
        else:
            print(f"{year}年: 未找到 ✗")
    
    print(f"\n成功提取: {success_count}/{len(results)} 年")
    
    # 测试4: 保存为CSV
    print("\n" + "-" * 80)
    print("测试4: 保存为CSV文件")
    print("-" * 80)
    
    csv_path = extract_and_save_to_csv(
        pdf_dir, symbol, start_year, end_year, output_dir=".", verbose=True
    )
    
    if csv_path and os.path.exists(csv_path):
        print(f"\n[OK] CSV文件已成功保存: {csv_path}")
        
        # 显示CSV内容
        print("\nCSV文件内容:")
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            print(f.read())
    else:
        print("\n[WARNING] CSV文件保存失败")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    test_tencent_extractor()

