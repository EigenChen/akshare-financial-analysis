# -*- coding: utf-8 -*-
"""
港股员工数量提取器 - 基于多态的设计

功能：
1. 定义抽象基类，规范提取接口
2. 为不同公司实现特定的提取逻辑
3. 使用工厂模式根据股票代码返回对应的提取器

设计思路：
- 每个公司可能有不同的年报格式，需要定制化提取逻辑
- 使用多态设计，便于扩展新的公司提取器
- 如果某公司未实现提取器，返回None并提示
"""

import os
import re
import csv
import pdfplumber
from abc import ABC, abstractmethod
from typing import Optional, Dict, Union
from pathlib import Path


class HKEmployeeExtractor(ABC):
    """
    港股员工数量提取器抽象基类
    
    所有公司的提取器都应该继承这个基类并实现extract方法
    """
    
    def __init__(self, symbol: str, company_name: str):
        """
        初始化提取器
        
        参数:
            symbol: 股票代码（如 "00700"）
            company_name: 公司名称（如 "腾讯控股"）
        """
        self.symbol = symbol
        self.company_name = company_name
    
    @abstractmethod
    def extract(self, pdf_path: str, verbose: bool = True) -> Optional[int]:
        """
        从PDF中提取员工数量（抽象方法，子类必须实现）
        
        参数:
            pdf_path: PDF文件路径
            verbose: 是否显示详细调试信息
        
        返回:
            员工数量（整数），如果未找到返回None
        """
        pass
    
    def extract_total_salary(self, pdf_path: str, verbose: bool = True) -> Optional[float]:
        """
        从PDF中提取总薪酬（可选方法，子类可以重写）
        
        参数:
            pdf_path: PDF文件路径
            verbose: 是否显示详细调试信息
        
        返回:
            总薪酬（亿元，浮点数），如果未找到返回None
        """
        # 默认实现返回None，子类可以重写此方法
        return None
    
    def extract_by_year(self, pdf_dir: str, start_year: int, end_year: int, verbose: bool = True) -> Dict[int, Optional[int]]:
        """
        按年份提取员工数量（通用方法，子类可以重写）
        
        参数:
            pdf_dir: PDF文件目录
            start_year: 起始年份
            end_year: 结束年份
            verbose: 是否显示详细调试信息
        
        返回:
            字典，格式为 {年份: 员工数量}
        """
        results = {}
        
        for year in range(start_year, end_year + 1):
            # 尝试多种可能的文件名格式
            possible_names = [
                f"{self.symbol}_{year}年年度报告.pdf",
                f"{self.symbol}_{year}年度报告.pdf",
                f"{self.symbol}_{year}.pdf",
                f"{year}年年度报告.pdf",
                f"{year}年度报告.pdf",
            ]
            
            found = False
            for filename in possible_names:
                pdf_path = os.path.join(pdf_dir, filename)
                if os.path.exists(pdf_path):
                    if verbose:
                        print(f"\n处理 {year} 年年报: {filename}")
                    count = self.extract(pdf_path, verbose=verbose)
                    results[year] = count
                    found = True
                    break
            
            if not found:
                if verbose:
                    print(f"[WARNING] 未找到 {year} 年年报PDF文件")
                results[year] = None
        
        return results
    
    def extract_employee_and_salary_by_year(self, pdf_dir: str, start_year: int, end_year: int, verbose: bool = True) -> Dict[int, Dict[str, Union[int, float, None]]]:
        """
        按年份提取员工数量和总薪酬（通用方法）
        
        参数:
            pdf_dir: PDF文件目录
            start_year: 起始年份
            end_year: 结束年份
            verbose: 是否显示详细调试信息
        
        返回:
            字典，格式为 {年份: {'员工数量': int, '总薪酬': float}}
        """
        results = {}
        
        for year in range(start_year, end_year + 1):
            # 尝试多种可能的文件名格式
            possible_names = [
                f"{self.symbol}_{year}年年度报告.pdf",
                f"{self.symbol}_{year}年度报告.pdf",
                f"{self.symbol}_{year}.pdf",
                f"{year}年年度报告.pdf",
                f"{year}年度报告.pdf",
            ]
            
            found = False
            for filename in possible_names:
                pdf_path = os.path.join(pdf_dir, filename)
                if os.path.exists(pdf_path):
                    if verbose:
                        print(f"\n{'='*60}")
                        print(f"处理 {year} 年年报: {filename}")
                        print(f"{'='*60}")
                    count = self.extract(pdf_path, verbose=verbose)
                    if verbose:
                        print(f"\n[INFO] {year} 年员工数量提取完成: {count if count else '未找到'}")
                    total_salary = self.extract_total_salary(pdf_path, verbose=verbose)
                    if verbose:
                        print(f"[INFO] {year} 年总薪酬提取完成: {total_salary:.3f} 亿元" if total_salary else f"[INFO] {year} 年总薪酬提取完成: 未找到")
                    results[year] = {
                        '员工数量': count,
                        '总薪酬': total_salary
                    }
                    if verbose:
                        print(f"[OK] {year} 年数据提取完成")
                    found = True
                    break
            
            if not found:
                if verbose:
                    print(f"[WARNING] 未找到 {year} 年年报PDF文件")
                results[year] = {'员工数量': None, '总薪酬': None}
        
        return results
    
    def save_to_csv(self, results: Dict[int, Optional[int]], output_dir: str = ".") -> str:
        """
        将提取结果保存为CSV文件（兼容旧接口，只保存员工数量）
        
        参数:
            results: 提取结果字典，格式为 {年份: 员工数量}
            output_dir: 输出目录
        
        返回:
            CSV文件路径
        """
        # 转换为新格式
        new_results = {}
        for year, count in results.items():
            new_results[year] = {'员工数量': count, '总薪酬': None}
        return self.save_to_csv_with_salary(new_results, output_dir)
    
    def save_to_csv_with_salary(self, results: Dict[int, Dict[str, Union[int, float, None]]], output_dir: str = ".") -> str:
        """
        将提取结果（包含员工数量和总薪酬）保存为CSV文件
        
        参数:
            results: 提取结果字典，格式为 {年份: {'员工数量': int, '总薪酬': float}}
                    注意：总薪酬的单位是"亿元"
            output_dir: 输出目录
        
        返回:
            CSV文件路径
        
        注意：
            - CSV中保存的总薪酬单位是"亿元"
            - 在计算人均薪酬时，需要转换为"万元"：人均薪酬（万元）= 总薪酬（亿元）/ 人数 × 10000
        """
        # 创建输出目录
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 生成CSV文件名
        csv_filename = f"{self.symbol}_员工数量.csv"
        csv_path = os.path.join(output_dir, csv_filename)
        
        # 按年份排序
        sorted_years = sorted([y for y in results.keys() if results[y].get('员工数量') is not None])
        
        # 检查是否有总薪酬数据
        has_salary = any(results[y].get('总薪酬') is not None for y in sorted_years)
        
        # 写入CSV文件
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                # 写入表头
                if has_salary:
                    writer.writerow(['年份', '员工数量', '总薪酬'])
                else:
                    writer.writerow(['年份', '员工数量'])
                
                # 写入数据
                for year in sorted_years:
                    count = results[year].get('员工数量')
                    salary = results[year].get('总薪酬')
                    if has_salary:
                        writer.writerow([year, count if count is not None else '', 
                                        f"{salary:.3f}" if salary is not None else ''])
                    else:
                        writer.writerow([year, count if count is not None else ''])
            
            print(f"[OK] 员工数量CSV已保存: {csv_path}")
            if has_salary:
                print(f"  [INFO] CSV文件包含总薪酬数据（单位：亿元）")
            return csv_path
        except Exception as e:
            print(f"[FAIL] 保存CSV文件失败: {e}")
            return ""


