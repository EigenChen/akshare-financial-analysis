# -*- coding: utf-8 -*-
"""
统一财务工具（A股 + 港股）

整合三大功能：
1) 财务分析（9个Sheet，A股/港股）
2) 历年三大报表下载（资产负债表、利润表、现金流量表）
3) 历年员工数量提取（年报PDF）

说明：
- A股默认货币：人民币（CNY）
- 港股默认货币：港币（HKD），不进行货币转换
"""

import os
import io
import sys
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -----------------------------
# 工具：动态导入模块
# -----------------------------
def load_module(name: str, path: str):
    module_path = ROOT / path
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# 预加载核心模块
fa_a = load_module("financial_analysis_a", "core/a_share/financial_analysis.py")
fa_hk = load_module("financial_analysis_hk", "core/hk/financial_analysis_full.py")
hk_adapter = load_module("hk_adapter", "core/hk/financial_adapter.py")
dl_tool = load_module("report_downloader", "core/tools/report_downloader.py")
emp_a = load_module("emp_a", "core/a_share/employee_extractor.py")
emp_hk = load_module("emp_hk", "core/hk/employee_extractor.py")

# -----------------------------
# 页面配置
# -----------------------------
st.set_page_config(
    page_title="统一财务工具（A股+港股）",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# 侧边栏：市场与功能选择
# -----------------------------
st.sidebar.header("🌍 市场与功能")
market = st.sidebar.radio("选择市场", ["A股", "港股"], horizontal=True)

# 功能列表（A股和港股都支持年报PDF下载）
feature_options = ["📊 财务分析", "📄 报表下载", "👥 员工数量提取", "📥 年报PDF下载"]

feature = st.sidebar.radio("选择功能", feature_options)

# 公共输入：股票代码与年份
st.sidebar.markdown("---")
symbol_help = "A股：6位代码，如 603486；港股：5位代码，如 00700"
symbol_default = "603486" if market == "A股" else "00700"
symbol = st.sidebar.text_input("股票代码", value=symbol_default, help=symbol_help)

col_y1, col_y2 = st.sidebar.columns(2)
with col_y1:
    start_year = st.number_input("起始年份", min_value=2000, max_value=2035, value=2020, step=1)
with col_y2:
    end_year = st.number_input("结束年份", min_value=2000, max_value=2035, value=2024, step=1)
if start_year > end_year:
    st.sidebar.error("起始年份不能大于结束年份")
    st.stop()

# -----------------------------
# 辅助函数：获取公式说明
# -----------------------------
def get_formula_notes(sheet_name):
    """
    获取指定sheet的公式说明
    
    参数:
        sheet_name: Sheet名称
    
    返回:
        字典，格式为 {指标名称: 公式说明}
    """
    formula_notes = {}
    
    if sheet_name == '营收基本数据':
        formula_notes = {
            '金融利润（亿元）': '金融利润 = 公允价值变动收益 + 投资收益',
            '经营利润（亿元）': '经营利润 = 归母净利润 - 金融利润',
            'CAPEX（亿元）': 'CAPEX = 购建固定资产、无形资产和其他长期资产支付的现金（来自现金流量表）'
        }
    elif sheet_name == '资产负债':
        formula_notes = {
            '狭义无息债务（亿元）': '狭义无息债务 = 应付账款 + 预收账款 + 合同负债',
            '广义无息债务（亿元）': '广义无息债务 = 应付账款 + 应付票据 + 预收账款 + 合同负债'
        }
    elif sheet_name == 'WC分析':
        formula_notes = {
            'WC（亿元）': 'WC = (应收账款 + 预付账款 + 存货 + 合同资产) - (应付账款 + 预收账款 + 合同负债)'
        }
    elif sheet_name == '固定资产投入分析':
        formula_notes = {
            '固定资产（亿元）': '固定资产 = 固定资产 + 在建工程 + 工程物资 - 固定资产清理',
            '长期资产（亿元）': '长期资产 = 固定资产 + 无形资产 + 开发支出 + 使用权资产 + 商誉 + 长期待摊费用'
        }
    elif sheet_name == '收益率和杜邦分析':
        formula_notes = {
            'ROIC(%)': 'ROIC = EBIT / 投入资本 × 100，其中EBIT = 营业利润 + 利息支出，投入资本 = 总资产 - 狭义无息债务（应付账款 + 预收账款 + 合同负债）'
        }
    
    return formula_notes

# -----------------------------
# 功能 1：财务分析
# -----------------------------
def run_financial_analysis():
    st.header("📊 财务分析结果")
    # 分析模块选择
    st.sidebar.markdown("### 📋 分析模块")
    modules = {
        "营收基本数据": st.sidebar.checkbox("营收基本数据", value=True),
        "费用构成": st.sidebar.checkbox("费用构成", value=True),
        "增长率": st.sidebar.checkbox("增长率", value=True),
        "资产负债": st.sidebar.checkbox("资产负债", value=True),
        "WC分析": st.sidebar.checkbox("WC分析", value=True),
        "固定资产投入分析": st.sidebar.checkbox("固定资产投入分析", value=True),
        "收益率和杜邦分析": st.sidebar.checkbox("收益率和杜邦分析", value=True),
        "资产周转": st.sidebar.checkbox("资产周转", value=True),
        "人均数据": st.sidebar.checkbox("人均数据", value=True),
    }
    # 可选员工CSV
    employee_csv = st.sidebar.file_uploader("员工数量CSV（可选，年份,员工数量）", type=["csv"])

    run_btn = st.sidebar.button("🚀 开始分析", type="primary", use_container_width=True)
    
    # 先检查是否有已保存的结果
    session_key = f"analysis_results_{market}_{symbol}_{start_year}_{end_year}"
    
    # 如果点击了按钮，执行分析
    if run_btn:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        results: Dict[str, pd.DataFrame] = {}

        try:
            if market == "A股":
                fa = fa_a
            else:
                fa = fa_hk
            company_name = fa.get_symbol_name(symbol) if hasattr(fa, "get_symbol_name") else symbol

            progress = st.progress(0)
            done = 0
            total = sum(modules.values()) or 1

            def step():
                nonlocal done
                done += 1
                progress.progress(min(1.0, done / total))

            # 营收基本数据
            if modules["营收基本数据"]:
                df = fa.calculate_revenue_metrics(symbol, start_year, end_year)
                if df is not None and not df.empty:
                    results["营收基本数据"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "营收基本数据", timestamp=timestamp)
                step()
            # 费用构成
            if modules["费用构成"]:
                df = fa.calculate_expense_metrics(symbol, start_year, end_year)
                if df is not None and not df.empty:
                    results["费用构成"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "费用构成", timestamp=timestamp)
                step()
            # 增长率
            if modules["增长率"]:
                df = fa.calculate_growth_metrics(symbol, start_year, end_year)
                if df is not None and not df.empty:
                    results["增长"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "增长", timestamp=timestamp)
                step()
            # 资产负债
            if modules["资产负债"]:
                df = fa.calculate_balance_sheet_metrics(symbol, start_year, end_year)
                if df is not None and not df.empty:
                    results["资产负债"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "资产负债", timestamp=timestamp)
                step()
            # WC分析
            if modules["WC分析"]:
                df = fa.calculate_wc_metrics(symbol, start_year, end_year)
                if df is not None and not df.empty:
                    results["WC分析"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "WC分析", timestamp=timestamp)
                step()
            # 固定资产投入分析
            if modules["固定资产投入分析"]:
                df = fa.calculate_fixed_asset_metrics(symbol, start_year, end_year)
                if df is not None and not df.empty:
                    results["固定资产投入分析"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "固定资产投入分析", timestamp=timestamp)
                step()
            # 收益率和杜邦分析
            if modules["收益率和杜邦分析"]:
                df = fa.calculate_roi_metrics(symbol, start_year, end_year)
                if df is not None and not df.empty:
                    results["收益率和杜邦分析"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "收益率和杜邦分析", timestamp=timestamp)
                step()
            # 资产周转
            if modules["资产周转"]:
                df = fa.calculate_asset_turnover_metrics(symbol, start_year, end_year)
                if df is not None and not df.empty:
                    results["资产周转"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "资产周转", timestamp=timestamp)
                step()
            # 人均数据
            if modules["人均数据"]:
                csv_path = None
                if employee_csv:
                    import tempfile
                    csv_bytes = employee_csv.getvalue()
                    # 使用系统临时目录，兼容 Windows 和 Linux
                    temp_dir = tempfile.gettempdir()
                    csv_path = os.path.join(temp_dir, employee_csv.name)
                    with open(csv_path, "wb") as f:
                        f.write(csv_bytes)
                df = fa.calculate_per_capita_metrics(symbol, start_year, end_year, employee_csv_path=csv_path)
                if df is not None and not df.empty:
                    results["人均数据"] = df
                    fa.save_to_excel(df, symbol, company_name, start_year, end_year, "人均数据", timestamp=timestamp)
                step()

            progress.progress(1.0)
            st.success("分析完成！")

            if not results:
                st.warning("未生成任何结果，请检查数据是否可用。")
                return

            # 保存结果到 session_state
            st.session_state[session_key] = results
            st.session_state[f"{session_key}_company"] = company_name
            st.session_state[f"{session_key}_timestamp"] = timestamp
            # 注意：save_to_excel函数统一使用"财务分析"作为文件名，不区分A股/港股
            st.session_state[f"{session_key}_filepath"] = os.path.join("output", f"{company_name}_{start_year}-{end_year}_财务分析_{timestamp}.xlsx")

        except Exception as e:
            st.error(f"分析失败：{e}")
            import traceback
            st.code(traceback.format_exc())

    # 显示分析结果（从 session_state 读取）
    if session_key in st.session_state:
        results = st.session_state[session_key]
        company_name = st.session_state.get(f"{session_key}_company", symbol)
        timestamp = st.session_state.get(f"{session_key}_timestamp", "")
        filepath = st.session_state.get(f"{session_key}_filepath", "")

        sheet = st.selectbox("选择要查看的Sheet", list(results.keys()))
        
        # 显示数据表格
        st.subheader(f"📊 {sheet}")
        # 将DataFrame转换为字符串类型以避免PyArrow类型转换问题（混合类型：数值和"-"）
        display_df = results[sheet].astype(str)
        st.dataframe(display_df, width='stretch', height=420)
        
        # 显示公式注释
        formula_notes = get_formula_notes(sheet)
        if formula_notes:
            st.markdown("---")
            st.subheader("📝 公式说明")
            for metric_name, formula in formula_notes.items():
                st.markdown(f"**{metric_name}**: {formula}")
        
        # 趋势图（仅显示数值指标）
        try:
            df = results[sheet]
            # DataFrame 格式：第一列是"科目"，其他列是年份（如'2020', '2021'等）
            if "科目" in df.columns:
                # 获取所有年份列（数字字符串）
                year_cols = [col for col in df.columns if col != "科目" and col.isdigit()]
                
                if len(year_cols) >= 2:  # 至少需要2年数据才能画趋势
                    st.subheader("📈 趋势图")
                    
                    # 获取所有科目（指标）
                    all_metrics = df["科目"].tolist()
                    
                    # 用户选择要显示的指标
                    selected_metrics = st.multiselect(
                        "选择要可视化的指标",
                        options=all_metrics,
                        default=all_metrics[:min(3, len(all_metrics))],  # 默认选前3个
                        key=f"chart_metrics_{sheet}"
                    )
                    
                    if selected_metrics:
                        # 准备绘图数据
                        chart_data = []
                        for metric in selected_metrics:
                            metric_row = df[df["科目"] == metric]
                            if not metric_row.empty:
                                for year_col in year_cols:
                                    value = metric_row[year_col].iloc[0]
                                    # 跳过 "-" 和非数值
                                    if value != "-" and pd.notna(value):
                                        try:
                                            numeric_value = float(value)
                                            chart_data.append({
                                                "年份": int(year_col),
                                                "指标": metric,
                                                "数值": numeric_value
                                            })
                                        except (ValueError, TypeError):
                                            pass
                        
                        if chart_data:
                            chart_df = pd.DataFrame(chart_data)
                            fig = px.line(
                                chart_df,
                                x="年份",
                                y="数值",
                                color="指标",
                                markers=True,
                                title=f"{sheet} - 趋势图"
                            )
                            fig.update_layout(hovermode="x unified")
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("💡 所选指标没有可绘制的数值数据")
        except Exception as e:
            st.warning(f"⚠️ 图表生成失败：{str(e)}")
            import traceback
            st.code(traceback.format_exc())

        # 下载Excel文件
        if filepath and os.path.exists(filepath):
            with open(filepath, "rb") as f:
                st.download_button("📥 下载Excel文件", data=f.read(), file_name=os.path.basename(filepath),
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Excel 文件尚未生成或路径不存在。")
    else:
        # 没有结果，提示用户
        st.info("在左侧选择分析模块并点击【开始分析】按钮。")

# -----------------------------
# 功能 2：报表下载
# -----------------------------
def run_report_download():
    st.header("📄 财务报表下载")
    st.sidebar.markdown("### 📋 报表类型")
    dl_balance = st.sidebar.checkbox("资产负债表", value=True)
    dl_profit = st.sidebar.checkbox("利润表", value=True)
    dl_cash = st.sidebar.checkbox("现金流量表", value=True)
    run_btn = st.sidebar.button("🚀 开始下载", type="primary", use_container_width=True)
    
    # 初始化 session_state
    session_key = f"report_data_{market}_{symbol}_{start_year}_{end_year}"
    if run_btn:
        # 点击按钮时清空旧数据
        if session_key in st.session_state:
            del st.session_state[session_key]
        if f"{session_key}_excel" in st.session_state:
            del st.session_state[f"{session_key}_excel"]
        if f"{session_key}_company" in st.session_state:
            del st.session_state[f"{session_key}_company"]
    
    # 如果已有数据，直接使用；否则提示用户点击按钮
    if session_key not in st.session_state:
        if not run_btn:
            st.info("在左侧选择报表类型并点击开始下载。")
            return
    else:
        # 已有数据，显示预览和下载
        result_dict = st.session_state[session_key]
        excel_bytes = st.session_state.get(f"{session_key}_excel")
        company_name = st.session_state.get(f"{session_key}_company", symbol)
        
        # 显示预览选择器（A股和港股都支持）
        st.subheader(f"📊 {'A股' if market == 'A股' else '港股'}报表预览")
        year_options = sorted(result_dict.keys())
        if year_options:
            col_y, col_t = st.columns(2)
            with col_y:
                sel_year = st.selectbox("选择年份", year_options, key=f"report_year_{market}")
            with col_t:
                sel_type = st.selectbox("选择报表类型", ["资产负债表", "利润表", "现金流量表"], key=f"report_type_{market}")
            
            stmt_map = {
                "资产负债表": "balance",
                "利润表": "profit",
                "现金流量表": "cash_flow",
            }
            df_preview = result_dict.get(sel_year, {}).get(stmt_map[sel_type])
            if df_preview is None or df_preview.empty:
                st.info(f"{sel_year} 年的 {sel_type} 数据为空。")
            else:
                # A股数据已经是格式化后的（科目、中文科目、数值(亿)），港股需要转置
                if market == "A股":
                    # A股：直接显示，但只显示科目和数值(亿)
                    display_df = df_preview[["科目", "数值(亿)"]].copy()
                    display_df.columns = ["科目", "数值(亿元)"]
                else:
                    # 港股：转置，并转换为亿元，使用中文名称
                    # 排除 REPORT_DATE 列
                    df_to_transpose = df_preview.drop(columns=['REPORT_DATE'], errors='ignore')
                    df_t = df_to_transpose.T.reset_index()
                    df_t.columns = ["科目", "数值"]
                    # 将金额从元转换为亿元（跳过非数值）
                    def convert_to_yi(x):
                        if pd.isna(x) or str(x) == 'nan':
                            return x
                        try:
                            return round(float(x) / 100000000, 2)
                        except (ValueError, TypeError):
                            return x
                    df_t["数值"] = df_t["数值"].apply(convert_to_yi)
                    # 使用中文名称映射替换英文字段名
                    chinese_mappings = st.session_state.get(f"{session_key}_chinese_mappings", {})
                    stmt_key = stmt_map[sel_type]
                    chinese_mapping = chinese_mappings.get(stmt_key, {})
                    df_t["科目"] = df_t["科目"].apply(
                        lambda x: chinese_mapping.get(x, x)  # 如果有映射就用中文，否则用原值
                    )
                    display_df = df_t
                    display_df.columns = ["科目", "数值(亿元)"]
                # 确保"数值"列为字符串类型，避免 Arrow 序列化错误
                display_df["数值(亿元)"] = display_df["数值(亿元)"].astype(str)
                st.dataframe(display_df, width='stretch', height=420)
        
        # 显示下载按钮
        if excel_bytes:
            filename = f"{company_name}_{start_year}-{end_year}_{'三大报表' if market == 'A股' else '港股三大报表'}.xlsx"
            st.success("下载完成，可保存为Excel。")
            st.download_button("📥 下载Excel文件", data=excel_bytes, file_name=filename,
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        return

    try:
        if market == "A股":
            # 使用现有下载工具
            result_dict = dl_tool.get_financial_statements(symbol, start_year, end_year)
            if not result_dict:
                st.warning("未获取到任何报表数据。")
                return
            company_name = dl_tool.get_symbol_name(symbol)
            excel_bytes = dl_tool.create_excel_file(result_dict, symbol, company_name, start_year, end_year)
            
            # 保存到 session_state
            st.session_state[session_key] = result_dict
            st.session_state[f"{session_key}_excel"] = excel_bytes
            st.session_state[f"{session_key}_company"] = company_name
            
            # 重新运行以显示预览
            st.rerun()
        else:
            # 港股：使用适配层获取三大报表并生成Excel
            data = hk_adapter.get_hk_annual_data(symbol, start_year, end_year)
            if not data or (data.get("profit") is None and data.get("balance_sheet") is None and data.get("cash_flow") is None):
                st.warning("未获取到港股报表数据。")
                return

            def to_yearly(df, date_col="REPORT_DATE"):
                if df is None or df.empty:
                    return {}
                out = {}
                for year in range(start_year, end_year + 1):
                    row = hk_adapter.extract_year_data_hk(df, year, date_col_name=date_col)
                    if row is not None:
                        out[year] = row.to_frame().T
                return out

            profit_years = to_yearly(data.get("profit"))
            balance_years = to_yearly(data.get("balance_sheet"))
            cash_years = to_yearly(data.get("cash_flow"))
            
            # 保存中文名称映射
            chinese_mappings = {
                "balance": data.get("balance_sheet_chinese_mapping", {}),
                "profit": data.get("profit_chinese_mapping", {}),
                "cash_flow": data.get("cash_flow_chinese_mapping", {}),
            }
            
            # 组装为 {year: {balance, profit, cash}}
            results = {}
            for year in range(start_year, end_year + 1):
                year_data = {
                    "balance": balance_years.get(year),
                    "profit": profit_years.get(year),
                    "cash_flow": cash_years.get(year),
                }
                if any(v is not None for v in year_data.values()):
                    results[year] = year_data

            if not results:
                st.warning("未找到指定年份的港股报表数据。")
                return

            # 写入Excel（金额已转换为亿元）
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for year, year_data in results.items():
                    sheet_name = f"{year}年"
                    pos = 0
                    for title, stmt_key, df in [
                        ("资产负债表", "balance", year_data["balance"]),
                        ("利润表", "profit", year_data["profit"]),
                        ("现金流量表", "cash_flow", year_data["cash_flow"])
                    ]:
                        if df is None or df.empty:
                            continue
                        # 行转列：科目 | 数值（亿元）
                        # 排除 REPORT_DATE 列
                        df_to_transpose = df.drop(columns=['REPORT_DATE'], errors='ignore')
                        df_t = df_to_transpose.T.reset_index()
                        df_t.columns = ["科目", "数值"]
                        # 将金额从元转换为亿元（跳过非数值）
                        def convert_to_yi(x):
                            if pd.isna(x) or str(x) == 'nan':
                                return x
                            try:
                                return round(float(x) / 100000000, 2)
                            except (ValueError, TypeError):
                                return x
                        df_t["数值"] = df_t["数值"].apply(convert_to_yi)
                        # 使用中文名称映射替换英文字段名
                        chinese_mapping = chinese_mappings.get(stmt_key, {})
                        df_t["科目"] = df_t["科目"].apply(
                            lambda x: chinese_mapping.get(x, x)  # 如果有映射就用中文，否则用原值
                        )
                        # 写标题
                        ws = writer.book.create_sheet(sheet_name) if sheet_name not in writer.book.sheetnames else writer.book[sheet_name]
                        # 如果是新建的空sheet，openpyxl不会被pandas自动写入；改用 pandas 写数据，标题单元格用 openpyxl
                        df_t.to_excel(writer, sheet_name=sheet_name, startrow=pos, index=False)
                        # 写标题文字（放在数据上方一行）
                        ws = writer.sheets[sheet_name]
                        ws.cell(row=pos + 1, column=1, value=f"【{title}】")
                        pos += len(df_t) + 3  # 标题 + 数据 + 空行
                
                # 在writer关闭前设置列宽自适应
                try:
                    from openpyxl.utils import get_column_letter
                    
                    # 为每个sheet设置列宽
                    for sheet_name in writer.book.sheetnames:
                        ws = writer.book[sheet_name]
                        for col_idx, col in enumerate(ws.iter_cols(min_row=1, max_row=ws.max_row, values_only=False), start=1):
                            max_length = 0
                            column_letter = get_column_letter(col_idx)
                            
                            for cell in col:
                                if cell.value is not None:
                                    try:
                                        cell_value = str(cell.value)
                                        length = 0
                                        for char in cell_value:
                                            if ord(char) > 127:  # 非ASCII字符（包括中文）
                                                length += 2
                                            else:
                                                length += 1
                                        if length > max_length:
                                            max_length = length
                                    except:
                                        pass
                            
                            if max_length > 0:
                                adjusted_width = min(max(max_length + 2, 8), 50)
                                ws.column_dimensions[column_letter].width = adjusted_width
                            else:
                                ws.column_dimensions[column_letter].width = 10
                except Exception as e:
                    # 如果设置列宽失败，不影响返回结果
                    pass

            output.seek(0)
            excel_bytes = output.getvalue()
            
            # 保存到 session_state（包含中文映射）
            st.session_state[session_key] = results
            st.session_state[f"{session_key}_excel"] = excel_bytes
            st.session_state[f"{session_key}_company"] = symbol
            st.session_state[f"{session_key}_chinese_mappings"] = chinese_mappings
            
            # 重新运行以显示预览
            st.rerun()

    except Exception as e:
        st.error(f"下载失败：{e}")
        import traceback
        st.code(traceback.format_exc())

# -----------------------------
# 功能 3：员工数量提取
# -----------------------------
def run_employee_extraction():
    st.header("👥 员工数量提取")
    
    # 文件夹选择功能
    def select_folder():
        """打开文件夹选择对话框"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            root.attributes('-topmost', True)  # 窗口置顶
            folder_path = filedialog.askdirectory(title="选择PDF文件夹")
            root.destroy()
            return folder_path if folder_path else None
        except Exception as e:
            st.warning(f"文件夹选择器不可用: {e}，请手动输入路径")
            return None
    
    # 初始化PDF目录路径
    if 'pdf_dir' not in st.session_state:
        st.session_state['pdf_dir'] = "年报PDF"
    
    # 文件夹选择按钮和输入框
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        # 不使用key参数，直接通过value参数控制，这样选择文件夹后可以立即更新
        pdf_dir = st.text_input(
            "PDF目录路径", 
            value=st.session_state.get('pdf_dir', "年报PDF")
        )
        # 如果输入框的值改变了，更新session_state
        if pdf_dir:
            st.session_state['pdf_dir'] = pdf_dir
    with col2:
        if st.button("📁 选择", use_container_width=True, help="点击选择文件夹", key="select_folder_btn"):
            selected_folder = select_folder()
            if selected_folder:
                # 直接更新session_state，然后rerun，输入框会自动使用新的value
                st.session_state['pdf_dir'] = selected_folder
                st.rerun()  # 刷新页面以更新输入框
    
    run_btn = st.sidebar.button("🚀 开始提取", type="primary", use_container_width=True)
    if not run_btn:
        st.info("选择或输入PDF目录并点击开始提取。")
        return

    try:
        # 使用session_state中的pdf_dir
        actual_pdf_dir = st.session_state.get('pdf_dir', pdf_dir)
        
        # 显示当前使用的路径（用于调试）
        if actual_pdf_dir:
            st.info(f"📂 当前PDF目录: `{actual_pdf_dir}`")
        
        if not actual_pdf_dir:
            st.error("❌ 请选择或输入PDF目录路径")
            return
            
        # 检查目录是否存在
        if not os.path.exists(actual_pdf_dir):
            st.error(f"❌ PDF目录不存在: `{actual_pdf_dir}`")
            st.info("💡 请检查路径是否正确，或使用【📁 选择】按钮重新选择文件夹")
            return
        
        # 检查目录中是否有PDF文件
        pdf_files = [f for f in os.listdir(actual_pdf_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            st.warning(f"⚠️ 目录中没有找到PDF文件: `{actual_pdf_dir}`")
            st.info("💡 请确保目录中包含年报PDF文件")
        else:
            st.success(f"✓ 找到 {len(pdf_files)} 个PDF文件")
        
        results = {}
        if market == "A股":
            # 批量提取（传递股票代码）
            res = emp_a.batch_extract_employee_count_smart(actual_pdf_dir, stock_code=symbol, use_smart=True)
            results = {k: v for k, v in res.items()}
        else:
            # 港股按年份提取
            res = emp_hk.extract_employee_count_by_year_from_pdfs(actual_pdf_dir, symbol, start_year, end_year)
            results = {f"{year}年": count for year, count in res.items()}

        if not results:
            st.warning("未提取到员工数量，请检查PDF目录。")
            return

        # 展示结果
        df = pd.DataFrame(list(results.items()), columns=["年份/文件", "员工数量"])
        st.dataframe(df, width='stretch', height=400)

        # 下载CSV
        output = io.StringIO()
        df.to_csv(output, index=False, encoding="utf-8-sig")
        st.download_button("📥 下载员工数量CSV", data=output.getvalue().encode("utf-8-sig"),
                           file_name=f"{symbol}_员工数量.csv", mime="text/csv")

    except Exception as e:
        st.error(f"提取失败：{e}")
        import traceback
        st.code(traceback.format_exc())

# -----------------------------
# 功能 4：年报PDF下载（A股 + 港股）
# -----------------------------
def run_pdf_download():
    if market == "A股":
        run_pdf_download_a()
    else:
        run_pdf_download_hk()


def run_pdf_download_a():
    """A股年报PDF下载"""
    st.header("📥 年报PDF下载（A股）")
    st.info("从巨潮资讯网下载A股上市公司年度报告PDF")
    
    # 加载下载模块
    try:
        pdf_dl = load_module("pdf_downloader", "core/a_share/annual_report_downloader.py")
    except Exception as e:
        st.error(f"加载下载模块失败：{e}")
        return
    
    # 文件夹选择功能
    def select_save_folder():
        """打开文件夹选择对话框"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder_path = filedialog.askdirectory(title="选择PDF保存目录")
            root.destroy()
            return folder_path if folder_path else None
        except Exception as e:
            st.warning(f"文件夹选择器不可用: {e}，请手动输入路径")
            return None
    
    # 初始化保存路径
    if 'pdf_save_dir' not in st.session_state:
        st.session_state['pdf_save_dir'] = "年报PDF"
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 下载设置")
    
    # 保存路径选择（不使用key参数，通过value直接控制）
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        save_dir = st.text_input(
            "保存目录",
            value=st.session_state.get('pdf_save_dir', "年报PDF")
        )
        # 如果用户手动输入了路径，更新session_state
        if save_dir and save_dir != st.session_state.get('pdf_save_dir'):
            st.session_state['pdf_save_dir'] = save_dir
    with col2:
        if st.button("📁", use_container_width=True, help="选择保存文件夹", key="select_save_folder_btn"):
            selected_folder = select_save_folder()
            if selected_folder:
                st.session_state['pdf_save_dir'] = selected_folder
                st.rerun()
    
    # 下载按钮
    download_btn = st.sidebar.button("🚀 开始下载", type="primary", use_container_width=True, key="download_pdf_btn")
    
    # 显示当前设置
    st.markdown("### 📋 下载设置")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.write(f"**股票代码：** {symbol}")
        st.write(f"**年份范围：** {start_year} - {end_year}")
    with col_info2:
        actual_save_dir = st.session_state.get('pdf_save_dir', save_dir)
        st.write(f"**保存目录：** `{actual_save_dir}`")
        # 检查目录
        if os.path.exists(actual_save_dir):
            existing_pdfs = [f for f in os.listdir(actual_save_dir) if f.lower().endswith('.pdf')]
            st.write(f"**已有文件：** {len(existing_pdfs)} 个PDF")
        else:
            st.write("**目录状态：** 将自动创建")
    
    if not download_btn:
        st.markdown("---")
        st.markdown("""
        ### 📖 使用说明
        1. 在左侧输入 **股票代码**（6位数字，如 600900）
        2. 设置 **起始年份** 和 **结束年份**
        3. 选择或输入 **PDF保存目录**
        4. 点击 **开始下载** 按钮
        
        ### ⚠️ 注意事项
        - 年报PDF通常在次年3-4月发布（如2023年年报在2024年4月前发布）
        - 下载需要网络连接，请确保网络通畅
        - 单个年报PDF文件较大（几MB到几十MB），请耐心等待
        """)
        return
    
    # 执行下载
    st.markdown("---")
    st.markdown("### 📥 下载进度")
    
    actual_save_dir = st.session_state.get('pdf_save_dir', save_dir)
    
    # 创建保存目录
    os.makedirs(actual_save_dir, exist_ok=True)
    
    # 下载结果统计
    results = {
        'success': [],
        'failed': []
    }
    
    # 进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_container = st.container()
    
    years = list(range(int(start_year), int(end_year) + 1))
    total_years = len(years)
    
    for idx, year in enumerate(years):
        status_text.text(f"正在下载 {year} 年年报... ({idx + 1}/{total_years})")
        
        with log_container:
            st.write(f"**[{year}年]** 搜索中...")
        
        try:
            # 调用下载函数
            filepath = pdf_dl.download_annual_report(symbol, year, actual_save_dir)
            
            if filepath and os.path.exists(filepath):
                file_size = os.path.getsize(filepath) / 1024 / 1024  # MB
                results['success'].append({
                    'year': year,
                    'path': filepath,
                    'size': f"{file_size:.2f} MB"
                })
                with log_container:
                    st.success(f"[OK] {year}年年报下载成功：{os.path.basename(filepath)} ({file_size:.2f} MB)")
            else:
                results['failed'].append({
                    'year': year,
                    'reason': '未找到年报或下载失败'
                })
                with log_container:
                    st.warning(f"[!] {year}年年报下载失败")
        except Exception as e:
            results['failed'].append({
                'year': year,
                'reason': str(e)
            })
            with log_container:
                st.error(f"[X] {year}年年报下载出错：{e}")
        
        # 更新进度
        progress_bar.progress((idx + 1) / total_years)
    
    # 显示下载结果汇总
    st.markdown("---")
    st.markdown("### 📊 下载结果")
    
    col_success, col_failed = st.columns(2)
    
    with col_success:
        st.metric("下载成功", f"{len(results['success'])} 个")
        if results['success']:
            for item in results['success']:
                st.write(f"- {item['year']}年：{item['size']}")
    
    with col_failed:
        st.metric("下载失败", f"{len(results['failed'])} 个")
        if results['failed']:
            for item in results['failed']:
                st.write(f"- {item['year']}年：{item['reason']}")
    
    # 打开保存目录按钮
    if results['success']:
        st.success(f"下载完成！文件保存在：`{actual_save_dir}`")


def run_pdf_download_hk():
    """港股年报PDF下载（从HTML文件解析）"""
    st.header("📥 年报PDF下载（港股）")
    st.info("从港交所披露易下载港股年度报告PDF（需先保存搜索结果HTML）")
    
    # 加载港股下载模块
    try:
        hk_pdf_dl = load_module("hk_pdf_downloader", "core/hk/annual_report_downloader.py")
    except Exception as e:
        st.error(f"加载港股下载模块失败：{e}")
        return
    
    # 文件选择功能
    def select_html_file():
        """打开文件选择对话框选择HTML文件"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="选择港交所搜索结果HTML文件",
                filetypes=[("HTML文件", "*.html;*.htm"), ("所有文件", "*.*")]
            )
            root.destroy()
            return file_path if file_path else None
        except Exception as e:
            st.warning(f"文件选择器不可用: {e}，请手动输入路径")
            return None
    
    def select_save_folder():
        """打开文件夹选择对话框"""
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            folder_path = filedialog.askdirectory(title="选择PDF保存目录")
            root.destroy()
            return folder_path if folder_path else None
        except Exception as e:
            st.warning(f"文件夹选择器不可用: {e}，请手动输入路径")
            return None
    
    # 初始化路径
    if 'hk_html_path' not in st.session_state:
        st.session_state['hk_html_path'] = ""
    if 'hk_pdf_save_dir' not in st.session_state:
        st.session_state['hk_pdf_save_dir'] = "港股年报PDF"
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📁 下载设置")
    
    # HTML文件选择
    st.sidebar.markdown("**步骤1: 选择HTML文件**")
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        html_path = st.text_input(
            "HTML文件路径",
            value=st.session_state.get('hk_html_path', ""),
            placeholder="从港交所保存的搜索结果HTML"
        )
        # 如果用户手动输入了路径，更新session_state
        if html_path and html_path != st.session_state.get('hk_html_path'):
            st.session_state['hk_html_path'] = html_path
    with col2:
        if st.button("📄", use_container_width=True, help="选择HTML文件", key="select_html_btn"):
            selected_file = select_html_file()
            if selected_file:
                st.session_state['hk_html_path'] = selected_file
                st.rerun()
    
    # PDF保存目录选择
    st.sidebar.markdown("**步骤2: 选择保存目录**")
    col3, col4 = st.sidebar.columns([3, 1])
    with col3:
        save_dir = st.text_input(
            "保存目录",
            value=st.session_state.get('hk_pdf_save_dir', "港股年报PDF")
        )
        # 如果用户手动输入了路径，更新session_state
        if save_dir and save_dir != st.session_state.get('hk_pdf_save_dir'):
            st.session_state['hk_pdf_save_dir'] = save_dir
    with col4:
        if st.button("📁", use_container_width=True, help="选择保存文件夹", key="select_hk_save_folder_btn"):
            selected_folder = select_save_folder()
            if selected_folder:
                st.session_state['hk_pdf_save_dir'] = selected_folder
                st.rerun()
    
    # 下载按钮
    download_btn = st.sidebar.button("🚀 开始下载", type="primary", use_container_width=True, key="download_hk_pdf_btn")
    
    # 显示当前设置
    st.markdown("### 📋 下载设置")
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.write(f"**股票代码：** {symbol}")
        st.write(f"**年份范围：** {start_year} - {end_year}")
    with col_info2:
        actual_html_path = st.session_state.get('hk_html_path', '')
        actual_save_dir = st.session_state.get('hk_pdf_save_dir', save_dir)
        if actual_html_path:
            st.write(f"**HTML文件：** `{os.path.basename(actual_html_path)}`")
        else:
            st.write("**HTML文件：** 未选择")
        st.write(f"**保存目录：** `{actual_save_dir}`")
    
    # 如果没有点击下载按钮，显示使用说明
    if not download_btn:
        st.markdown("---")
        st.markdown("""
        ### 📖 使用说明
        
        **港股年报下载需要先从港交所网站保存搜索结果页面：**
        
        1. 打开港交所披露易搜索页面：[https://www1.hkexnews.hk/search/titlesearch.xhtml](https://www1.hkexnews.hk/search/titlesearch.xhtml)
        2. 输入股票代码（如 01810），选择 **"年度报告"** 文件类别
        3. 点击搜索，等待结果显示
        4. **Ctrl+S** 保存网页为HTML文件（完整网页格式）
        5. 回到本工具，选择刚保存的HTML文件
        6. 设置PDF保存目录
        7. 点击 **开始下载**
        
        ### ⚠️ 注意事项
        - 保存HTML时请选择 **"网页，完整"** 或 **"网页，仅HTML"** 格式
        - 年份范围会用于筛选要下载的年报
        - 下载速度取决于网络状况
        """)
        
        # 显示解析预览（如果已选择HTML文件）
        if actual_html_path and os.path.exists(actual_html_path):
            st.markdown("---")
            st.markdown("### 🔍 HTML文件预览")
            try:
                reports = hk_pdf_dl.parse_html_for_annual_reports(actual_html_path)
                if reports:
                    # 筛选年份范围
                    filtered_reports = [r for r in reports if start_year <= r['year'] <= end_year]
                    st.success(f"解析成功！找到 {len(reports)} 个年报，符合年份范围的有 {len(filtered_reports)} 个")
                    
                    # 显示列表
                    preview_data = []
                    for r in reports:
                        in_range = "✓" if start_year <= r['year'] <= end_year else ""
                        preview_data.append({
                            "选中": in_range,
                            "年份": r['year'],
                            "标题": r['title'][:40],
                        })
                    st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
                else:
                    st.warning("未在HTML文件中找到年报链接，请检查文件是否正确")
            except Exception as e:
                st.error(f"解析HTML失败：{e}")
        return
    
    # 执行下载
    actual_html_path = st.session_state.get('hk_html_path', '')
    actual_save_dir = st.session_state.get('hk_pdf_save_dir', save_dir)
    
    # 检查HTML文件
    if not actual_html_path:
        st.error("请先选择HTML文件！")
        return
    if not os.path.exists(actual_html_path):
        st.error(f"HTML文件不存在：{actual_html_path}")
        return
    
    # 创建保存目录
    os.makedirs(actual_save_dir, exist_ok=True)
    
    st.markdown("---")
    st.markdown("### 📥 下载进度")
    
    # 解析HTML获取年报列表
    status_text = st.empty()
    status_text.text("正在解析HTML文件...")
    
    try:
        reports = hk_pdf_dl.parse_html_for_annual_reports(actual_html_path)
        if not reports:
            st.error("未在HTML文件中找到年报链接")
            return
        
        # 筛选年份范围
        years_to_download = list(range(int(start_year), int(end_year) + 1))
        filtered_reports = [r for r in reports if r['year'] in years_to_download]
        
        if not filtered_reports:
            st.warning(f"没有找到 {start_year}-{end_year} 年份范围内的年报")
            st.info(f"HTML文件中包含的年份：{sorted([r['year'] for r in reports])}")
            return
        
        st.info(f"准备下载 {len(filtered_reports)} 个年报")
        
        # 下载结果统计
        results = {'success': [], 'failed': []}
        
        # 进度条
        progress_bar = st.progress(0)
        log_container = st.container()
        
        total = len(filtered_reports)
        for idx, report in enumerate(filtered_reports):
            year = report['year']
            pdf_url = report['pdf_url']
            title = report['title']
            
            status_text.text(f"正在下载 {year} 年年报... ({idx + 1}/{total})")
            
            with log_container:
                st.write(f"**[{year}年]** {title[:30]}...")
            
            try:
                # 生成文件名
                symbol_clean = symbol.zfill(5)
                filename = f"{symbol_clean}_{year}年年度报告.pdf"
                save_path = os.path.join(actual_save_dir, filename)
                
                # 下载PDF
                success = hk_pdf_dl.download_pdf_from_url(pdf_url, save_path)
                
                if success and os.path.exists(save_path):
                    file_size = os.path.getsize(save_path) / 1024 / 1024
                    results['success'].append({
                        'year': year,
                        'path': save_path,
                        'size': f"{file_size:.2f} MB"
                    })
                    with log_container:
                        st.success(f"[OK] {year}年年报下载成功 ({file_size:.2f} MB)")
                else:
                    results['failed'].append({
                        'year': year,
                        'reason': '下载失败'
                    })
                    with log_container:
                        st.warning(f"[!] {year}年年报下载失败")
            except Exception as e:
                results['failed'].append({
                    'year': year,
                    'reason': str(e)
                })
                with log_container:
                    st.error(f"[X] {year}年年报下载出错：{e}")
            
            # 更新进度
            progress_bar.progress((idx + 1) / total)
        
        # 显示下载结果汇总
        st.markdown("---")
        st.markdown("### 📊 下载结果")
        
        col_success, col_failed = st.columns(2)
        
        with col_success:
            st.metric("下载成功", f"{len(results['success'])} 个")
            if results['success']:
                for item in results['success']:
                    st.write(f"- {item['year']}年：{item['size']}")
        
        with col_failed:
            st.metric("下载失败", f"{len(results['failed'])} 个")
            if results['failed']:
                for item in results['failed']:
                    st.write(f"- {item['year']}年：{item['reason']}")
        
        if results['success']:
            st.success(f"下载完成！文件保存在：`{actual_save_dir}`")
    
    except Exception as e:
        st.error(f"下载失败：{e}")
        import traceback
        st.code(traceback.format_exc())


# -----------------------------
# 主路由
# -----------------------------
st.title("📊 统一财务工具（A股 + 港股）")
st.caption("财务分析｜报表下载｜员工数量提取｜年报下载 —— 一站式界面")
st.markdown("---")

if feature == "📊 财务分析":
    run_financial_analysis()
elif feature == "📄 报表下载":
    run_report_download()
elif feature == "👥 员工数量提取":
    run_employee_extraction()
elif feature == "📥 年报PDF下载":
    run_pdf_download()
else:
    st.info("请选择左侧的功能开始。")

