"""
港股财务分析工具 - Streamlit Web 界面

功能：
1. 港股代码输入和公司信息查询
2. 年份范围选择
3. 一键生成完整的财务分析报告（9个sheet）
4. 结果可视化展示（表格和图表）
5. Excel 文件下载

注意：港股数据单位为港币（HKD），不进行货币转换
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import io
import re
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 动态导入港股财务分析模块
spec = importlib.util.spec_from_file_location("hk_financial_analysis", ROOT / "core/hk/financial_analysis_full.py")
hk_financial_analysis = importlib.util.module_from_spec(spec)
sys.modules["hk_financial_analysis"] = hk_financial_analysis
spec.loader.exec_module(hk_financial_analysis)

# 导入港股适配层
from core.hk.financial_adapter import (
    is_hk_stock, get_hk_symbol_name, get_hk_annual_data,
    extract_year_data_hk, get_value_from_row_hk
)

# 导入A股计算函数（字段名已统一，可以直接复用）
spec_a = importlib.util.spec_from_file_location("financial_analysis", ROOT / "core/a_share/financial_analysis.py")
financial_analysis = importlib.util.module_from_spec(spec_a)
sys.modules["financial_analysis"] = financial_analysis
spec_a.loader.exec_module(financial_analysis)

# 导入A股的计算函数
calculate_revenue_metrics = financial_analysis.calculate_revenue_metrics
calculate_expense_metrics = financial_analysis.calculate_expense_metrics
calculate_growth_metrics = financial_analysis.calculate_growth_metrics
calculate_balance_sheet_metrics = financial_analysis.calculate_balance_sheet_metrics
calculate_wc_metrics = financial_analysis.calculate_wc_metrics
calculate_fixed_asset_metrics = financial_analysis.calculate_fixed_asset_metrics
calculate_roi_metrics = financial_analysis.calculate_roi_metrics
calculate_asset_turnover_metrics = financial_analysis.calculate_asset_turnover_metrics
calculate_per_capita_metrics = financial_analysis.calculate_per_capita_metrics
save_to_excel = financial_analysis.save_to_excel

# 替换数据获取函数为港股版本
financial_analysis.get_annual_data = get_hk_annual_data
financial_analysis.extract_year_data = extract_year_data_hk
financial_analysis.get_value_from_row = get_value_from_row_hk

# 辅助函数：获取公式说明
def get_formula_notes(sheet_name):
    """
    获取指定sheet的公式说明
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

# 辅助函数：从Excel文件名解析信息
def parse_excel_filename(filename):
    """
    从Excel文件名解析股票代码、公司名称、年份范围
    
    格式：公司名称_起始年-结束年_港股财务分析_时间戳.xlsx
    例如：腾讯控股_2020-2024_港股财务分析_20251215112834.xlsx
    
    返回: (company_name, start_year, end_year, symbol) 或 None
    """
    if not filename or not filename.endswith('.xlsx'):
        return None
    
    basename = filename.replace('.xlsx', '')
    
    # 匹配格式：公司名_起始年-结束年_港股财务分析_时间戳
    pattern = r'(.+?)_(\d{4})-(\d{4})_港股财务分析_\d+'
    match = re.match(pattern, basename)
    
    if match:
        company_name = match.group(1)
        start_year = int(match.group(2))
        end_year = int(match.group(3))
        return (company_name, start_year, end_year, None)
    
    return None