class TencentEmployeeExtractor(HKEmployeeExtractor):
    """
    腾讯控股（00700）员工数量提取器
    
    腾讯年报格式示例：
    "於二零零七年十二月三十一日，本集團有4,344名僱員（二零零六年︰3,017名）"
    
    提取逻辑：
    1. 查找包含"僱員"或"雇员"的文本
    2. 匹配"本集團有X名僱員"或"本集团有X名雇员"的模式
    3. 提取当期（报告期）的员工数量
    """
    
    def __init__(self):
        super().__init__("00700", "腾讯控股")
    
    def extract(self, pdf_path: str, verbose: bool = True) -> Optional[int]:
        """
        从腾讯年报PDF中提取员工数量
        
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
                
                # 腾讯年报中的关键词模式
                # 格式示例: "於二零零七年十二月三十一日，本集團有4,344名僱員（二零零六年︰3,017名）"
                # 需要提取的是"本集團有4,344名僱員"中的数字，这是当期（报告期）的员工数量
                # 括号中的是上一年的数据，应该忽略
                
                patterns = [
                    # 优先匹配：完整格式 "於...十二月三十一日，本集團有X,XXX名僱員"
                    # 这个模式确保匹配的是当期数据，而不是括号中的上一年数据
                    r'於[^，,（(]*[十十]二[月月][^，,（(]*[三三][十十][一一]日[^，,（(]*，?\s*本[集集]團有\s*([\d,，]+)\s*名[僱雇]員',
                    # 次优匹配：直接匹配"本集團有X,XXX名僱員"，但确保后面不是括号（避免匹配到括号中的上一年数据）
                    r'本[集集]團有\s*([\d,，]+)\s*名[僱雇]員(?!\s*[（(])',
                    # 备用匹配：匹配"有X,XXX名僱員"（简化版）
                    r'有\s*([\d,，]+)\s*名[僱雇]員',
                ]
                
                employee_count = None
                
                # 遍历每一页
                for page_num, page in enumerate(pdf.pages, 1):
                    # 提取文本
                    text = page.extract_text()
                    
                    if not text:
                        continue
                    
                    # 检查是否包含"僱員"或"雇员"关键词
                    if "僱員" not in text and "雇员" not in text:
                        continue
                    
                    if verbose:
                        print(f"\n在第 {page_num} 页找到员工相关信息")
                    
                    # 尝试匹配各种模式
                    for pattern_idx, pattern in enumerate(patterns):
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            num_str = match.group(1)
                            # 移除千位分隔符
                            num_str = num_str.replace(',', '').replace('，', '').strip()
                            try:
                                count = int(num_str)
                                # 验证数字是否合理（10到1000000之间）
                                if 10 <= count <= 1000000:
                                    employee_count = count
                                    if verbose:
                                        print(f"  [OK] 使用模式 {pattern_idx + 1} 提取到员工数量: {employee_count:,}")
                                    return employee_count
                            except ValueError:
                                continue
                
                if employee_count is None and verbose:
                    print("\n[WARNING] 未找到员工数量信息")
                    print("提示：腾讯年报通常在'雇员及酬金政策'章节中")
                
                return employee_count
                
        except Exception as e:
            if verbose:
                print(f"[FAIL] 处理PDF文件时出错: {e}")
                import traceback
                traceback.print_exc()
            return None
    
    def extract_total_salary(self, pdf_path: str, verbose: bool = True) -> Optional[float]:
        """
        从腾讯年报PDF中提取总薪酬
        
        腾讯年报格式示例：
        "本集團截至二零零七年十二月三十一日止年度的總酬金為人民幣7.315億元"
        
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
                
                # 腾讯年报中的总薪酬模式
                # 格式示例: 
                # - 2007年: "本集團截至二零零七年十二月三十一日止年度的總酬金為人民幣7.315億元"
                # - 2008年: "本集團截至二零零八年十二月三十一日止年度的總酬金成本（包括已資本化的酬金成本）為人民幣13.656億元"
                # - 2024年: "本集團截至二零二四年十二月三十一日止年度的總酬金成本為人民幣 1,128 億元"
                # 注意：
                # 1. 可能是"總酬金"或"總酬金成本"
                # 2. "總酬金成本"和"為"之间可能有括号说明，如"（包括已資本化的酬金成本）"
                # 3. 需要匹配第一个数字（当期），而不是括号中的上一年数据
                
                patterns = [
                    # 优先匹配：完整格式，处理括号说明
                    # "本集團截至...止年度的總酬金成本（...）為人民幣X,XXX億元"
                    # 使用非贪婪匹配，确保匹配到第一个"為"
                    r'本[集集]團截至[^為]*止年度的總酬金(?:成本)?(?:[^為]*)?為[人民幣]*\s*([\d,，.．]+)\s*億元',
                    # 次优匹配：简化格式 "總酬金成本為人民幣X,XXX億元"（处理可能的括号）
                    r'總酬金(?:成本)?(?:[^為]*)?為[人民幣]*\s*([\d,，.．]+)\s*億元',
                    # 备用匹配：万元单位（需要转换为亿元）
                    r'總酬金(?:成本)?(?:[^為]*)?為[人民幣]*\s*([\d,，.．]+)\s*萬元',
                ]
                
                total_salary = None
                unit_multiplier = 1.0  # 单位倍数：亿元=1.0, 万元=0.0001
                
                # 遍历每一页
                for page_num, page in enumerate(pdf.pages, 1):
                    # 提取文本
                    text = page.extract_text()
                    
                    if not text:
                        continue
                    
                    # 检查是否包含"總酬金"或"总酬金"关键词
                    if "總酬金" not in text and "总酬金" not in text:
                        continue
                    
                    if verbose:
                        print(f"\n在第 {page_num} 页找到总薪酬相关信息")
                    
                    # 尝试匹配各种模式
                    candidates = []  # 存储所有候选结果
                    
                    for pattern_idx, pattern in enumerate(patterns):
                        matches = re.finditer(pattern, text, re.IGNORECASE)
                        for match in matches:
                            num_str = match.group(1)
                            # 移除千位分隔符
                            num_str = num_str.replace(',', '').replace('，', '').strip()
                            
                            # 判断单位
                            if '萬元' in match.group(0) or '万元' in match.group(0):
                                unit_multiplier = 0.0001  # 万元转亿元
                            else:
                                unit_multiplier = 1.0  # 已经是亿元
                            
                            try:
                                salary = float(num_str) * unit_multiplier
                                # 验证数字是否合理（0.1到10000亿元之间，即1000万到10万亿）
                                if 0.1 <= salary <= 10000:
                                    # 获取匹配的完整文本和位置信息
                                    match_text = match.group(0)
                                    match_start = match.start()
                                    
                                    # 检查是否在括号中（上一年数据通常在括号中）
                                    # 查找匹配位置之前的文本，看是否有未闭合的括号
                                    text_before = text[:match_start]
                                    open_parens = text_before.count('（') - text_before.count('）')
                                    is_in_parentheses = open_parens > 0
                                    
                                    # 记录候选结果
                                    candidates.append({
                                        'salary': salary,
                                        'pattern_idx': pattern_idx,
                                        'match_text': match_text[:150],  # 只取前150个字符
                                        'position': match_start,
                                        'in_parentheses': is_in_parentheses
                                    })
                                    if verbose:
                                        status = "括号中" if is_in_parentheses else "主文本"
                                        print(f"  [候选] 模式 {pattern_idx + 1}: {salary:.3f} 亿元 ({status}, 位置: {match_start})")
                                        print(f"        匹配文本: {match_text[:100]}...")
                            except ValueError:
                                continue
                    
                    # 选择最佳结果
                    if candidates:
                        # 优先选择不在括号中的结果（当期数据）
                        non_parentheses = [c for c in candidates if not c['in_parentheses']]
                        if non_parentheses:
                            # 如果有多条不在括号中的，选择最大的
                            non_parentheses.sort(key=lambda x: x['salary'], reverse=True)
                            best_match = non_parentheses[0]
                        else:
                            # 如果都在括号中，选择最大的（可能是当期数据在括号中，但金额更大）
                            candidates.sort(key=lambda x: x['salary'], reverse=True)
                            best_match = candidates[0]
                        
                        total_salary = best_match['salary']
                        if verbose:
                            print(f"  [OK] 使用模式 {best_match['pattern_idx'] + 1} 提取到总薪酬: {total_salary:.3f} 亿元")
                            if len(candidates) > 1:
                                print(f"  [INFO] 共找到 {len(candidates)} 个候选结果，选择了{'不在括号中的' if not best_match['in_parentheses'] else '最大的'}结果")
                        return total_salary
                
                if total_salary is None and verbose:
                    print("\n[WARNING] 未找到总薪酬信息")
                    print("提示：腾讯年报通常在'雇员及酬金政策'章节中")
                
                return total_salary
                
        except Exception as e:
            if verbose:
                print(f"[FAIL] 处理PDF文件时出错: {e}")
                import traceback
                traceback.print_exc()
            return None


