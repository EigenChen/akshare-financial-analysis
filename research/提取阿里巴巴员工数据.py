# -*- coding: utf-8 -*-
"""
提取阿里巴巴（09988）年报中的员工数量和总薪酬

使用方法：
python 提取阿里巴巴员工数据.py
"""

import os
import sys
import pdfplumber
import re
from typing import Optional, Dict
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.hk.employee_extractor import HKEmployeeExtractor


class AlibabaEmployeeExtractor(HKEmployeeExtractor):
    """
    阿里巴巴（09988）员工数量和总薪酬提取器
    
    需要分析阿里巴巴年报格式，实现提取逻辑
    """
    
    def __init__(self):
        super().__init__("09988", "阿里巴巴")
    
    def extract(self, pdf_path: str, verbose: bool = True) -> Optional[int]:
        """
        从阿里巴巴年报PDF中提取员工数量
        
        参数:
            pdf_path: PDF文件路径
            verbose: 是否显示详细调试信息
        
        返回:
            员工数量（整数），如果未找到返回None
        """
        if not os.path.exists(pdf_path):
            if verbose:
                print(f"[FAIL] 文件不存在: {pdf_path}")
            return None
        
        if verbose:
            print(f"正在打开PDF文件: {pdf_path}")
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if verbose:
                    print(f"[OK] PDF文件打开成功，共 {total_pages} 页")
                
                # 先尝试查找员工相关信息
                employee_keywords = [
                    "员工", "雇员", "employee", "staff", "personnel",
                    "人数", "数量", "number", "count"
                ]
                
                employee_count = None
                
                # 遍历每一页
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    
                    if not text:
                        continue
                    
                    # 检查是否包含员工相关关键词
                    has_employee_keyword = any(keyword in text for keyword in employee_keywords)
                    if not has_employee_keyword:
                        continue
                    
                    if verbose:
                        print(f"\n在第 {page_num} 页找到员工相关信息")
                        # 显示相关文本片段（用于分析格式）
                        lines = text.split('\n')
                        for i, line in enumerate(lines):
                            if any(kw in line for kw in employee_keywords):
                                # 显示前后各2行
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                context = '\n'.join(lines[start:end])
                                print(f"  相关文本片段:\n{context}\n")
                                break
                    
                    # 尝试多种模式匹配
                    patterns = [
                        # 通用模式：数字 + 人/名/位
                        r'(\d{1,3}(?:[,，]\d{3})*)\s*[人名位]',
                        # 包含"员工"的模式
                        r'员工[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*)\s*[人名位]',
                        r'雇员[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*)\s*[人名位]',
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            num_str = match.group(1)
                            num_str = num_str.replace(',', '').replace('，', '').strip()
                            try:
                                count = int(num_str)
                                if 10 <= count <= 1000000:  # 合理的员工数量范围
                                    employee_count = count
                                    if verbose:
                                        print(f"  [候选] 找到数字: {count:,} (模式: {pattern})")
                                    break
                            except ValueError:
                                continue
                        if employee_count:
                            break
                    
                    if employee_count:
                        break
                
                if employee_count and verbose:
                    print(f"\n[OK] 提取到员工数量: {employee_count:,} 人")
                elif verbose:
                    print("\n[WARNING] 未找到员工数量信息")
                
                return employee_count
                
        except Exception as e:
            if verbose:
                print(f"[FAIL] 处理PDF文件时出错: {e}")
                import traceback
                traceback.print_exc()
            return None
    
    def extract_total_salary(self, pdf_path: str, verbose: bool = True) -> Optional[float]:
        """
        从阿里巴巴年报PDF中提取总薪酬
        
        参数:
            pdf_path: PDF文件路径
            verbose: 是否显示详细调试信息
        
        返回:
            总薪酬（亿元，浮点数），如果未找到返回None
        """
        if not os.path.exists(pdf_path):
            if verbose:
                print(f"[FAIL] 文件不存在: {pdf_path}")
            return None
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                if verbose:
                    print(f"正在提取总薪酬信息...")
                
                # 查找薪酬相关关键词
                salary_keywords = [
                    "薪酬", "酬金", "salary", "compensation", "remuneration",
                    "工资", "wage", "pay"
                ]
                
                total_salary = None
                
                # 遍历每一页
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    
                    if not text:
                        continue
                    
                    # 检查是否包含薪酬相关关键词
                    has_salary_keyword = any(keyword in text for keyword in salary_keywords)
                    if not has_salary_keyword:
                        continue
                    
                    if verbose:
                        print(f"\n在第 {page_num} 页找到薪酬相关信息")
                        # 显示相关文本片段（用于分析格式）
                        lines = text.split('\n')
                        for i, line in enumerate(lines):
                            if any(kw in line for kw in salary_keywords):
                                # 显示前后各2行
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)
                                context = '\n'.join(lines[start:end])
                                print(f"  相关文本片段:\n{context}\n")
                                break
                    
                    # 尝试多种模式匹配
                    patterns = [
                        # 包含"薪酬"和"亿元"的模式
                        r'薪酬[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*亿元',
                        r'酬金[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*亿元',
                        # 包含"薪酬"和"万元"的模式（需要转换）
                        r'薪酬[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*万元',
                    ]
                    
                    candidates = []
                    for pattern in patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            num_str = match.group(1)
                            num_str = num_str.replace(',', '').replace('，', '').strip()
                            
                            # 判断单位
                            unit_multiplier = 0.0001 if '万元' in match.group(0) else 1.0
                            
                            try:
                                salary = float(num_str) * unit_multiplier
                                if 0.1 <= salary <= 10000:  # 合理的薪酬范围
                                    candidates.append(salary)
                                    if verbose:
                                        print(f"  [候选] 找到薪酬: {salary:.3f} 亿元 (模式: {pattern})")
                            except ValueError:
                                continue
                    
                    if candidates:
                        # 选择最大的（通常是当期数据）
                        total_salary = max(candidates)
                        if verbose:
                            print(f"  [OK] 选择最大薪酬: {total_salary:.3f} 亿元")
                        return total_salary
                
                if total_salary is None and verbose:
                    print("\n[WARNING] 未找到总薪酬信息")
                
                return total_salary
                
        except Exception as e:
            if verbose:
                print(f"[FAIL] 处理PDF文件时出错: {e}")
                import traceback
                traceback.print_exc()
            return None


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
        return
    
    # 创建提取器
    extractor = AlibabaEmployeeExtractor()
    
    # 提取数据
    print(f"\n开始提取 {start_year}-{end_year} 年数据...")
    results = extractor.extract_employee_and_salary_by_year(
        pdf_dir, start_year, end_year, verbose=True
    )
    
    # 显示结果
    print("\n" + "=" * 80)
    print("提取结果汇总")
    print("=" * 80)
    print(f"{'年份':<10} {'员工数量':<15} {'总薪酬（亿元）':<20}")
    print("-" * 80)
    
    for year in sorted(results.keys()):
        data = results[year]
        count = data.get('员工数量')
        salary = data.get('总薪酬')
        
        count_str = f"{count:,}" if count else "未找到"
        salary_str = f"{salary:.3f}" if salary else "未找到"
        
        print(f"{year:<10} {count_str:<15} {salary_str:<20}")
    
    # 保存为CSV
    csv_path = extractor.save_to_csv_with_salary(results, output_dir=pdf_dir)
    if csv_path:
        print(f"\n[OK] 数据已保存到: {csv_path}")


if __name__ == "__main__":
    main()

