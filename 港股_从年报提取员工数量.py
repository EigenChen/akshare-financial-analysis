# -*- coding: utf-8 -*-
"""
从港股年报PDF中提取员工数量信息

功能：
1. 打开指定的港股年报PDF文件
2. 查找"员工情况"相关内容（支持中英文）
3. 分析表格结构
4. 提取员工数量合计对应的数值

注意：港股年报可能使用中英文混合，需要同时支持两种语言的关键词
"""

import os
import re
import csv
import pdfplumber
from typing import Optional, Dict, List, Tuple
from pathlib import Path
import sys

# 避免在 Streamlit 环境替换 stdout，防止 “I/O operation on closed file”
def is_streamlit_env():
    try:
        import streamlit  # noqa: F401
        return True
    except ImportError:
        return any('streamlit' in str(m) for m in sys.modules.keys())

if sys.platform == 'win32' and not is_streamlit_env():
    try:
        import io
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

def extract_employee_count_from_hk_pdf(pdf_path: str, verbose: bool = True) -> Optional[int]:
    """
    从港股年报PDF中提取员工数量
    
    参数:
        pdf_path: PDF文件路径
        verbose: 是否显示详细调试信息
    
    返回:
        员工数量（整数），如果未找到返回None
    """
    if not os.path.exists(pdf_path):
        print(f"[FAIL] 文件不存在: {pdf_path}")
        return None
    
    if verbose:
        print(f"正在打开PDF文件: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            if verbose:
                print(f"[OK] PDF文件打开成功，共 {total_pages} 页")
            
            # 港股年报关键词（中英文混合）
            keywords = [
                # 中文关键词
                "在职员工的数量合计",
                "在职员工数量合计",
                "员工数量合计",
                "员工总数",
                "在职员工总数",
                "员工人数合计",
                "雇员总数",
                "雇员人数合计",
                "员工人数",
                "雇员人数",
                # 英文关键词
                "Total number of employees",
                "Total employees",
                "Number of employees",
                "Employee count",
                "Total staff",
                "Staff number",
                # 繁体中文关键词
                "在職員工的數量合計",
                "在職員工數量合計",
                "員工數量合計",
                "員工總數",
                "在職員工總數",
                "員工人數合計",
                "僱員總數",
                "僱員人數合計",
            ]
            
            employee_count = None
            
            # 遍历每一页
            for page_num, page in enumerate(pdf.pages, 1):
                # 提取文本
                text = page.extract_text()
                
                if not text:
                    continue
                
                # 检查是否包含员工相关关键词
                has_employee_keyword = any(keyword in text for keyword in keywords)
                has_employee_section = (
                    ("员工" in text or "雇员" in text or "employee" in text.lower() or "staff" in text.lower()) and 
                    ("情况" in text or "构成" in text or "information" in text.lower() or "composition" in text.lower())
                )
                
                if has_employee_keyword or has_employee_section:
                    if verbose:
                        print(f"\n在第 {page_num} 页找到员工相关信息")
                    
                    # 尝试提取表格
                    tables = page.extract_tables()
                    if tables:
                        if verbose:
                            print(f"  找到 {len(tables)} 个表格")
                        
                        # 分析每个表格
                        for table_idx, table in enumerate(tables):
                            if verbose:
                                print(f"  分析表格 {table_idx + 1}:")
                            employee_count = analyze_table_for_employee_count(table, keywords, verbose=verbose)
                            if employee_count is not None:
                                if verbose:
                                    print(f"  [OK] 在表格 {table_idx + 1} 中找到员工数量: {employee_count:,}")
                                return employee_count
                    
                    # 如果表格提取失败，尝试从文本中提取
                    employee_count = extract_employee_count_from_text(text, keywords)
                    if employee_count is not None:
                        if verbose:
                            print(f"  [OK] 从文本中提取到员工数量: {employee_count:,}")
                        return employee_count
            
            if employee_count is None and verbose:
                print("\n[WARNING] 未找到员工数量信息")
                print("提示：可以尝试查看PDF中的'员工情况'、'员工构成'或'Employee Information'章节")
            
            return employee_count
            
    except Exception as e:
        print(f"[FAIL] 处理PDF文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def is_reasonable_employee_count(num: int) -> bool:
    """
    判断数字是否是合理的员工数量
    
    参数:
        num: 数字
    
    返回:
        如果合理返回True，否则返回False
    """
    # 员工数量通常在 10 到 1000000 之间
    return 10 <= num <= 1000000

def analyze_table_for_employee_count(table: List[List], keywords: List[str], verbose: bool = False) -> Optional[int]:
    """
    分析表格，查找员工数量
    
    参数:
        table: 表格数据（二维列表）
        keywords: 关键词列表
        verbose: 是否显示详细调试信息
    
    返回:
        员工数量（整数），如果未找到返回None
    """
    if not table:
        return None
    
    candidates = []
    
    # 优先查找包含"合计"或"Total"的关键词行
    for row_idx, row in enumerate(table):
        row_text = " ".join([str(cell) if cell else "" for cell in row])
        
        # 检查是否包含合计相关的关键词
        for keyword in keywords:
            if keyword in row_text and ("合计" in keyword or "Total" in keyword or "total" in keyword.lower()):
                if verbose:
                    print(f"    找到合计关键词 '{keyword}' 在第 {row_idx + 1} 行（高优先级）")
                
                # 在这一行查找数字
                numbers = extract_numbers_from_row(row)
                if numbers:
                    valid_numbers = [num for num in numbers if isinstance(num, int) and is_reasonable_employee_count(num)]
                    if valid_numbers:
                        max_num = max(valid_numbers)
                        candidates.append((max_num, f"合计关键词行{row_idx+1}", 1))
                        if verbose:
                            print(f"    [OK] 候选数字: {max_num:,} (来自合计关键词行，优先级1)")
    
    # 查找其他关键词行
    for row_idx, row in enumerate(table):
        row_text = " ".join([str(cell) if cell else "" for cell in row])
        
        for keyword in keywords:
            if keyword in row_text and "合计" not in keyword and "Total" not in keyword and "total" not in keyword.lower():
                if verbose:
                    print(f"    找到关键词 '{keyword}' 在第 {row_idx + 1} 行")
                
                numbers = extract_numbers_from_row(row)
                if numbers:
                    for num in numbers:
                        if isinstance(num, int) and is_reasonable_employee_count(num):
                            candidates.append((num, f"关键词行{row_idx+1}", 2))
                            if verbose:
                                print(f"    [OK] 候选数字: {num:,} (来自关键词行，优先级2)")
    
    # 按优先级排序，返回最高优先级的数字
    if candidates:
        candidates.sort(key=lambda x: (x[2], -x[0]))  # 先按优先级，再按数字大小（降序）
        best_candidate = candidates[0]
        if verbose:
            print(f"  [OK] 选择最佳候选: {best_candidate[0]:,} ({best_candidate[1]}, 优先级{best_candidate[2]})")
        return best_candidate[0]
    
    return None

def extract_numbers_from_row(row: List) -> List[int]:
    """
    从表格行中提取所有数字
    
    参数:
        row: 表格行（列表）
    
    返回:
        数字列表
    """
    numbers = []
    
    for cell in row:
        if cell is None:
            continue
        
        cell_str = str(cell).strip()
        
        # 移除常见的分隔符和单位
        cell_str = cell_str.replace(',', '').replace('，', '').replace(' ', '')
        cell_str = cell_str.replace('人', '').replace('名', '').replace('位', '')
        cell_str = cell_str.replace('persons', '').replace('employees', '').replace('staff', '')
        
        # 尝试提取数字
        # 匹配整数（可能包含千位分隔符）
        number_patterns = [
            r'\d{1,3}(?:[,，]\d{3})*',  # 带千位分隔符的数字
            r'\d+',  # 普通整数
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, cell_str)
            for match in matches:
                try:
                    # 移除分隔符后转换为整数
                    num_str = match.replace(',', '').replace('，', '')
                    num = int(num_str)
                    numbers.append(num)
                except ValueError:
                    continue
    
    return numbers

def extract_employee_count_from_text(text: str, keywords: List[str]) -> Optional[int]:
    """
    从文本中提取员工数量
    
    参数:
        text: 文本内容
        keywords: 关键词列表
    
    返回:
        员工数量（整数），如果未找到返回None
    """
    # 查找包含关键词的行
    lines = text.split('\n')
    
    for line in lines:
        for keyword in keywords:
            if keyword in line:
                # 尝试从该行提取数字
                numbers = re.findall(r'\d{1,3}(?:[,，]\d{3})*', line)
                for num_str in numbers:
                    try:
                        num = int(num_str.replace(',', '').replace('，', ''))
                        if is_reasonable_employee_count(num):
                            return num
                    except ValueError:
                        continue
    
    return None

def batch_extract_employee_count_from_pdfs(pdf_dir: str, output_csv: str = None) -> Dict[str, Optional[int]]:
    """
    批量从PDF目录中提取员工数量
    
    参数:
        pdf_dir: PDF文件目录
        output_csv: 输出CSV文件路径（可选）
    
    返回:
        字典，格式为 {文件名: 员工数量}
    """
    results = {}
    
    pdf_files = list(Path(pdf_dir).glob("*.pdf"))
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    for pdf_file in pdf_files:
        print(f"\n处理: {pdf_file.name}")
        count = extract_employee_count_from_hk_pdf(str(pdf_file), verbose=True)
        results[pdf_file.name] = count
    
    # 保存到CSV
    if output_csv:
        with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['文件名', '员工数量'])
            for filename, count in results.items():
                writer.writerow([filename, count if count else ''])
        print(f"\n[OK] 结果已保存到: {output_csv}")
    
    return results

def extract_employee_count_by_year_from_pdfs(pdf_dir: str, symbol: str, start_year: int, end_year: int) -> Dict[int, Optional[int]]:
    """
    从PDF目录中按年份提取员工数量
    
    参数:
        pdf_dir: PDF文件目录
        symbol: 股票代码（用于匹配文件名）
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        字典，格式为 {年份: 员工数量}
    """
    results = {}
    
    for year in range(start_year, end_year + 1):
        # 尝试多种可能的文件名格式
        possible_names = [
            f"{symbol}_{year}年年度报告.pdf",
            f"{symbol}_{year}年度报告.pdf",
            f"{symbol}_{year}.pdf",
            f"{year}年年度报告.pdf",
            f"{year}年度报告.pdf",
        ]
        
        found = False
        for filename in possible_names:
            pdf_path = os.path.join(pdf_dir, filename)
            if os.path.exists(pdf_path):
                print(f"\n处理 {year} 年年报: {filename}")
                count = extract_employee_count_from_hk_pdf(pdf_path, verbose=True)
                results[year] = count
                found = True
                break
        
        if not found:
            print(f"[WARNING] 未找到 {year} 年年报PDF文件")
            results[year] = None
    
    return results

if __name__ == "__main__":
    # 示例：从单个PDF提取员工数量
    # pdf_path = "年报PDF/00700_2024年年度报告.pdf"
    # count = extract_employee_count_from_hk_pdf(pdf_path)
    # if count:
    #     print(f"\n员工数量: {count:,} 人")
    
    # 示例：批量提取
    # pdf_dir = "年报PDF"
    # results = batch_extract_employee_count_from_pdfs(pdf_dir, "港股员工数量.csv")
    
    # 示例：按年份提取
    pdf_dir = "年报PDF"
    symbol = "00700"
    results = extract_employee_count_by_year_from_pdfs(pdf_dir, symbol, 2020, 2024)
    
    print("\n" + "=" * 80)
    print("提取结果")
    print("=" * 80)
    for year, count in results.items():
        if count:
            print(f"{year}年: {count:,} 人")
        else:
            print(f"{year}年: 未找到")