def get_employee_extractor(symbol: str) -> Optional[HKEmployeeExtractor]:
    """
    工厂函数：根据股票代码返回对应的员工数量提取器
    
    参数:
        symbol: 股票代码（如 "00700"）
    
    返回:
        对应的提取器实例，如果未实现返回None
    """
    # 标准化股票代码（去除前导零，统一格式）
    symbol_clean = symbol.strip().zfill(5)
    
    # 根据股票代码返回对应的提取器
    extractors = {
        "00700": TencentEmployeeExtractor,  # 腾讯控股
        "09988": AlibabaEmployeeExtractor,  # 阿里巴巴（待实现）
        # 可以在这里添加更多公司的提取器
        # "00001": AnotherCompanyExtractor,
    }
    
    if symbol_clean in extractors:
        return extractors[symbol_clean]()
    else:
        return None


class AlibabaEmployeeExtractor(HKEmployeeExtractor):
    """
    阿里巴巴（09988）员工数量和总薪酬提取器
    
    注意：这是一个基础实现，需要根据实际年报格式进行调整
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
                
                # 阿里巴巴年报关键词（需要根据实际格式调整）
                keywords = [
                    "员工", "雇员", "employee", "staff",
                    "人数", "数量", "number", "count"
                ]
                
                employee_count = None
                
                # 遍历每一页
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # 检查是否包含员工相关关键词
                    if not any(kw in text for kw in keywords):
                        continue
                    
                    if verbose:
                        print(f"\n在第 {page_num} 页找到员工相关信息")
                    
                    # 尝试提取表格
                    tables = page.extract_tables()
                    if tables:
                        if verbose:
                            print(f"  找到 {len(tables)} 个表格")
                        # 这里可以添加表格分析逻辑
                    
                    # 尝试从文本中提取
                    # 匹配模式：数字 + 人/名/位
                    patterns = [
                        r'(\d{1,3}(?:[,，]\d{3})*)\s*[人名位]',
                        r'员工[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*)\s*[人名位]',
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            num_str = match.group(1)
                            num_str = num_str.replace(',', '').replace('，', '').strip()
                            try:
                                count = int(num_str)
                                if 10 <= count <= 1000000:
                                    employee_count = count
                                    if verbose:
                                        print(f"  [OK] 提取到员工数量: {employee_count:,}")
                                    return employee_count
                            except ValueError:
                                continue
                
                if employee_count is None and verbose:
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
                if verbose:
                    print(f"正在提取总薪酬信息...")
                
                # 查找薪酬相关关键词
                salary_keywords = [
                    "薪酬", "酬金", "salary", "compensation", "remuneration",
                    "工资", "wage", "pay"
                ]
                
                total_salary = None
                candidates = []
                
                # 遍历每一页
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # 检查是否包含薪酬相关关键词
                    if not any(kw in text for kw in salary_keywords):
                        continue
                    
                    if verbose:
                        print(f"\n在第 {page_num} 页找到薪酬相关信息")
                    
                    # 尝试多种模式匹配
                    patterns = [
                        r'薪酬[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*亿元',
                        r'酬金[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*亿元',
                        r'薪酬[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*万元',
                    ]
                    
                    for pattern in patterns:
                        matches = re.finditer(pattern, text)
                        for match in matches:
                            num_str = match.group(1)
                            num_str = num_str.replace(',', '').replace('，', '').strip()
                            
                            # 判断单位
                            unit_multiplier = 0.0001 if '万元' in match.group(0) else 1.0
                            
                            try:
                                salary = float(num_str) * unit_multiplier
                                if 0.1 <= salary <= 10000:
                                    candidates.append(salary)
                                    if verbose:
                                        print(f"  [候选] 找到薪酬: {salary:.3f} 亿元")
                            except ValueError:
                                continue
                    
                    if candidates:
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


def extract_employee_count_by_company(pdf_dir: str, symbol: str, start_year: int, end_year: int, verbose: bool = True) -> Dict[int, Optional[int]]:
    """
    根据公司类型提取员工数量（主入口函数，兼容旧接口）
    
    参数:
        pdf_dir: PDF文件目录
        symbol: 股票代码
        start_year: 起始年份
        end_year: 结束年份
        verbose: 是否显示详细调试信息
    
    返回:
        字典，格式为 {年份: 员工数量}
    """
    # 获取对应的提取器
    extractor = get_employee_extractor(symbol)
    
    if extractor is None:
        if verbose:
            print(f"[WARNING] 股票代码 {symbol} 的员工数量提取功能尚未实现")
            print(f"提示：请联系开发者添加 {symbol} 的提取逻辑")
        return {}
    
    if verbose:
        print(f"[INFO] 使用 {extractor.company_name} ({extractor.symbol}) 专用提取器")
    
    # 使用提取器提取数据（包含总薪酬）
    full_results = extractor.extract_employee_and_salary_by_year(pdf_dir, start_year, end_year, verbose=verbose)
    
    # 转换为旧格式（只返回员工数量）
    results = {year: data.get('员工数量') for year, data in full_results.items()}
    
    return results

def extract_employee_and_salary_by_company(pdf_dir: str, symbol: str, start_year: int, end_year: int, verbose: bool = True) -> Dict[int, Dict[str, Union[int, float, None]]]:
    """
    根据公司类型提取员工数量和总薪酬（新接口）
    
    参数:
        pdf_dir: PDF文件目录
        symbol: 股票代码
        start_year: 起始年份
        end_year: 结束年份
        verbose: 是否显示详细调试信息
    
    返回:
        字典，格式为 {年份: {'员工数量': int, '总薪酬': float}}
    """
    # 获取对应的提取器
    extractor = get_employee_extractor(symbol)
    
    if extractor is None:
        if verbose:
            print(f"[WARNING] 股票代码 {symbol} 的员工数量提取功能尚未实现")
            print(f"提示：请联系开发者添加 {symbol} 的提取逻辑")
        return {}
    
    if verbose:
        print(f"[INFO] 使用 {extractor.company_name} ({extractor.symbol}) 专用提取器")
    
    # 使用提取器提取数据（包含总薪酬）
    results = extractor.extract_employee_and_salary_by_year(pdf_dir, start_year, end_year, verbose=verbose)
    
    return results


def extract_and_save_to_csv(pdf_dir: str, symbol: str, start_year: int, end_year: int, output_dir: str = ".", verbose: bool = True) -> str:
    """
    提取员工数量和总薪酬并保存为CSV文件（便捷函数）
    
    参数:
        pdf_dir: PDF文件目录
        symbol: 股票代码
        start_year: 起始年份
        end_year: 结束年份
        output_dir: 输出目录
        verbose: 是否显示详细调试信息
    
    返回:
        CSV文件路径，如果失败返回空字符串
    """
    # 获取对应的提取器
    extractor = get_employee_extractor(symbol)
    
    if extractor is None:
        if verbose:
            print(f"[WARNING] 股票代码 {symbol} 的员工数量提取功能尚未实现")
        return ""
    
    # 提取数据（包含总薪酬）
    results = extractor.extract_employee_and_salary_by_year(pdf_dir, start_year, end_year, verbose=verbose)
    
    # 保存为CSV（包含总薪酬）
    csv_path = extractor.save_to_csv_with_salary(results, output_dir)
    
    return csv_path


if __name__ == "__main__":
    # 测试腾讯控股的员工数量提取
    pdf_dir = "年报PDF"
    symbol = "00700"
    start_year = 2020
    end_year = 2024
    
    print("=" * 80)
    print(f"测试 {symbol} 员工数量提取")
    print("=" * 80)
    
    results = extract_employee_count_by_company(pdf_dir, symbol, start_year, end_year, verbose=True)
    
    print("\n" + "=" * 80)
    print("提取结果")
    print("=" * 80)
    for year, count in sorted(results.items()):
        if count:
            print(f"{year}年: {count:,} 人")
        else:
            print(f"{year}年: 未找到")
    
    # 保存为CSV
    csv_path = extract_and_save_to_csv(pdf_dir, symbol, start_year, end_year, output_dir=".", verbose=True)
    if csv_path:
        print(f"\n[OK] CSV文件已保存: {csv_path}")

