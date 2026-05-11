# -*- coding: utf-8 -*-
"""
检查CSV文件实际保存情况

模拟完整的主程序流程，检查CSV文件是否正确生成
"""

import os
import csv
import tempfile
from pathlib import Path

def simulate_main_program_csv_save():
    """模拟主程序的CSV保存过程"""
    print("="*80)
    print("模拟主程序CSV保存过程")
    print("="*80)

    # 模拟数据（基于测试结果）
    symbol = "600519"
    company_name = "贵州茅台"

    # 创建临时工作目录来测试
    with tempfile.TemporaryDirectory() as temp_dir:
        company_dir = os.path.join(temp_dir, f"{company_name} {symbol}")
        os.makedirs(company_dir, exist_ok=True)

        print(f"临时工作目录: {company_dir}")

        # 模拟智能提取的结果
        batch_results = {
            '贵州茅台_2014年度报告.pdf': 7036,
            '贵州茅台_2013年度报告.pdf': 5135,
            '贵州茅台_2012年度报告.pdf': 4274,
            '贵州茅台_2011年度报告.pdf': 3942,
        }

        print("\n1. 智能提取结果:")
        for filename, count in batch_results.items():
            print(f"  {filename}: {count:,}人")

        # 转换结果格式以兼容现有代码
        results = []
        for filename, count in batch_results.items():
            # 从文件名提取年份
            year = None
            try:
                import re
                year_match = re.search(r'(\d{4})', filename)
                if year_match:
                    year = int(year_match.group(1))
            except:
                pass

            file_path = os.path.join(company_dir, filename)
            results.append((file_path, year, count))

        print("\n2. 格式转换结果:")
        for file_path, year, count in results:
            filename = os.path.basename(file_path)
            print(f"  {year}年: {filename} -> {count:,}人")

        # 复制验证逻辑
        def validate_employee_count(year, count, all_counts):
            if count is None:
                return None

            prev_year_count = all_counts.get(year - 1)
            next_year_count = all_counts.get(year + 1)

            # 验证逻辑（简化版）
            if prev_year_count is not None and next_year_count is not None:
                avg_count = (prev_year_count + next_year_count) / 2
                if avg_count > 0:
                    ratio = count / avg_count
                    if ratio > 10 or ratio < 0.1:
                        return None
            elif prev_year_count is not None:
                if prev_year_count > 0:
                    ratio = count / prev_year_count
                    if ratio > 10 or ratio < 0.1:
                        return None
            elif next_year_count is not None:
                if next_year_count > 0:
                    ratio = count / next_year_count
                    if ratio > 10 or ratio < 0.1:
                        return None

            return count

        def process_employee_counts(results):
            all_counts = {}
            for file_path, year, count in results:
                if year is not None:
                    all_counts[year] = count

            validated_counts = {}
            for year in sorted(all_counts.keys()):
                count = all_counts[year]
                validated_count = validate_employee_count(year, count, all_counts)
                validated_counts[year] = validated_count

            return validated_counts

        # 处理结果，添加数量级检查
        employee_counts = process_employee_counts(results)

        print("\n3. 验证后的数据:")
        for year, count in sorted(employee_counts.items()):
            status = f"{count:,}人" if count is not None else "被过滤"
            print(f"  {year}年: {status}")

        # 保存验证后的数据到CSV
        csv_path = os.path.join(company_dir, f"{symbol}_员工数量.csv")
        print(f"\n4. 保存CSV文件: {csv_path}")

        try:
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['年份', '员工数量'])
                for year in sorted(employee_counts.keys()):
                    count = employee_counts[year]
                    # 如果数量为None，保存为"-"
                    csv_value = count if count is not None else '-'
                    writer.writerow([year, csv_value])
                    print(f"  写入: {year}, {csv_value}")

            print(f"\n5. 验证CSV文件是否存在:")
            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                print(f"  [OK] CSV文件已创建: {csv_path}")
                print(f"  [OK] 文件大小: {file_size} bytes")

                # 读取并显示CSV内容
                print(f"\n6. CSV文件内容:")
                with open(csv_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    print(content)

                # 用pandas读取测试
                try:
                    import pandas as pd
                    df = pd.read_csv(csv_path, encoding='utf-8-sig')
                    print(f"\n7. Pandas读取测试:")
                    print(f"  行数: {len(df)}")
                    print(f"  列数: {len(df.columns)}")
                    print("  内容:")
                    for index, row in df.iterrows():
                        year = row['年份']
                        count = row['员工数量']
                        print(f"    {year}年: {count}")

                except Exception as e:
                    print(f"\n7. Pandas读取失败: {e}")

            else:
                print(f"  [ERROR] CSV文件未创建!")

        except Exception as e:
            print(f"  [ERROR] CSV保存失败: {e}")
            import traceback
            traceback.print_exc()

def check_actual_csv_files():
    """检查实际的CSV文件"""
    print("\n" + "="*80)
    print("检查实际的CSV文件")
    print("="*80)

    # 可能的CSV文件位置
    possible_paths = [
        r"F:\code\akshare\年报PDF",
        r"F:\code\akshare",
        # 可以添加其他可能的路径
    ]

    csv_files_found = []

    for search_dir in possible_paths:
        if os.path.exists(search_dir):
            search_path = Path(search_dir)
            csv_files = list(search_path.glob("*员工数量*.csv"))
            if csv_files:
                csv_files_found.extend(csv_files)
                print(f"在 {search_dir} 找到:")
                for csv_file in csv_files:
                    print(f"  {csv_file}")

    if csv_files_found:
        print(f"\n检查最新的CSV文件:")
        latest_csv = max(csv_files_found, key=lambda f: f.stat().st_mtime)
        print(f"最新文件: {latest_csv}")
        print(f"修改时间: {latest_csv.stat().st_mtime}")

        try:
            with open(latest_csv, 'r', encoding='utf-8-sig') as f:
                content = f.read()
                print(f"\n文件内容:")
                print(content)

            # 检查是否为空或只有表头
            lines = content.strip().split('\n')
            if len(lines) <= 1:
                print("[PROBLEM] CSV文件只有表头，没有数据行!")
            else:
                data_lines = len(lines) - 1
                print(f"[OK] CSV文件包含 {data_lines} 行数据")

        except Exception as e:
            print(f"读取CSV文件失败: {e}")
    else:
        print("未找到任何员工数量CSV文件")

if __name__ == "__main__":
    simulate_main_program_csv_save()
    check_actual_csv_files()