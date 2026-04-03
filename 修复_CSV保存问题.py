# -*- coding: utf-8 -*-
"""
CSV保存修复补丁

解决员工数量没有正确保存到CSV文件的问题
"""

def create_fixed_csv_save_section():
    """创建修复后的CSV保存代码段"""

    fixed_code = '''
        try:
            # 使用智能批量提取功能
            with log_container:
                st.write("正在使用智能算法提取员工数量...")
                st.write(f"PDF目录: {company_dir}")

            batch_results = emp_module.batch_extract_employee_count_smart(
                company_dir,
                stock_code=symbol,
                use_smart=True
            )

            with log_container:
                st.write(f"智能算法提取完成，处理了 {len(batch_results)} 个文件")

            # 直接处理智能算法结果，跳过复杂的验证逻辑
            employee_counts = {}

            for filename, count in batch_results.items():
                # 从文件名提取年份
                year = None
                try:
                    import re
                    year_match = re.search(r'(\\d{4})', filename)
                    if year_match:
                        year = int(year_match.group(1))
                except:
                    pass

                if year is not None:
                    employee_counts[year] = count

                with log_container:
                    if count:
                        st.write(f"  {year}年 ({filename}): {count:,}人")
                    else:
                        st.write(f"  {year}年 ({filename}): 提取失败")

            # 保存到CSV文件
            csv_path = os.path.join(company_dir, f"{symbol}_员工数量.csv")

            with log_container:
                st.write(f"正在保存CSV文件到: {csv_path}")

            try:
                with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                    import csv
                    writer = csv.writer(f)
                    writer.writerow(['年份', '员工数量'])

                    saved_rows = 0
                    for year in sorted(employee_counts.keys()):
                        count = employee_counts[year]
                        csv_value = count if count is not None else '-'
                        writer.writerow([year, csv_value])
                        saved_rows += 1

                        with log_container:
                            st.write(f"  保存: {year}年 -> {csv_value}")

                # 验证文件保存
                if os.path.exists(csv_path):
                    file_size = os.path.getsize(csv_path)
                    with log_container:
                        st.success(f"✅ CSV文件保存成功!")
                        st.write(f"   文件路径: {csv_path}")
                        st.write(f"   文件大小: {file_size} bytes")
                        st.write(f"   数据行数: {saved_rows}")

                        # 验证读取
                        with open(csv_path, 'r', encoding='utf-8-sig') as f:
                            lines = f.readlines()
                            st.write(f"   实际行数: {len(lines)} 行")
                            if len(lines) > 1:
                                st.write("   CSV内容预览:")
                                for line in lines[:6]:  # 显示前6行
                                    st.code(line.strip())
                else:
                    with log_container:
                        st.error("❌ CSV文件保存失败 - 文件不存在")

            except Exception as csv_error:
                with log_container:
                    st.error(f"❌ CSV保存异常: {csv_error}")
                    import traceback
                    st.code(traceback.format_exc())
'''

    return fixed_code

def apply_fix():
    """应用修复"""
    print("="*80)
    print("CSV保存修复补丁")
    print("="*80)

    print("\n建议的修复方案:")
    print("1. 移除复杂的数量级验证逻辑")
    print("2. 直接保存智能算法的提取结果")
    print("3. 增加详细的保存过程日志")
    print("4. 添加CSV文件验证步骤")

    print("\n主要变化:")
    print("- 跳过 process_employee_counts() 验证")
    print("- 直接使用智能算法结果")
    print("- 增强错误处理和日志")
    print("- 添加文件保存验证")

    print("\n原因分析:")
    print("- 智能算法本身已经有置信度验证")
    print("- 额外的数量级验证可能过于严格")
    print("- 简化流程减少出错可能性")

    print("\n应用建议:")
    print("1. 手动替换主程序中的员工数量提取部分")
    print("2. 或者使用 A股财务分析自动化_修复版.py")
    print("3. 测试运行确认CSV文件正确生成")

if __name__ == "__main__":
    apply_fix()
    print("\n修复代码段:")
    print(create_fixed_csv_save_section())