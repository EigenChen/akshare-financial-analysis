"""
测试从财务年报PDF中提取员工数量信息

功能：
1. 打开指定的财务年报PDF文件
2. 查找"员工情况"相关内容
3. 分析表格结构
4. 提取"在职员工的数量合计"对应的数值
"""

import os
import re
import csv
import pdfplumber
from typing import Optional, Dict, List, Tuple
from pathlib import Path

def extract_employee_count_from_pdf(pdf_path: str, verbose: bool = True) -> Optional[int]:
    """
    从PDF年报中提取员工数量
    
    参数:
        pdf_path: PDF文件路径
    
    返回:
        员工数量（整数），如果未找到返回None
    """
    if not os.path.exists(pdf_path):
        print(f"✗ 文件不存在: {pdf_path}")
        return None
    
    if verbose:
        print(f"正在打开PDF文件: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            if verbose:
                print(f"✓ PDF文件打开成功，共 {total_pages} 页")
            
            # 搜索关键词
            keywords = [
                "在职员工的数量合计",
                "在职员工数量合计",
                "员工数量合计",
                "员工总数",
                "在职员工总数",
                "员工人数合计"
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
                has_employee_section = "员工" in text and ("情况" in text or "构成" in text)
                
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
                                    print(f"  ✓ 在表格 {table_idx + 1} 中找到员工数量: {employee_count}")
                                return employee_count
                    
                    # 如果表格提取失败，尝试从文本中提取
                    employee_count = extract_employee_count_from_text(text, keywords)
                    if employee_count is not None:
                        if verbose:
                            print(f"  ✓ 从文本中提取到员工数量: {employee_count}")
                        return employee_count
            
            if employee_count is None and verbose:
                print("\n⚠ 未找到员工数量信息")
                print("提示：可以尝试查看PDF中的'员工情况'或'员工构成'章节")
            
            return employee_count
            
    except Exception as e:
        print(f"✗ 处理PDF文件时出错: {e}")
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
    # 小于10可能是其他数据，大于100万通常不合理
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
    
    # 将表格转换为字符串以便搜索
    table_text = "\n".join(["\t".join([str(cell) if cell else "" for cell in row]) for row in table])
    
    # 存储所有候选数字（用于调试）
    # 格式：(数字, 来源描述, 优先级)
    # 优先级：1=合计关键词行, 2=其他关键词行, 3=合计+员工行
    candidates = []
    
    # 优先查找包含"合计"的关键词行（最高优先级）
    for row_idx, row in enumerate(table):
        row_text = " ".join([str(cell) if cell else "" for cell in row])
        
        # 检查是否包含"合计"相关的关键词（最高优先级）
        for keyword in keywords:
            if keyword in row_text and "合计" in keyword:
                if verbose:
                    print(f"    找到合计关键词 '{keyword}' 在第 {row_idx + 1} 行（高优先级）")
                    print(f"    行内容: {row_text[:150]}...")
                
                # 在这一行查找数字
                numbers = extract_numbers_from_row(row)
                if numbers:
                    if verbose:
                        print(f"    当前行找到数字: {numbers}")
                    # 优先选择该行中最大的合理数字（合计通常是最大的）
                    valid_numbers = [num for num in numbers if isinstance(num, int) and is_reasonable_employee_count(num)]
                    if valid_numbers:
                        # 选择最大的数字（合计行通常包含最大的数字）
                        max_num = max(valid_numbers)
                        candidates.append((max_num, f"合计关键词行{row_idx+1}", 1))
                        if verbose:
                            print(f"    ✓ 候选数字: {max_num} (来自合计关键词行，优先级1)")
                        # 如果找到合计关键词行，优先返回（不再查找其他）
                        # 但继续收集其他候选用于调试
                
                # 如果当前行没找到，检查下一行
                if row_idx + 1 < len(table):
                    next_row = table[row_idx + 1]
                    numbers = extract_numbers_from_row(next_row)
                    if numbers:
                        if verbose:
                            print(f"    下一行找到数字: {numbers}")
                        valid_numbers = [num for num in numbers if isinstance(num, int) and is_reasonable_employee_count(num)]
                        if valid_numbers:
                            max_num = max(valid_numbers)
                            candidates.append((max_num, f"合计关键词行{row_idx+1}的下一行", 1))
                            if verbose:
                                print(f"    ✓ 候选数字: {max_num} (来自下一行，优先级1)")
    
    # 查找其他关键词行（较低优先级）
    for row_idx, row in enumerate(table):
        row_text = " ".join([str(cell) if cell else "" for cell in row])
        
        # 检查是否包含其他关键词（排除已处理的合计关键词）
        for keyword in keywords:
            if keyword in row_text and "合计" not in keyword:
                if verbose:
                    print(f"    找到关键词 '{keyword}' 在第 {row_idx + 1} 行")
                    print(f"    行内容: {row_text[:100]}...")
                
                # 在这一行查找数字
                numbers = extract_numbers_from_row(row)
                if numbers:
                    if verbose:
                        print(f"    当前行找到数字: {numbers}")
                    for num in numbers:
                        if isinstance(num, int) and is_reasonable_employee_count(num):
                            candidates.append((num, f"关键词行{row_idx+1}", 2))
                            if verbose:
                                print(f"    ✓ 候选数字: {num} (来自关键词行，优先级2)")
                
                # 如果当前行没找到，检查下一行
                if row_idx + 1 < len(table):
                    next_row = table[row_idx + 1]
                    numbers = extract_numbers_from_row(next_row)
                    if numbers:
                        if verbose:
                            print(f"    下一行找到数字: {numbers}")
                        for num in numbers:
                            if isinstance(num, int) and is_reasonable_employee_count(num):
                                candidates.append((num, f"关键词行{row_idx+1}的下一行", 2))
                                if verbose:
                                    print(f"    ✓ 候选数字: {num} (来自下一行，优先级2)")
    
    # 如果没找到关键词，尝试查找"合计"行（最低优先级）
    for row_idx, row in enumerate(table):
        row_text = " ".join([str(cell) if cell else "" for cell in row])
        if "合计" in row_text and "员工" in row_text:
            if verbose:
                print(f"    找到'合计+员工'在第 {row_idx + 1} 行")
            numbers = extract_numbers_from_row(row)
            if numbers:
                if verbose:
                    print(f"    合计行找到数字: {numbers}")
                valid_numbers = [num for num in numbers if isinstance(num, int) and is_reasonable_employee_count(num)]
                if valid_numbers:
                    max_num = max(valid_numbers)
                    candidates.append((max_num, f"合计行{row_idx+1}", 3))
                    if verbose:
                        print(f"    ✓ 候选数字: {max_num} (来自合计行，优先级3)")
    
    # 如果有多个候选，按优先级选择
    if candidates:
        if verbose:
            print(f"    所有候选数字: {candidates}")
        
        # 按优先级分组
        priority_1 = [(num, desc) for num, desc, priority in candidates if priority == 1]
        priority_2 = [(num, desc) for num, desc, priority in candidates if priority == 2]
        priority_3 = [(num, desc) for num, desc, priority in candidates if priority == 3]
        
        # 优先选择优先级1的候选（合计关键词行）
        if priority_1:
            valid_nums = [num for num, _ in priority_1 if 10 <= num <= 100000]
            if valid_nums:
                result = max(valid_nums)  # 选择最大的
                if verbose:
                    print(f"    → 选择: {result} (来自合计关键词行，优先级1，最大合理值)")
                return result
        
        # 其次选择优先级2的候选
        if priority_2:
            valid_nums = [num for num, _ in priority_2 if 10 <= num <= 100000]
            if valid_nums:
                result = max(valid_nums)
                if verbose:
                    print(f"    → 选择: {result} (来自关键词行，优先级2，最大合理值)")
                return result
        
        # 最后选择优先级3的候选
        if priority_3:
            valid_nums = [num for num, _ in priority_3 if 10 <= num <= 100000]
            if valid_nums:
                result = max(valid_nums)
                if verbose:
                    print(f"    → 选择: {result} (来自合计行，优先级3，最大合理值)")
                return result
        
        # 如果都没有合理范围内的，返回优先级最高的第一个
        if priority_1:
            result = priority_1[0][0]
            if verbose:
                print(f"    ⚠ 选择: {result} (来自合计关键词行，但可能不在合理范围)")
            return result
        elif priority_2:
            result = priority_2[0][0]
            if verbose:
                print(f"    ⚠ 选择: {result} (来自关键词行，但可能不在合理范围)")
            return result
        elif priority_3:
            result = priority_3[0][0]
            if verbose:
                print(f"    ⚠ 选择: {result} (来自合计行，但可能不在合理范围)")
            return result
    
    return None

def extract_numbers_from_row(row: List) -> List[int]:
    """
    从表格行中提取数字
    
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
        
        # 尝试直接转换为整数
        try:
            num = int(float(cell_str.replace(",", "").replace("，", "")))
            numbers.append(num)
        except (ValueError, AttributeError):
            # 尝试从文本中提取数字
            # 匹配整数（可能包含千位分隔符）
            matches = re.findall(r'[\d,，]+', cell_str)
            for match in matches:
                try:
                    num = int(float(match.replace(",", "").replace("，", "")))
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
    # 查找包含关键词的段落
    lines = text.split("\n")
    
    for i, line in enumerate(lines):
        for keyword in keywords:
            if keyword in line:
                # 在这一行或附近行查找数字
                search_lines = lines[max(0, i-2):min(len(lines), i+3)]
                search_text = " ".join(search_lines)
                
                # 提取所有数字
                numbers = re.findall(r'\d+[,\d]*', search_text)
                for num_str in numbers:
                    try:
                        num = int(float(num_str.replace(",", "").replace("，", "")))
                        # 员工数量通常是较大的整数
                        if num > 10:
                            return num
                    except ValueError:
                        continue
    
    return None

def print_table_preview(table: List[List], max_rows: int = 10):
    """
    打印表格预览
    
    参数:
        table: 表格数据
        max_rows: 最大显示行数
    """
    if not table:
        print("  表格为空")
        return
    
    print(f"  表格预览（前 {min(max_rows, len(table))} 行）:")
    for i, row in enumerate(table[:max_rows]):
        row_str = " | ".join([str(cell)[:20] if cell else "" for cell in row])
        print(f"    行 {i+1}: {row_str}")

def is_annual_report_pdf(filename: str) -> bool:
    """
    判断文件名是否是年度报告PDF
    
    参数:
        filename: 文件名
    
    返回:
        如果是年报PDF返回True，否则返回False
    """
    # 必须是PDF文件
    if not filename.lower().endswith('.pdf'):
        return False
    
    # 必须包含"年度报告"4个字
    if '年度报告' not in filename:
        return False
    
    return True

def extract_year_from_filename(filename: str) -> Optional[int]:
    """
    从文件名中提取年份
    
    参数:
        filename: 文件名
    
    返回:
        年份（整数），如果未找到返回None
    """
    # 查找4位数字年份（2000-2099）
    year_match = re.search(r'20\d{2}', filename)
    if year_match:
        try:
            year = int(year_match.group())
            if 2000 <= year <= 2099:
                return year
        except ValueError:
            pass
    
    return None

def extract_stock_code_from_filename(filename: str) -> Optional[str]:
    """
    从文件名中提取股票代码
    
    参数:
        filename: 文件名
    
    返回:
        股票代码（字符串），如果未找到返回None
    """
    # 常见的股票代码格式：6位数字（A股）
    # 例如：600519、000001、300750等
    
    # 匹配6位数字（可能是股票代码）
    code_matches = re.findall(r'\b\d{6}\b', filename)
    
    if code_matches:
        # 返回第一个匹配的6位数字
        return code_matches[0]
    
    # 如果没有找到6位数字，尝试从文件名开头提取
    # 有些文件名可能是：600519_2024年年度报告.pdf
    basename = os.path.splitext(filename)[0]
    parts = basename.split('_')
    if parts:
        first_part = parts[0]
        if re.match(r'^\d{6}$', first_part):
            return first_part
    
    return None

def save_to_csv(stock_code: str, results: List[Tuple[int, Optional[int]]], output_dir: str = ".") -> str:
    """
    将员工数量数据保存到CSV文件
    
    参数:
        stock_code: 股票代码
        results: 结果列表，每个元素为 (年份, 员工数量)
        output_dir: 输出目录
    
    返回:
        CSV文件路径
    """
    if not stock_code:
        stock_code = "未知"
    
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成CSV文件名
    csv_filename = f"{stock_code}_员工数量.csv"
    csv_path = os.path.join(output_dir, csv_filename)
    
    # 按年份排序
    sorted_results = sorted(results, key=lambda x: x[0] if x[0] else 0)
    
    # 写入CSV文件
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            # 写入表头
            writer.writerow(['年份', '员工数量'])
            # 写入数据
            for year, employee_count in sorted_results:
                count_str = str(employee_count) if employee_count is not None else ""
                writer.writerow([year, count_str])
        
        print(f"  ✓ 数据已保存到: {csv_path}")
        return csv_path
    except Exception as e:
        print(f"  ✗ 保存CSV文件失败: {e}")
        return ""

def process_directory(directory_path: str, verbose: bool = False, stock_code: Optional[str] = None) -> List[Tuple[str, Optional[int], Optional[int]]]:
    """
    批量处理目录中的年报PDF文件
    
    参数:
        directory_path: 目录路径
        verbose: 是否显示详细信息
        stock_code: 股票代码（如果为None，会尝试从文件名中提取）
    
    返回:
        结果列表，每个元素为 (文件路径, 年份, 员工数量)
    """
    if not os.path.exists(directory_path):
        print(f"✗ 目录不存在: {directory_path}")
        return []
    
    if not os.path.isdir(directory_path):
        print(f"✗ 不是有效的目录: {directory_path}")
        return []
    
    print(f"正在扫描目录: {directory_path}")
    print("=" * 80)
    
    results = []
    pdf_files = []
    
    # 遍历目录中的所有文件
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if is_annual_report_pdf(file):
                file_path = os.path.join(root, file)
                pdf_files.append(file_path)
    
    if not pdf_files:
        print("⚠ 未找到年报PDF文件")
        return []
    
    print(f"找到 {len(pdf_files)} 个年报PDF文件\n")
    
    # 如果未提供股票代码，尝试从第一个文件名中提取
    if stock_code is None and pdf_files:
        first_filename = os.path.basename(pdf_files[0])
        stock_code = extract_stock_code_from_filename(first_filename)
        if stock_code:
            print(f"从文件名识别股票代码: {stock_code}\n")
    
    # 用于保存CSV的数据（年份，员工数量）
    csv_data = []
    
    # 处理每个PDF文件
    for idx, pdf_path in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_path)
        year = extract_year_from_filename(filename)
        
        # 如果还未识别股票代码，尝试从当前文件名提取
        if stock_code is None:
            stock_code = extract_stock_code_from_filename(filename)
        
        print(f"[{idx}/{len(pdf_files)}] 处理文件: {filename}")
        if year:
            print(f"  识别年份: {year}")
        
        # 提取员工数量（verbose=False时输出更简洁）
        employee_count = extract_employee_count_from_pdf(pdf_path, verbose=verbose)
        
        if not verbose:
            # 简化输出模式
            if employee_count is not None:
                print(f"  ✓ 员工数量: {employee_count} 人")
            else:
                print(f"  ✗ 未能提取员工数量")
        
        results.append((pdf_path, year, employee_count))
        
        # 收集CSV数据（只保存有年份的数据）
        if year is not None:
            csv_data.append((year, employee_count))
        
        print()  # 空行分隔
    
    # 保存到CSV文件
    if csv_data:
        print("=" * 80)
        print("保存数据到CSV文件...")
        # 如果没有股票代码，使用"未知"作为默认值
        if not stock_code:
            stock_code = "未知"
            print(f"⚠ 未能识别股票代码，使用默认值: {stock_code}")
        save_to_csv(stock_code, csv_data, output_dir=directory_path)
        print()
    elif stock_code:
        print("=" * 80)
        print("⚠ 没有可保存的数据（未提取到员工数量或年份）")
        print()
    
    return results

def print_summary(results: List[Tuple[str, Optional[int], Optional[int]]]):
    """
    打印处理结果汇总
    
    参数:
        results: 处理结果列表
    """
    print("\n" + "=" * 80)
    print("处理结果汇总")
    print("=" * 80)
    
    # 统计
    total_files = len(results)
    success_count = sum(1 for _, _, count in results if count is not None)
    failed_count = total_files - success_count
    
    print(f"\n总计: {total_files} 个文件")
    print(f"成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    
    print("\n详细结果:")
    print("-" * 80)
    print(f"{'文件名':<50} {'年份':<8} {'员工数量':<12}")
    print("-" * 80)
    
    for pdf_path, year, employee_count in results:
        filename = os.path.basename(pdf_path)
        # 截断过长的文件名
        if len(filename) > 48:
            filename = filename[:45] + "..."
        
        year_str = str(year) if year else "未知"
        count_str = f"{employee_count} 人" if employee_count is not None else "未找到"
        
        print(f"{filename:<50} {year_str:<8} {count_str:<12}")
    
    print("-" * 80)
    print("=" * 80)

def verify_specific_year(directory_path: str, year: int, stock_code: Optional[str] = None):
    """
    验证特定年份的员工数量提取结果
    
    参数:
        directory_path: 目录路径
        year: 要验证的年份
        stock_code: 股票代码（可选）
    """
    print("=" * 80)
    print(f"验证 {year} 年员工数量提取结果")
    print("=" * 80)
    
    # 查找对应年份的PDF文件
    pdf_files = []
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            if is_annual_report_pdf(file):
                file_year = extract_year_from_filename(file)
                if file_year == year:
                    file_path = os.path.join(root, file)
                    pdf_files.append(file_path)
    
    if not pdf_files:
        print(f"✗ 未找到 {year} 年的年报PDF文件")
        return
    
    if len(pdf_files) > 1:
        print(f"⚠ 找到 {len(pdf_files)} 个 {year} 年的PDF文件，将验证第一个")
    
    pdf_path = pdf_files[0]
    filename = os.path.basename(pdf_path)
    print(f"\n文件: {filename}")
    print(f"路径: {pdf_path}\n")
    
    # 使用详细模式提取
    print("开始提取（详细模式）...")
    print("-" * 80)
    employee_count = extract_employee_count_from_pdf(pdf_path, verbose=True)
    print("-" * 80)
    
    print("\n" + "=" * 80)
    if employee_count is not None:
        print(f"提取结果: {employee_count} 人")
        print("\n⚠ 请手动验证：")
        print("1. 打开PDF文件，找到'员工情况'或'员工构成'章节")
        print("2. 查找'在职员工的数量合计'或类似表述")
        print("3. 确认提取的数字是否正确")
        print("\n如果提取结果不正确，请手动修正CSV文件中的数据")
    else:
        print("✗ 未能提取员工数量")
        print("\n建议：")
        print("1. 手动打开PDF文件查看")
        print("2. 检查关键词是否匹配")
        print("3. 可能需要调整提取逻辑")
    print("=" * 80)

def main():
    """
    主函数
    
    支持三种模式：
    1. 单文件模式：处理指定的单个PDF文件
    2. 目录模式：批量处理目录中的所有年报PDF文件
    3. 验证模式：详细验证特定年份的数据
    """
    import sys
    
    # 模式选择：可以修改这里来切换模式
    # 模式1：单文件模式
    # 模式2：目录模式（批量处理）
    # 模式3：验证模式（验证特定年份）
    MODE = "directory"  # 可选: "single"、"directory" 或 "verify"
    
    if MODE == "single":
        # ========== 单文件模式 ==========
        # 指定财务年报PDF路径（请修改为实际路径）
        pdf_path = r"G:\code\akshare\贵州茅台：贵州茅台2024年年度报告.pdf"
        
        print("=" * 80)
        print("从财务年报PDF中提取员工数量（单文件模式）")
        print("=" * 80)
        print(f"\nPDF文件路径: {pdf_path}")
        
        # 提取员工数量
        employee_count = extract_employee_count_from_pdf(pdf_path)
        
        print("\n" + "=" * 80)
        if employee_count is not None:
            print(f"✓ 成功提取员工数量: {employee_count} 人")
        else:
            print("✗ 未能提取员工数量")
        print("=" * 80)
    
    elif MODE == "verify":
        # ========== 验证模式（验证特定年份）==========
        # 指定包含年报PDF的目录路径和要验证的年份
        directory_path = r"E:\stock\行业\佳都科技"  # 请修改为实际的目录路径
        verify_year = 2013  # 要验证的年份
        
        # 验证特定年份的数据
        verify_specific_year(directory_path, verify_year, stock_code="600728")
    
    else:
        # ========== 目录模式（批量处理）==========
        # 指定包含年报PDF的目录路径（请修改为实际路径）
        directory_path = r"G:\移动云盘同步文件夹\13600004997\生活\投资\行业\科沃斯"  # 请修改为实际的目录路径
        
        print("=" * 80)
        print("从财务年报PDF中提取员工数量（批量处理模式）")
        print("=" * 80)
        
        # 批量处理目录中的年报PDF
        results = process_directory(directory_path, verbose=False, stock_code="603486")
        
        # 打印汇总结果
        if results:
            print_summary(results)
        else:
            print("\n未找到可处理的年报PDF文件")

if __name__ == "__main__":
    main()

