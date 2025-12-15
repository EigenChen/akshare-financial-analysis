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
from datetime import datetime
from typing import Dict, Optional

import pandas as pd
import streamlit as st

# -----------------------------
# 工具：动态导入模块
# -----------------------------
def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# 预加载核心模块
fa_a = load_module("financial_analysis_a", "07_财务分析.py")
fa_hk = load_module("financial_analysis_hk", "hk_financial_analysis_full.py")
hk_adapter = load_module("hk_adapter", "hk_financial_adapter.py")
dl_tool = load_module("report_downloader", "财务报表下载工具.py")
emp_a = load_module("emp_a", "测试_从年报提取员工数量.py")
emp_hk = load_module("emp_hk", "港股_从年报提取员工数量.py")

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
feature = st.sidebar.radio("选择功能", ["📊 财务分析", "📄 报表下载", "👥 员工数量提取"])

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
    if not run_btn:
        st.info("在左侧选择模块并点击开始分析。")
        return

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
                csv_bytes = employee_csv.getvalue()
                csv_path = f"/tmp/{employee_csv.name}"
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

        sheet = st.selectbox("选择要查看的Sheet", list(results.keys()))
        st.dataframe(results[sheet], width='stretch', height=420)

        # 下载最新生成的Excel
        filename = f"{company_name}_{start_year}-{end_year}_{'财务分析' if market=='A股' else '港股财务分析'}_{timestamp}.xlsx"
        filepath = os.path.join("output", filename)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                st.download_button("📥 下载Excel文件", data=f.read(), file_name=filename,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.info("Excel 文件尚未生成或路径不存在。")

    except Exception as e:
        st.error(f"分析失败：{e}")
        import traceback
        st.code(traceback.format_exc())

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
    pdf_dir = st.sidebar.text_input("PDF目录路径", value="年报PDF")
    run_btn = st.sidebar.button("🚀 开始提取", type="primary", use_container_width=True)
    if not run_btn:
        st.info("输入PDF目录并点击开始提取。")
        return

    try:
        results = {}
        if market == "A股":
            # 批量提取
            res = emp_a.batch_extract_employee_count_from_pdfs(pdf_dir, output_csv=None)
            results = {k: v for k, v in res.items()}
        else:
            # 港股按年份提取
            res = emp_hk.extract_employee_count_by_year_from_pdfs(pdf_dir, symbol, start_year, end_year)
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
# 主路由
# -----------------------------
st.title("📊 统一财务工具（A股 + 港股）")
st.caption("财务分析｜报表下载｜员工数量提取 —— 一站式界面")
st.markdown("---")

if feature == "📊 财务分析":
    run_financial_analysis()
elif feature == "📄 报表下载":
    run_report_download()
elif feature == "👥 员工数量提取":
    run_employee_extraction()
else:
    st.info("请选择左侧的功能开始。")