# 辅助函数：加载Excel文件
def load_excel_file(file_input):
    """
    加载Excel文件，返回所有sheet的字典
    """
    try:
        if hasattr(file_input, 'read'):
            excel_file = pd.ExcelFile(io.BytesIO(file_input.read()))
        else:
            excel_file = pd.ExcelFile(file_input)
        
        sheets = {}
        for sheet_name in excel_file.sheet_names:
            sheets[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name)
        return sheets
    except Exception as e:
        st.error(f"加载Excel文件失败：{str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

# 辅助函数：判断指标类型（金额或百分比）
def is_percentage_indicator(indicator_name):
    """
    判断指标是否为百分比类型
    """
    percentage_keywords = ['率', '%', '比率', '占比', '比例', '增长率', '复合增长率']
    return any(keyword in indicator_name for keyword in percentage_keywords)

# 辅助函数：准备图表数据
def prepare_chart_data(df, selected_indicators, start_year, end_year):
    """
    准备图表数据，将DataFrame转换为适合绘制折线图的格式
    """
    year_cols = [str(year) for year in range(start_year, end_year + 1)]
    
    selected_df = df[df['科目'].isin(selected_indicators)].copy()
    
    if selected_df.empty:
        return None, None
    
    amount_data = []
    percentage_data = []
    
    for _, row in selected_df.iterrows():
        indicator = row['科目']
        is_percentage = is_percentage_indicator(indicator)
        
        for year_col in year_cols:
            if year_col in row.index:
                value = row[year_col]
                if value == '-' or pd.isna(value) or value == '':
                    continue
                
                try:
                    if isinstance(value, str):
                        value = value.replace(',', '').replace('，', '')
                    num_value = float(value)
                    
                    if num_value == 0:
                        continue
                    
                    year = int(year_col)
                    
                    data_point = {
                        '年份': year,
                        '指标': indicator,
                        '数值': num_value
                    }
                    
                    if is_percentage:
                        percentage_data.append(data_point)
                    else:
                        amount_data.append(data_point)
                except (ValueError, TypeError):
                    continue
    
    amount_df = pd.DataFrame(amount_data) if amount_data else None
    percentage_df = pd.DataFrame(percentage_data) if percentage_data else None
    
    return amount_df, percentage_df

# 辅助函数：创建双Y轴折线图
def create_dual_axis_line_chart(amount_df, percentage_df, title="趋势图"):
    """
    创建双Y轴折线图
    """
    fig = go.Figure()
    
    amount_colors = px.colors.qualitative.Set1
    percentage_colors = px.colors.qualitative.Set2
    
    # 添加金额数据（左Y轴）- 使用实线
    if amount_df is not None and not amount_df.empty:
        amount_indicators = amount_df['指标'].unique()
        for idx, indicator in enumerate(amount_indicators):
            indicator_data = amount_df[amount_df['指标'] == indicator].sort_values('年份')
            color = amount_colors[idx % len(amount_colors)]
            fig.add_trace(go.Scatter(
                x=indicator_data['年份'],
                y=indicator_data['数值'],
                name=f"{indicator} (金额)",
                mode='lines+markers',
                yaxis='y',
                line=dict(width=2.5, color=color),
                marker=dict(size=7, color=color),
                hovertemplate='<b>%{fullData.name}</b><br>年份: %{x}<br>数值: %{y:.2f}<extra></extra>'
            ))
    
    # 添加百分比数据（右Y轴）- 使用虚线
    if percentage_df is not None and not percentage_df.empty:
        percentage_indicators = percentage_df['指标'].unique()
        for idx, indicator in enumerate(percentage_indicators):
            indicator_data = percentage_df[percentage_df['指标'] == indicator].sort_values('年份')
            color = percentage_colors[idx % len(percentage_colors)]
            fig.add_trace(go.Scatter(
                x=indicator_data['年份'],
                y=indicator_data['数值'],
                name=f"{indicator} (%)",
                mode='lines+markers',
                yaxis='y2',
                line=dict(width=2.5, dash='dash', color=color),
                marker=dict(size=7, symbol='diamond', color=color),
                hovertemplate='<b>%{fullData.name}</b><br>年份: %{x}<br>数值: %{y:.2f}%<extra></extra>'
            ))
    
    # 配置布局
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis=dict(
            title="年份",
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        yaxis=dict(
            title="金额（亿元，港币）",
            side='left',
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)'
        ),
        yaxis2=dict(
            title="百分比（%）",
            side='right',
            overlaying='y',
            showgrid=False
        ),
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        height=500,
        margin=dict(l=60, r=100, t=60, b=60)
    )
    
    return fig

