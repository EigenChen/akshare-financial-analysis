# -*- coding: utf-8 -*-
"""
提取阿里巴巴（09988）年报中的员工数量和总薪酬

使用方法：
python 提取阿里巴巴09988员工数据.py
"""

import os
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.hk.employee_extractor import extract_employee_and_salary_by_company, extract_and_save_to_csv


def main():
    """主函数：提取阿里巴巴年报中的员工数量和总薪酬"""
    pdf_dir = r"F:/移动云盘同步文件夹/13600004997/生活/投资/旗下公司/阿里巴巴 09988"
    symbol = "09988"
    start_year = 2020
    end_year = 2025
    
    print("=" * 80)
    print(f"提取阿里巴巴（{symbol}）年报中的员工数量和总薪酬")
    print("=" * 80)
    
    # 检查目录是否存在
    if not os.path.exists(pdf_dir):
        print(f"[ERROR] 目录不存在: {pdf_dir}")
        print("请检查路径是否正确")
        return
    
    # 提取数据
    print(f"\n开始提取 {start_year}-{end_year} 年数据...")
    print("=" * 80)
    
    results = extract_employee_and_salary_by_company(
        pdf_dir, symbol, start_year, end_year, verbose=True
    )
    
    # 显示结果
    print("\n" + "=" * 80)
    print("提取结果汇总")
    print("=" * 80)
    print(f"{'年份':<10} {'员工数量':<20} {'总薪酬（亿元）':<20}")
    print("-" * 80)
    
    for year in sorted(results.keys()):
        data = results[year]
        count = data.get('员工数量')
        salary = data.get('总薪酬')
        
        count_str = f"{count:,} 人" if count else "未找到"
        salary_str = f"{salary:.3f} 亿元" if salary else "未找到"
        
        print(f"{year:<10} {count_str:<20} {salary_str:<20}")
    
    # 保存为CSV
    print("\n" + "=" * 80)
    csv_path = extract_and_save_to_csv(
        pdf_dir, symbol, start_year, end_year, output_dir=pdf_dir, verbose=True
    )
    
    if csv_path:
        print(f"\n[OK] 数据已保存到: {csv_path}")
        print("\n提取完成！")
    else:
        print("\n[WARNING] CSV文件保存失败")


if __name__ == "__main__":
    main()

