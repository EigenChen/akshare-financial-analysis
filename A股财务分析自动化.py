# -*- coding: utf-8 -*-
"""
A股财务分析自动化工具

功能：
1. 自动下载年报PDF
2. 自动提取员工数量
3. 自动生成财务分析Excel
"""

import os
import sys
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st
import akshare as ak

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -----------------------------
# 页面配置
# -----------------------------
st.set_page_config(
    page_title="A股财务分析自动化",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# 动态导入模块
# -----------------------------
def load_module(name: str, path: str):
    """动态加载模块"""
    module_path = ROOT / path
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# -----------------------------
# 辅助函数：获取企业名称
# -----------------------------
def get_symbol_name(symbol: str) -> str:
    """
    获取股票名称
    
    参数:
        symbol: 股票代码，如 "600519"
    
    返回:
        股票名称
    """
    try:
        symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
        stock_list = ak.stock_info_a_code_name()
        stock_info = stock_list[stock_list['code'] == symbol_clean]
        if not stock_info.empty:
            return stock_info.iloc[0]['name']
        return symbol_clean
    except Exception as e:
        st.warning(f"获取企业名称失败: {e}")
        return symbol.replace('.SZ', '').replace('.SH', '')

# -----------------------------
# 辅助函数：获取上市日期和年份
# -----------------------------
def get_listing_date(symbol: str) -> Optional[str]:
    """
    获取股票的上市日期
    
    参数:
        symbol: 股票代码，如 "600519" 或 "000001"
    
    返回:
        上市日期（字符串），如果获取失败返回None
    """
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    
    try:
        # 方法1: 尝试使用股票基本信息接口（适用于所有A股，包括科创板）
        try:
            basic_info = ak.stock_individual_info_em(symbol=symbol_clean)
            if basic_info is not None and not basic_info.empty:
                # 查找上市时间/上市日期
                for idx, row in basic_info.iterrows():
                    item = str(row.get('item', ''))
                    value = row.get('value', '')
                    if '上市' in item and ('时间' in item or '日期' in item):
                        # 处理日期格式：可能是"20221018"或"2022-10-18"
                        date_str = str(value)
                        if len(date_str) == 8 and date_str.isdigit():
                            # 格式化为"2022-10-18"
                            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                        return date_str
        except:
            pass
        
        # 方法2: 使用上交所接口（非科创板）
        if symbol_clean.startswith(('600', '601', '603', '605')):
            try:
                stock_info = ak.stock_info_sh_name_code()
                if stock_info is not None and not stock_info.empty:
                    stock_data = stock_info[stock_info['证券代码'] == symbol_clean]
                    if not stock_data.empty and '上市日期' in stock_data.columns:
                        listing_date = stock_data.iloc[0]['上市日期']
                        return listing_date
            except:
                pass
        
        # 方法3: 使用深交所接口
        if symbol_clean.startswith(('000', '001', '002', '003', '300')):
            try:
                stock_info = ak.stock_info_sz_name_code()
                if stock_info is not None and not stock_info.empty:
                    # 检查列名（可能是'A股代码'或'代码'）
                    code_col = None
                    for col in stock_info.columns:
                        if '代码' in col:
                            code_col = col
                            break
                    
                    if code_col:
                        stock_data = stock_info[stock_info[code_col] == symbol_clean]
                        if not stock_data.empty:
                            # 查找上市日期列
                            date_col = None
                            for col in stock_data.columns:
                                if '上市' in col and '日期' in col:
                                    date_col = col
                                    break
                            
                            if date_col:
                                listing_date = stock_data.iloc[0][date_col]
                                return listing_date
            except:
                pass
        
        return None
    except Exception as e:
        return None

def get_listing_year(symbol: str) -> Optional[int]:
    """
    获取股票的上市年份
    
    参数:
        symbol: 股票代码
    
    返回:
        上市年份（整数），如果获取失败返回None
    """
    listing_date = get_listing_date(symbol)
    if listing_date:
        try:
            # 尝试从日期字符串中提取年份
            # 日期格式可能是 "2020-01-01" 或 "20200101"
            if '-' in str(listing_date):
                year = int(str(listing_date).split('-')[0])
            else:
                year = int(str(listing_date)[:4])
            return year
        except:
            return None
    return None

# -----------------------------
# 辅助函数：验证员工数量（数量级检查）
# -----------------------------
def validate_employee_count(year: int, count: Optional[int], all_counts: Dict[int, Optional[int]]) -> Optional[int]:
    """
    验证员工数量是否合理（通过前后年份对比）
    
    参数:
        year: 年份
        count: 当前年份的员工数量
        all_counts: 所有年份的员工数量字典 {年份: 数量}
    
    返回:
        验证后的员工数量，如果不合理返回None（用"-"表示）
    """
    if count is None:
        return None
    
    # 获取前后年份的数量
    prev_year_count = all_counts.get(year - 1)
    next_year_count = all_counts.get(year + 1)
    
    # 如果前后年份都有数据，进行数量级检查
    if prev_year_count is not None and next_year_count is not None:
        # 计算平均值作为参考
        avg_count = (prev_year_count + next_year_count) / 2
        
        # 如果当前数量与平均值相差超过10倍，认为不合理
        if avg_count > 0:
            ratio = count / avg_count
            if ratio > 10 or ratio < 0.1:
                return None
    
    # 如果只有前一年有数据
    elif prev_year_count is not None:
        if prev_year_count > 0:
            ratio = count / prev_year_count
            if ratio > 10 or ratio < 0.1:
                return None
    
    # 如果只有后一年有数据
    elif next_year_count is not None:
        if next_year_count > 0:
            ratio = count / next_year_count
            if ratio > 10 or ratio < 0.1:
                return None
    
    return count

# -----------------------------
# 辅助函数：处理员工数量数据（添加数量级检查）
# -----------------------------
def process_employee_counts(results: List[Tuple[str, Optional[int], Optional[int]]]) -> Dict[int, Optional[int]]:
    """
    处理员工数量提取结果，添加数量级检查
    
    参数:
        results: process_directory返回的结果列表 [(文件路径, 年份, 员工数量), ...]
    
    返回:
        处理后的字典 {年份: 员工数量}
    """
    # 先收集所有数据
    all_counts = {}
    for file_path, year, count in results:
        if year is not None:
            all_counts[year] = count
    
    # 验证每个年份的数量
    validated_counts = {}
    for year in sorted(all_counts.keys()):
        count = all_counts[year]
        validated_count = validate_employee_count(year, count, all_counts)
        validated_counts[year] = validated_count
    
    return validated_counts

# -----------------------------
# 主界面
# -----------------------------
st.title("🤖 A股财务分析自动化")
st.caption("一键完成年报下载、员工数量提取和财务分析")
st.markdown("---")

# 初始化session_state
if 'work_dir' not in st.session_state:
    st.session_state['work_dir'] = ""

# 左侧：条件输入
with st.sidebar:
    st.header("📋 条件输入")
    
    # 1. 股票代码输入
    st.subheader("📊 股票代码")
    symbol = st.text_input(
        "输入股票代码",
        value="603486",
        help="输入6位A股股票代码，如 600519、000001",
        key="symbol_input"
    )
    
    # 获取上市年份（如果股票代码改变，重新获取）
    if symbol:
        listing_year_key = f'listing_year_{symbol}'
        listing_date_key = f'listing_date_{symbol}'
        
        # 检查是否需要重新获取
        need_refetch = (listing_year_key not in st.session_state or 
                       st.session_state.get('last_symbol') != symbol)
        
        if need_refetch:
            # 重新获取
            try:
                with st.spinner("正在获取上市年份..."):
                    listing_date = get_listing_date(symbol)
                    listing_year = get_listing_year(symbol)
                    st.session_state[listing_year_key] = listing_year
                    st.session_state[listing_date_key] = listing_date
                    st.session_state['last_symbol'] = symbol
            except Exception as e:
                # 获取失败，记录None
                st.session_state[listing_year_key] = None
                st.session_state[listing_date_key] = None
                st.session_state['last_symbol'] = symbol
        
        # 显示上市年份
        listing_year = st.session_state.get(listing_year_key)
        listing_date = st.session_state.get(listing_date_key)
        
        if listing_year:
            if listing_date:
                st.caption(f"📅 上市日期: {listing_date} (上市年份: {listing_year}年)")
            else:
                st.caption(f"📅 上市年份: {listing_year}年")
        elif need_refetch:
            # 刚刚尝试获取但失败了
            st.caption("⚠️ 正在获取上市年份信息...")
        else:
            # 之前获取过但失败了
            st.caption("⚠️ 未能获取上市年份信息，请检查股票代码是否正确")
    
    # 2. 文件目录选择
    st.subheader("📁 工作目录")
    
    def select_work_folder():
        """打开文件夹选择对话框"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder_path = filedialog.askdirectory(title="选择工作目录")
            root.destroy()
            return folder_path if folder_path else None
        except Exception as e:
            st.warning(f"文件夹选择器不可用: {e}，请手动输入路径")
            return None
    
    col1, col2 = st.columns([3, 1])
    with col1:
        work_dir = st.text_input(
            "工作目录",
            value=st.session_state.get('work_dir', ""),
            placeholder="选择或输入工作目录"
        )
        if work_dir and work_dir != st.session_state.get('work_dir'):
            st.session_state['work_dir'] = work_dir
    with col2:
        if st.button("📁", use_container_width=True, help="选择工作目录", key="select_work_dir_btn"):
            selected_folder = select_work_folder()
            if selected_folder:
                st.session_state['work_dir'] = selected_folder
                st.rerun()
    
    # 显示当前工作目录
    if st.session_state.get('work_dir'):
        st.info(f"当前目录：\n`{st.session_state['work_dir']}`")
    
    st.markdown("---")
    
    # 3. 年份范围
    st.subheader("📅 年份范围")
    
    # 计算默认结束年份
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    # 根据当前日期计算默认结束年份
    # 1月1日到4月30日：前年（当前年份-2）
    # 5月1日到12月31日：上一年（当前年份-1）
    if 1 <= current_month <= 4:
        default_end_year = current_year - 2
    else:  # 5月到12月
        default_end_year = current_year - 1
    
    # 获取默认起始年份
    # 如果上市年份晚于2015年，则使用上市年份；否则使用2015年
    listing_year = st.session_state.get(listing_year_key)
    if listing_year and listing_year > 2015:
        default_start_year = listing_year
    else:
        default_start_year = 2015
    
    col3, col4 = st.columns(2)
    with col3:
        start_year = st.number_input(
            "起始年份",
            min_value=1990,  # 支持更早的上市年份
            max_value=2035,
            value=default_start_year,  # 上市年份>2015则用上市年份，否则用2015
            step=1
        )
    with col4:
        end_year = st.number_input(
            "结束年份",
            min_value=1990,  # 支持更早的上市年份
            max_value=2035,
            value=default_end_year,  # 根据当前日期动态计算
            step=1
        )
    
    if start_year > end_year:
        st.error("起始年份不能大于结束年份")
        st.stop()
    
    st.markdown("---")

    # 下载财报选项（默认勾选）
    download_report = st.checkbox(
        "下载年报PDF",
        value=True,
        help="勾选则下载年报PDF；不勾选则跳过下载（步骤4仍会从目录内已有 PDF 提取员工数量）"
    )

    st.markdown("---")

    # 4. 开始分析按钮
    analyze_btn = st.button(
        "🚀 开始财务分析",
        type="primary",
        use_container_width=True,
        disabled=not symbol or not st.session_state.get('work_dir')
    )

# 右侧：执行过程和结果
if analyze_btn:
    if not symbol:
        st.error("❌ 请输入股票代码")
        st.stop()
    
    if not st.session_state.get('work_dir'):
        st.error("❌ 请选择工作目录")
        st.stop()
    
    work_dir = st.session_state['work_dir']
    
    # 显示执行过程
    st.header("📊 执行过程")
    
    progress_container = st.container()
    log_container = st.container()
    
    with log_container:
        st.markdown("### 步骤1: 获取企业信息")
    
    try:
        # 步骤1: 获取企业名称
        with log_container:
            st.write(f"正在查询股票代码: {symbol}")
        
        company_name = get_symbol_name(symbol)
        
        if not company_name or company_name == symbol:
            st.error(f"❌ 无法获取企业名称，请检查股票代码是否正确: {symbol}")
            st.stop()
        
        # 获取上市日期信息
        listing_date = get_listing_date(symbol)
        listing_year = get_listing_year(symbol)
        
        with log_container:
            st.success(f"✅ 企业名称: {company_name}")
            if listing_date and listing_year:
                st.info(f"📅 上市日期: {listing_date} (上市年份: {listing_year}年)")
            elif listing_year:
                st.info(f"📅 上市年份: {listing_year}年")
        
        # 步骤2: 创建工作目录
        with log_container:
            st.markdown("### 步骤2: 创建工作目录")
        
        # 创建目录：企业名称 股票代码
        company_dir = os.path.join(work_dir, f"{company_name} {symbol}")
        os.makedirs(company_dir, exist_ok=True)
        
        with log_container:
            st.success(f"✅ 工作目录已创建: `{company_dir}`")
        
        # 步骤3: 下载年报PDF（仅当勾选时执行）
        if download_report:
            with log_container:
                st.markdown("### 步骤3: 下载年报PDF")

            # 2020年特殊提示
            if start_year <= 2020 <= end_year:
                st.warning("⚠️ 注意：2020年年报受COVID-19疫情影响，发布时间普遍延期，程序下载成功率较低（约30-40%）")
                with st.expander("📖 查看2020年年报手动下载指导（推荐）"):
                    st.markdown(f"""
                    **🎯 推荐方案：手动下载（成功率95%+）**

                    **📍 推荐网站：巨潮资讯网**
                    - 🌐 网址：http://www.cninfo.com.cn

                    **📋 操作步骤：**
                    1. 访问巨潮资讯网首页
                    2. 在搜索框输入股票代码：`{symbol}`
                    3. 点击搜索结果中的公司名称
                    4. 选择"定期报告"选项卡
                    5. 筛选年份为"2020年"，类型为"年度报告"
                    6. 点击PDF图标下载年报文件

                    **⏰ 重要提示：**
                    - 2020年年报可能在2021年4月-2022年期间发布
                    - 如果2021年没找到，请在2022年中查找
                    - 建议保存文件名：`{symbol}_2020年年度报告.pdf`

                    **🔄 备用网站：**
                    - 深交所官网：http://www.szse.cn（适用于{symbol}）
                    - 东方财富：http://data.eastmoney.com/notices/
                    """)
                st.info("💡 程序仍会尝试自动下载，但如遇失败，请参考上述手动下载指导")

            # 加载PDF下载模块
            try:
                pdf_dl = load_module("pdf_downloader", "core/a_share/annual_report_downloader.py")
            except Exception as e:
                st.error(f"❌ 加载PDF下载模块失败: {e}")
                st.stop()

            years = list(range(start_year, end_year + 1))
            download_results = {'success': [], 'failed': []}

            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, year in enumerate(years):
                status_text.text(f"正在下载 {year} 年年报... ({idx + 1}/{len(years)})")
                try:
                    filepath = pdf_dl.download_annual_report(symbol, year, company_dir)
                    if filepath and os.path.exists(filepath):
                        file_size = os.path.getsize(filepath) / 1024 / 1024
                        download_results['success'].append({
                            'year': year,
                            'path': filepath,
                            'size': f"{file_size:.2f} MB"
                        })
                        with log_container:
                            st.write(f"  ✅ {year}年: {os.path.basename(filepath)} ({file_size:.2f} MB)")
                    else:
                        download_results['failed'].append({'year': year, 'reason': '未找到年报或下载失败'})
                        with log_container:
                            st.write(f"  ⚠️ {year}年: 下载失败")
                except Exception as e:
                    download_results['failed'].append({'year': year, 'reason': str(e)})
                    with log_container:
                        st.write(f"  ❌ {year}年: {e}")
                progress_bar.progress((idx + 1) / len(years))

            # 清除状态文本
            status_text.empty()
            progress_bar.empty()

            with log_container:
                st.info(f"📊 下载完成: 成功 {len(download_results['success'])} 个，失败 {len(download_results['failed'])} 个")
        else:
            with log_container:
                st.info("⏭️ 已跳过步骤3：下载年报PDF（未勾选「下载年报PDF」）。步骤4将尝试从目录内已有PDF提取员工数量。")

        # 步骤4: 提取员工数量（始终执行，使用智能算法）
        with log_container:
            st.markdown("### 步骤4: 提取员工数量")

        try:
            emp_module = load_module("employee_extractor", "core/a_share/employee_extractor.py")
        except Exception as e:
            st.error(f"❌ 加载智能员工数量提取模块失败: {e}")
            st.stop()

        with log_container:
            st.write("正在从PDF中提取员工数量...")
            st.write(f"PDF目录: {company_dir}")

        try:
            with log_container:
                st.write("正在使用智能算法提取员工数量...")

            batch_results = emp_module.batch_extract_employee_count_smart(
                company_dir,
                stock_code=symbol,
                use_smart=True
            )

            with log_container:
                st.write(f"智能算法提取完成，处理了 {len(batch_results)} 个文件")

            employee_counts = {}
            import re
            for filename, count in batch_results.items():
                year = None
                try:
                    year_patterns = [
                        r'(\d{4})年',
                        r'_(\d{4})年',
                        r'(\d{4})年度',
                        r'(\d{4})(?=年度报告)',
                        r'(?:20\d{2})',
                    ]
                    for pattern in year_patterns:
                        year_match = re.search(pattern, filename)
                        if year_match:
                            year_str = year_match.group(1) if year_match.groups() else year_match.group(0)
                            year_num = int(year_str)
                            if 2000 <= year_num <= 2030:
                                year = year_num
                                break
                    if year is None:
                        all_four_digits = re.findall(r'\b(\d{4})\b', filename)
                        for digit in all_four_digits:
                            digit_int = int(digit)
                            if 2000 <= digit_int <= 2030:
                                year = digit_int
                                break
                except Exception as e:
                    pass

                if year is not None:
                    employee_counts[year] = count

                with log_container:
                    if count:
                        st.write(f"  {year}年 ({filename}): {count:,}人")
                    else:
                        st.write(f"  {year}年 ({filename}): 提取失败")

            csv_path = os.path.join(company_dir, f"{symbol}_员工数量.csv")
            with log_container:
                st.write(f"正在保存CSV文件到: {os.path.basename(csv_path)}")

            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['年份', '员工数量'])
                saved_rows = 0
                for year in sorted(employee_counts.keys()):
                    count = employee_counts[year]
                    csv_value = count if count is not None else '-'
                    writer.writerow([year, csv_value])
                    saved_rows += 1
                    with log_container:
                        if count is not None:
                            st.write(f"  保存: {year}年 -> {count:,}人")
                        else:
                            st.write(f"  保存: {year}年 -> 无数据")

            if os.path.exists(csv_path):
                file_size = os.path.getsize(csv_path)
                with log_container:
                    st.success(f"✅ CSV文件保存成功!")
                    st.write(f"   文件路径: `{csv_path}`")
                    st.write(f"   文件大小: {file_size} bytes")
                    st.write(f"   数据行数: {saved_rows}")
                    try:
                        df = pd.read_csv(csv_path, encoding='utf-8-sig')
                        st.write(f"   验证读取: {len(df)} 行数据")
                        st.write("   CSV内容预览:")
                        with open(csv_path, 'r', encoding='utf-8-sig') as f:
                            lines = f.readlines()
                            for i, line in enumerate(lines[:6]):
                                st.code(f"第{i+1}行: {line.strip()}")
                    except Exception as e:
                        st.warning(f"   CSV读取验证失败: {e}")
            else:
                with log_container:
                    st.error("❌ CSV文件保存失败 - 文件不存在")

            with log_container:
                st.write("**员工数量提取结果汇总:**")
                result_df = pd.DataFrame([
                    {'年份': year, '员工数量': count if count is not None else '-'}
                    for year, count in sorted(employee_counts.items())
                ])
                display_df = result_df.astype(str)
                st.dataframe(display_df, use_container_width=True)

        except Exception as e:
            st.error(f"❌ 提取员工数量失败: {e}")
            import traceback
            st.code(traceback.format_exc())

        # 步骤5: 生成财务分析Excel
        with log_container:
            st.markdown("### 步骤5: 生成财务分析Excel")
        
        # 加载财务分析模块
        try:
            fa_module = load_module("financial_analysis", "core/a_share/financial_analysis.py")
        except Exception as e:
            st.error(f"❌ 加载财务分析模块失败: {e}")
            st.stop()
        
        # 准备员工数量CSV路径
        employee_csv_path = (csv_path if csv_path and os.path.exists(csv_path) else None)
        
        with log_container:
            st.write("正在生成财务分析报告...")
        
        try:
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # 调用财务分析函数（所有9个Sheet）
            analysis_functions = [
                ('营收基本数据', fa_module.calculate_revenue_metrics),
                ('费用构成', fa_module.calculate_expense_metrics),
                ('增长', fa_module.calculate_growth_metrics),
                ('资产负债', fa_module.calculate_balance_sheet_metrics),
                ('WC分析', fa_module.calculate_wc_metrics),
                ('固定资产投入分析', fa_module.calculate_fixed_asset_metrics),
                ('收益率和杜邦分析', fa_module.calculate_roi_metrics),
                ('资产周转', fa_module.calculate_asset_turnover_metrics),
                ('人均数据', fa_module.calculate_per_capita_metrics),
            ]
            
            excel_filepath = None
            
            for sheet_name, func in analysis_functions:
                with log_container:
                    st.write(f"  正在计算: {sheet_name}...")
                
                try:
                    if sheet_name == '人均数据':
                        df = func(symbol, start_year, end_year, employee_csv_path=employee_csv_path)
                    else:
                        df = func(symbol, start_year, end_year)
                    
                    if df is not None and not df.empty:
                        excel_filepath = fa_module.save_to_excel(
                            df, symbol, company_name, start_year, end_year, 
                            sheet_name, timestamp=timestamp, output_dir=company_dir
                        )
                        with log_container:
                            st.write(f"    ✅ {sheet_name} 已完成")
                    else:
                        with log_container:
                            st.write(f"    ⚠️ {sheet_name} 数据为空")
                except Exception as e:
                    with log_container:
                        st.write(f"    ❌ {sheet_name} 计算失败: {e}")
            
            if excel_filepath and os.path.exists(excel_filepath):
                with log_container:
                    st.success(f"✅ 财务分析Excel已生成: `{excel_filepath}`")
            else:
                # 尝试从output目录查找
                output_filepath = os.path.join("output", f"{company_name}_{start_year}-{end_year}_财务分析_{timestamp}.xlsx")
                if os.path.exists(output_filepath):
                    # 移动到工作目录
                    import shutil
                    final_path = os.path.join(company_dir, os.path.basename(output_filepath))
                    shutil.move(output_filepath, final_path)
                    with log_container:
                        st.success(f"✅ 财务分析Excel已生成: `{final_path}`")
                else:
                    with log_container:
                        st.warning("⚠️ 财务分析Excel文件未找到，请检查output目录")
        
        except Exception as e:
            st.error(f"❌ 生成财务分析Excel失败: {e}")
            import traceback
            st.code(traceback.format_exc())
        
        # 完成
        with log_container:
            st.markdown("---")
            st.success("🎉 所有步骤已完成！")
            st.info(f"📁 所有文件已保存到: `{company_dir}`")
    
    except Exception as e:
        st.error(f"❌ 执行失败: {e}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("👈 请在左侧输入股票代码、选择工作目录，然后点击【开始财务分析】按钮")