# 页面配置
st.set_page_config(
    page_title="港股财务分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题和说明
st.title("📊 港股财务分析工具")
st.markdown("""
<div style='background-color: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px;'>
    <h4 style='color: #1f77b4; margin-top: 0;'>💡 使用说明</h4>
    <ul style='margin-bottom: 0;'>
        <li>支持港股代码（5位数字，如：00700 腾讯控股）</li>
        <li>可生成完整的9个财务分析sheet</li>
        <li>数据单位为<strong>港币（HKD）</strong>，不进行货币转换</li>
        <li>支持结果可视化展示和Excel文件下载</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# 侧边栏 - 参数设置
with st.sidebar:
    st.header("⚙️ 分析参数设置")
    
    # 模式选择：新建分析 或 加载已有结果
    analysis_mode = st.radio(
        "分析模式",
        ["🆕 新建分析", "📂 加载已有结果"],
        help="选择新建分析或加载之前生成的结果文件",
        key="analysis_mode"
    )
    
    # 如果切换了模式，清除之前的状态
    if 'last_analysis_mode' in st.session_state:
        if st.session_state['last_analysis_mode'] != analysis_mode:
            if analysis_mode == "🆕 新建分析":
                if 'loaded_excel_data' in st.session_state:
                    del st.session_state['loaded_excel_data']
                    del st.session_state['loaded_file_info']
                    del st.session_state['loaded_file_name']
                    del st.session_state['loaded_file_content']
            else:
                if 'analysis_results' in st.session_state:
                    del st.session_state['analysis_results']
    
    st.session_state['last_analysis_mode'] = analysis_mode
    
    st.divider()
    
    # 如果选择加载已有结果
    file_info = None
    if analysis_mode == "📂 加载已有结果":
        result_file = st.file_uploader(
            "上传Excel文件",
            type=['xlsx'],
            help="请上传之前生成的港股财务分析Excel文件"
        )
        
        if result_file:
            file_info = parse_excel_filename(result_file.name)
            if file_info:
                company_name, start_year, end_year, _ = file_info
                st.success(f"✅ 文件信息：\n- 公司：{company_name}\n- 年份：{start_year}-{end_year}")
            else:
                st.warning("⚠️ 文件名格式不正确，无法解析信息")
                start_year = None
                end_year = None
        else:
            start_year = None
            end_year = None
            st.info("💡 请上传Excel文件")
    else:
        result_file = None
        # 新建分析模式
        # 港股代码输入
        symbol = st.text_input(
            "港股代码",
            value="00700",
            help="请输入5位港股代码，如：00700（腾讯控股）、03690（美团）、09988（阿里巴巴-SW）",
            placeholder="例如：00700"
        )
        
        # 验证港股代码格式
        if symbol:
            symbol_clean = symbol.replace('.HK', '').strip()
            if not is_hk_stock(symbol_clean):
                st.warning("⚠️ 请输入有效的港股代码（5位数字）")
            else:
                # 尝试获取公司名称
                try:
                    company_name = get_hk_symbol_name(symbol_clean)
                    if company_name:
                        st.info(f"📌 公司名称：{company_name}")
                except:
                    pass
        
        # 年份范围选择
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                "起始年份",
                min_value=2000,
                max_value=2030,
                value=2020,
                step=1,
                key="start_year_input"
            )
        with col2:
            end_year = st.number_input(
                "结束年份",
                min_value=2000,
                max_value=2030,
                value=2024,
                step=1,
                key="end_year_input"
            )
        
        # 验证年份范围
        if start_year > end_year:
            st.error("⚠️ 起始年份不能大于结束年份！")
            st.stop()
    
    st.divider()
    
    # 分析选项（仅在新建分析模式下显示）
    if analysis_mode == "🆕 新建分析":
        st.subheader("📋 分析模块")
        analyze_revenue = st.checkbox("营收基本数据", value=True)
        analyze_expense = st.checkbox("费用构成", value=True)
        analyze_growth = st.checkbox("增长率", value=True)
        analyze_balance = st.checkbox("资产负债", value=True)
        analyze_wc = st.checkbox("WC分析", value=True)
        analyze_fixed_asset = st.checkbox("固定资产投入分析", value=True)
        analyze_roi = st.checkbox("收益率和杜邦分析", value=True)
        analyze_asset_turnover = st.checkbox("资产周转", value=True)
        analyze_per_capita = st.checkbox("人均数据", value=True)
    else:
        # 加载模式下所有模块都会加载
        analyze_revenue = True
        analyze_expense = True
        analyze_growth = True
        analyze_balance = True
        analyze_wc = True
        analyze_fixed_asset = True
        analyze_roi = True
        analyze_asset_turnover = True
        analyze_per_capita = True
    
    st.divider()
    
    # 开始分析/加载按钮
    load_button = False
    analyze_button = False
    
    if analysis_mode == "📂 加载已有结果":
        if result_file and file_info:
            load_button = st.button(
                "📂 加载结果文件",
                type="primary",
                use_container_width=True
            )
            if load_button:
                st.session_state['loaded_excel_data'] = load_excel_file(result_file)
                st.session_state['loaded_file_info'] = file_info
                st.session_state['loaded_file_name'] = result_file.name
                st.session_state['loaded_file_content'] = result_file.getvalue()
    else:
        analyze_button = st.button(
            "🚀 开始分析",
            type="primary",
            use_container_width=True
        )
        if analyze_button:
            if 'loaded_excel_data' in st.session_state:
                del st.session_state['loaded_excel_data']
                del st.session_state['loaded_file_info']
                del st.session_state['loaded_file_name']
                del st.session_state['loaded_file_content']

# 主内容区 - 加载已有结果
if analysis_mode == "📂 加载已有结果" and 'loaded_excel_data' in st.session_state:
    loaded_data = st.session_state['loaded_excel_data']
    file_info = st.session_state['loaded_file_info']
    file_name = st.session_state['loaded_file_name']
    
    if loaded_data and file_info:
        company_name, start_year, end_year, _ = file_info
        
        st.header(f"📊 {company_name} 财务分析结果（{start_year}-{end_year}）")
        st.caption(f"📁 文件：{file_name} | 💰 货币单位：港币（HKD）")
        
        # 显示所有sheet
        sheet_names = list(loaded_data.keys())
        selected_sheet = st.selectbox("选择要查看的Sheet", sheet_names)
        
        if selected_sheet:
            df = loaded_data[selected_sheet]
            st.subheader(f"📋 {selected_sheet}")
            
            # 显示数据表 - 将DataFrame转换为字符串类型以避免PyArrow类型转换问题
            display_df = df.astype(str)
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # 显示公式说明
            formula_notes = get_formula_notes(selected_sheet)
            if formula_notes:
                with st.expander("📝 公式说明"):
                    for indicator, formula in formula_notes.items():
                        st.markdown(f"**{indicator}**：{formula}")
            
            # 图表展示
            if len(df) > 0 and '科目' in df.columns:
                st.subheader("📈 趋势图")
                indicators = df['科目'].tolist()
                selected_indicators = st.multiselect(
                    "选择要显示的指标",
                    indicators,
                    default=indicators[:min(5, len(indicators))],
                    key=f"indicators_{selected_sheet}"
                )
                
                if selected_indicators:
                    amount_df, percentage_df = prepare_chart_data(df, selected_indicators, start_year, end_year)
                    if amount_df is not None or percentage_df is not None:
                        chart = create_dual_axis_line_chart(amount_df, percentage_df, f"{selected_sheet} - 趋势图")
                        st.plotly_chart(chart, use_container_width=True)
        
        # 下载按钮
        st.divider()
        if 'loaded_file_content' in st.session_state:
            st.download_button(
                label="📥 下载Excel文件",
                data=st.session_state['loaded_file_content'],
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# 主内容区 - 新建分析
elif analysis_mode == "🆕 新建分析" and analyze_button:
    if not symbol or not is_hk_stock(symbol.replace('.HK', '').strip()):
        st.error("❌ 请输入有效的港股代码（5位数字）")
        st.stop()
    
    symbol_clean = symbol.replace('.HK', '').strip()
    
    # 获取公司名称
    try:
        company_name = get_hk_symbol_name(symbol_clean)
        if not company_name:
            company_name = f"股票{symbol_clean}"
    except:
        company_name = f"股票{symbol_clean}"
    
    st.header(f"📊 {company_name} 财务分析（{start_year}-{end_year}）")
    st.caption(f"💰 货币单位：港币（HKD）")
    
    # 进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 存储分析结果
    analysis_results = {}
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    total_modules = sum([
        analyze_revenue, analyze_expense, analyze_growth, analyze_balance,
        analyze_wc, analyze_fixed_asset, analyze_roi, analyze_asset_turnover, analyze_per_capita
    ])
    current_module = 0
    
    # 计算各个模块
    try:
        if analyze_revenue:
            current_module += 1
            status_text.text(f"📊 正在计算营收基本数据... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            result_df = calculate_revenue_metrics(symbol_clean, start_year, end_year)
            if result_df is not None and not result_df.empty:
                analysis_results['营收基本数据'] = result_df
                save_to_excel(result_df, symbol_clean, company_name, start_year, end_year, '营收基本数据', timestamp=timestamp)
        
        if analyze_expense:
            current_module += 1
            status_text.text(f"💰 正在计算费用构成... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            expense_df = calculate_expense_metrics(symbol_clean, start_year, end_year)
            if expense_df is not None and not expense_df.empty:
                analysis_results['费用构成'] = expense_df
                save_to_excel(expense_df, symbol_clean, company_name, start_year, end_year, '费用构成', timestamp=timestamp)
        
        if analyze_growth:
            current_module += 1
            status_text.text(f"📈 正在计算增长率... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            growth_df = calculate_growth_metrics(symbol_clean, start_year, end_year)
            if growth_df is not None and not growth_df.empty:
                analysis_results['增长'] = growth_df
                save_to_excel(growth_df, symbol_clean, company_name, start_year, end_year, '增长', timestamp=timestamp)
        
        if analyze_balance:
            current_module += 1
            status_text.text(f"💼 正在计算资产负债... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            balance_df = calculate_balance_sheet_metrics(symbol_clean, start_year, end_year)
            if balance_df is not None and not balance_df.empty:
                analysis_results['资产负债'] = balance_df
                save_to_excel(balance_df, symbol_clean, company_name, start_year, end_year, '资产负债', timestamp=timestamp)
        
        if analyze_wc:
            current_module += 1
            status_text.text(f"💵 正在计算WC分析... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            wc_df = calculate_wc_metrics(symbol_clean, start_year, end_year)
            if wc_df is not None and not wc_df.empty:
                analysis_results['WC分析'] = wc_df
                save_to_excel(wc_df, symbol_clean, company_name, start_year, end_year, 'WC分析', timestamp=timestamp)
        
        if analyze_fixed_asset:
            current_module += 1
            status_text.text(f"🏗️ 正在计算固定资产投入分析... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            fixed_asset_df = calculate_fixed_asset_metrics(symbol_clean, start_year, end_year)
            if fixed_asset_df is not None and not fixed_asset_df.empty:
                analysis_results['固定资产投入分析'] = fixed_asset_df
                save_to_excel(fixed_asset_df, symbol_clean, company_name, start_year, end_year, '固定资产投入分析', timestamp=timestamp)
        
        if analyze_roi:
            current_module += 1
            status_text.text(f"📊 正在计算收益率和杜邦分析... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            roi_df = calculate_roi_metrics(symbol_clean, start_year, end_year)
            if roi_df is not None and not roi_df.empty:
                analysis_results['收益率和杜邦分析'] = roi_df
                save_to_excel(roi_df, symbol_clean, company_name, start_year, end_year, '收益率和杜邦分析', timestamp=timestamp)
        
        if analyze_asset_turnover:
            current_module += 1
            status_text.text(f"🔄 正在计算资产周转... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            asset_turnover_df = calculate_asset_turnover_metrics(symbol_clean, start_year, end_year)
            if asset_turnover_df is not None and not asset_turnover_df.empty:
                analysis_results['资产周转'] = asset_turnover_df
                save_to_excel(asset_turnover_df, symbol_clean, company_name, start_year, end_year, '资产周转', timestamp=timestamp)
        
        if analyze_per_capita:
            current_module += 1
            status_text.text(f"👥 正在计算人均数据... ({current_module}/{total_modules})")
            progress_bar.progress(current_module / total_modules)
            per_capita_df = calculate_per_capita_metrics(symbol_clean, start_year, end_year, employee_csv_path=None)
            if per_capita_df is not None and not per_capita_df.empty:
                analysis_results['人均数据'] = per_capita_df
                save_to_excel(per_capita_df, symbol_clean, company_name, start_year, end_year, '人均数据', timestamp=timestamp)
        
        progress_bar.progress(1.0)
        status_text.text("✅ 分析完成！")
        
        # 保存到session_state
        st.session_state['analysis_results'] = analysis_results
        st.session_state['analysis_symbol'] = symbol_clean
        st.session_state['analysis_company'] = company_name
        st.session_state['analysis_start_year'] = start_year
        st.session_state['analysis_end_year'] = end_year
        st.session_state['analysis_timestamp'] = timestamp
        
        st.success(f"✅ 分析完成！共生成 {len(analysis_results)} 个sheet")
        
    except Exception as e:
        st.error(f"❌ 分析过程中出现错误：{str(e)}")
        import traceback
        with st.expander("查看错误详情"):
            st.code(traceback.format_exc())
        st.stop()

# 显示分析结果
if 'analysis_results' in st.session_state:
    analysis_results = st.session_state['analysis_results']
    company_name = st.session_state.get('analysis_company', '未知')
    start_year = st.session_state.get('analysis_start_year', 2020)
    end_year = st.session_state.get('analysis_end_year', 2024)
    
    st.header(f"📊 {company_name} 财务分析结果（{start_year}-{end_year}）")
    st.caption(f"💰 货币单位：港币（HKD）")
    
    # 显示所有sheet
    sheet_names = list(analysis_results.keys())
    selected_sheet = st.selectbox("选择要查看的Sheet", sheet_names, key="result_sheet_selector")
    
    if selected_sheet:
        df = analysis_results[selected_sheet]
        st.subheader(f"📋 {selected_sheet}")
        
        # 显示数据表 - 将DataFrame转换为字符串类型以避免PyArrow类型转换问题
        # （DataFrame中包含混合类型：数值和"-"字符串，PyArrow无法处理）
        display_df = df.astype(str)
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # 显示公式说明
        formula_notes = get_formula_notes(selected_sheet)
        if formula_notes:
            with st.expander("📝 公式说明"):
                for indicator, formula in formula_notes.items():
                    st.markdown(f"**{indicator}**：{formula}")
        
        # 图表展示
        if len(df) > 0 and '科目' in df.columns:
            st.subheader("📈 趋势图")
            indicators = df['科目'].tolist()
            selected_indicators = st.multiselect(
                "选择要显示的指标",
                indicators,
                default=indicators[:min(5, len(indicators))],
                key=f"indicators_{selected_sheet}"
            )
            
            if selected_indicators:
                amount_df, percentage_df = prepare_chart_data(df, selected_indicators, start_year, end_year)
                if amount_df is not None or percentage_df is not None:
                    chart = create_dual_axis_line_chart(amount_df, percentage_df, f"{selected_sheet} - 趋势图")
                    st.plotly_chart(chart, use_container_width=True)
    
    # 下载Excel文件
    st.divider()
    filename = f"{company_name}_{start_year}-{end_year}_港股财务分析_{st.session_state.get('analysis_timestamp', '')}.xlsx"
    filepath = os.path.join("output", filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            excel_data = f.read()
        
        st.download_button(
            label="📥 下载Excel文件",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.caption(f"💾 文件已保存到：{filepath}")

