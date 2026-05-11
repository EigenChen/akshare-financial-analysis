# -*- coding: utf-8 -*-
"""
分析阿里巴巴年报格式，找出员工数量和总薪酬的表述方式
"""

import pdfplumber
import re
import os

def analyze_alibaba_pdf(pdf_path):
    """分析阿里巴巴年报PDF，找出员工和薪酬相关信息"""
    print(f"正在分析: {pdf_path}")
    print("=" * 80)
    
    if not os.path.exists(pdf_path):
        print(f"[ERROR] 文件不存在: {pdf_path}")
        return
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"PDF文件打开成功，共 {len(pdf.pages)} 页\n")
            
            # 搜索员工相关信息
            print("=" * 80)
            print("搜索员工相关信息...")
            print("=" * 80)
            
            employee_keywords = ["员工", "雇员", "employee", "staff", "人数", "数量"]
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                # 检查是否包含员工相关关键词
                if any(kw in text for kw in employee_keywords):
                    print(f"\n第 {page_num} 页找到员工相关信息:")
                    print("-" * 80)
                    
                    # 提取包含关键词的行
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if any(kw in line for kw in employee_keywords):
                            # 显示上下文（前后各3行）
                            start = max(0, i - 3)
                            end = min(len(lines), i + 4)
                            context = '\n'.join(lines[start:end])
                            print(context)
                            print("-" * 80)
                    
                    # 尝试提取数字
                    numbers = re.findall(r'\d{1,3}(?:[,，]\d{3})*', text)
                    if numbers:
                        print(f"找到的数字: {numbers[:10]}")  # 只显示前10个
            
            # 搜索薪酬相关信息
            print("\n" + "=" * 80)
            print("搜索薪酬相关信息...")
            print("=" * 80)
            
            salary_keywords = ["薪酬", "酬金", "salary", "compensation", "工资", "wage"]
            
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if not text:
                    continue
                
                # 检查是否包含薪酬相关关键词
                if any(kw in text for kw in salary_keywords):
                    print(f"\n第 {page_num} 页找到薪酬相关信息:")
                    print("-" * 80)
                    
                    # 提取包含关键词的行
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        if any(kw in line for kw in salary_keywords):
                            # 显示上下文（前后各3行）
                            start = max(0, i - 3)
                            end = min(len(lines), i + 4)
                            context = '\n'.join(lines[start:end])
                            print(context)
                            print("-" * 80)
                    
                    # 尝试提取数字（带单位）
                    patterns = [
                        r'(\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)\s*[亿万]元',
                        r'[亿万]元[^，,。.]*?(\d{1,3}(?:[,，]\d{3})*(?:\.\d+)?)',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            print(f"找到的数字（带单位）: {matches[:10]}")
    
    except Exception as e:
        print(f"[ERROR] 处理PDF文件时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 分析2024年年报
    pdf_path = r"F:/移动云盘同步文件夹/13600004997/生活/投资/旗下公司/阿里巴巴 09988/09988_2024年年度报告.pdf"
    analyze_alibaba_pdf(pdf_path)

