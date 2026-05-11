"""
财务分析工具 - Streamlit Web 界面

功能：
1. 股票代码输入和公司信息查询
2. 年份范围选择
3. 一键生成完整的财务分析报告
4. 结果可视化展示（表格和图表）
5. Excel 文件下载
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

# 动态导入财务分析模块（因为文件名以数字开头）
spec = importlib.util.spec_from_file_location("financial_analysis", ROOT / "core/a_share/financial_analysis.py")
financial_analysis = importlib.util.module_from_spec(spec)
sys.modules["financial_analysis"] = financial_analysis
spec.loader.exec_module(financial_analysis)

# 导入函数
get_symbol_name = financial_analysis.get_symbol_name
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

# 辅助函数：获取公式说明
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

# 辅助函数：从Excel文件名解析信息
def parse_excel_filename(filename):
    """
    从Excel文件名解析股票代码、公司名称、年份范围
    
    格式：公司名称_起始年-结束年_财务分析_时间戳.xlsx
    例如：科沃斯_2013-2021_财务分析_20251212111013.xlsx
    
    返回: (company_name, start_year, end_year, symbol) 或 None
    """
    if not filename or not filename.endswith('.xlsx'):
        return None
    
    # 移除扩展名
    basename = filename.replace('.xlsx', '')
    
    # 匹配格式：公司名_起始年-结束年_财务分析_时间戳
    pattern = r'(.+?)_(\d{4})-(\d{4})_财务分析_\d+'
    match = re.match(pattern, basename)
    
    if match:
        company_name = match.group(1)
        start_year = int(match.group(2))
        end_year = int(match.group(3))
        # 注意：从文件名无法直接获取股票代码，需要用户输入或从其他地方获取
        return (company_name, start_year, end_year, None)
    
    return None

# 辅助函数：从员工数量CSV文件名解析股票代码
def parse_employee_csv_filename(filename):
    """
    从员工数量CSV文件名解析股票代码
    
    格式：xxxx_员工数量.csv
    例如：603486_员工数量.csv
    
    返回: 股票代码字符串 或 None
    """
    if not filename or not filename.endswith('_员工数量.csv'):
        return None
    
    # 提取股票代码（文件名开头部分）
    basename = filename.replace('_员工数量.csv', '')
    # 匹配6位数字股票代码
    match = re.match(r'^(\d{6})', basename)
    if match:
        return match.group(1)
    
    return None

# 辅助函数：加载Excel文件
def load_excel_file(file_input):
    """
    加载Excel文件，返回所有sheet的字典
    
    参数:
        file_input: 可以是文件路径（字符串）或Streamlit UploadedFile对象
    
    返回: {sheet_name: DataFrame}
    """
    try:
        # 如果是UploadedFile对象，使用BytesIO
        if hasattr(file_input, 'read'):
            excel_file = pd.ExcelFile(io.BytesIO(file_input.read()))
        else:
            # 如果是文件路径
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
    
    参数:
        indicator_name: 指标名称
    
    返回:
        True表示百分比，False表示金额
    """
    percentage_keywords = ['率', '%', '比率', '占比', '比例', '增长率', '复合增长率']
    return any(keyword in indicator_name for keyword in percentage_keywords)

# 辅助函数：准备图表数据
def prepare_chart_data(df, selected_indicators, start_year, end_year):
    """
    准备图表数据，将DataFrame转换为适合绘制折线图的格式
    
    参数:
        df: 原始DataFrame（科目为行，年份为列）
        selected_indicators: 选中的指标列表
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        (金额数据DataFrame, 百分比数据DataFrame)
    """
    # 获取年份列（可能是字符串格式的年份）
    year_cols = [str(year) for year in range(start_year, end_year + 1)]
    
    # 筛选选中的指标
    selected_df = df[df['科目'].isin(selected_indicators)].copy()
    
    if selected_df.empty:
        return None, None
    
    # 准备数据：转换为长格式（年份-指标-数值）
    amount_data = []
    percentage_data = []
    
    for _, row in selected_df.iterrows():
        indicator = row['科目']
        is_percentage = is_percentage_indicator(indicator)
        
        for year_col in year_cols:
            if year_col in row.index:
                value = row[year_col]
                # 跳过缺失值
                if value == '-' or pd.isna(value) or value == '':
                    continue
                
                try:
                    # 处理可能包含逗号的数值（如 "1,141"）
                    if isinstance(value, str):
                        value = value.replace(',', '').replace('，', '')
                    num_value = float(value)
                    
                    # 跳过0值（可能是无效数据）
                    if num_value == 0:
                        continue
                    
                    year = int(year_col)  # year_col已经是字符串格式
                    
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
    
    参数:
        amount_df: 金额数据DataFrame（年份、指标、数值）
        percentage_df: 百分比数据DataFrame（年份、指标、数值）
        title: 图表标题
    
    返回:
        Plotly图表对象
    """
    fig = go.Figure()
    
    # 定义颜色列表（金额数据使用实线，百分比数据使用虚线）
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
            title='年份',
            type='linear',
            dtick=1,
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title='金额（亿元/万元）',
            side='left',
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis2=dict(
            title='百分比（%）',
            side='right',
            overlaying='y',
            showgrid=False
        ),
        height=550,
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
        ),
        plot_bgcolor='white'
    )
    
    return fig

# 辅助函数：创建单Y轴折线图（当只有一种类型的数据时）
def create_single_axis_line_chart(data_df, title="趋势图", yaxis_title="数值"):
    """
    创建单Y轴折线图
    
    参数:
        data_df: 数据DataFrame（年份、指标、数值）
        title: 图表标题
        yaxis_title: Y轴标题
    
    返回:
        Plotly图表对象
    """
    fig = go.Figure()
    
    # 定义颜色列表
    colors = px.colors.qualitative.Set1
    
    if data_df is not None and not data_df.empty:
        indicators = data_df['指标'].unique()
        for idx, indicator in enumerate(indicators):
            indicator_data = data_df[data_df['指标'] == indicator].sort_values('年份')
            color = colors[idx % len(colors)]
            fig.add_trace(go.Scatter(
                x=indicator_data['年份'],
                y=indicator_data['数值'],
                name=indicator,
                mode='lines+markers',
                line=dict(width=2.5, color=color),
                marker=dict(size=7, color=color),
                hovertemplate='<b>%{fullData.name}</b><br>年份: %{x}<br>数值: %{y:.2f}<extra></extra>'
            ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        xaxis=dict(
            title='年份',
            type='linear',
            dtick=1,
            showgrid=True,
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title=yaxis_title,
            showgrid=True,
            gridcolor='lightgray'
        ),
        height=550,
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1
        ),
        plot_bgcolor='white'
    )
    
    return fig

# 辅助函数：加载员工数量CSV文件
def load_employee_csv(file_input):
    """
    加载员工数量CSV文件
    
    参数:
        file_input: 可以是文件路径（字符串）或Streamlit UploadedFile对象
    
    返回: DataFrame 或 None
    """
    try:
        # 如果是UploadedFile对象，使用StringIO
        if hasattr(file_input, 'read'):
            # 读取文件内容
            content = file_input.read()
            # 如果是bytes，需要解码
            if isinstance(content, bytes):
                content = content.decode('utf-8-sig')
            # 使用StringIO
            from io import StringIO
            df = pd.read_csv(StringIO(content), encoding='utf-8-sig')
        else:
            # 如果是文件路径
            df = pd.read_csv(file_input, encoding='utf-8-sig')
        
        # 确保有'年份'和'员工数量'列
        if '年份' in df.columns and '员工数量' in df.columns:
            return df
        else:
            st.warning("CSV文件格式不正确，需要包含'年份'和'员工数量'列")
            return None
    except Exception as e:
        st.error(f"加载员工数量CSV文件失败：{str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return None

# 页面配置
st.set_page_config(
    page_title="财务分析工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# 标题
st.markdown('<h1 class="main-header">📊 上市公司财务分析工具</h1>', unsafe_allow_html=True)

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
            # 模式切换了，清除之前的数据
            if analysis_mode == "🆕 新建分析":
                # 切换到新建分析，清除加载的数据
                if 'loaded_excel_data' in st.session_state:
                    del st.session_state['loaded_excel_data']
                    del st.session_state['loaded_file_info']
                    del st.session_state['loaded_file_name']
                    del st.session_state['loaded_file_content']
            else:
                # 切换到加载模式，清除分析结果
                if 'analysis_results' in st.session_state:
                    del st.session_state['analysis_results']
    
    st.session_state['last_analysis_mode'] = analysis_mode
    
    st.divider()
    
    # 如果选择加载已有结果
    file_info = None  # 初始化变量
    if analysis_mode == "📂 加载已有结果":
        st.subheader("📂 选择结果文件")
        result_file = st.file_uploader(
            "选择已生成的Excel文件",
            type=['xlsx'],
            help="选择之前生成的财务分析Excel文件，格式：公司名_起始年-结束年_财务分析_时间戳.xlsx",
            key="result_file_uploader"
        )
        
        if result_file:
            # 解析文件名
            file_info = parse_excel_filename(result_file.name)
            if file_info:
                company_name_from_file, start_year_from_file, end_year_from_file, _ = file_info
                st.success(f"✓ 文件信息：**{company_name_from_file}** ({start_year_from_file}-{end_year_from_file})")
                # 文件合法，不需要显示输入框，直接使用解析出的信息
                symbol = ""  # 加载模式下不需要股票代码
                start_year = start_year_from_file
                end_year = end_year_from_file
            else:
                # 文件格式不合法
                st.error("❌ 文件格式不合法！")
                st.warning("⚠️ 文件名格式应为：`公司名_起始年-结束年_财务分析_时间戳.xlsx`")
                st.info("例如：`科沃斯_2013-2021_财务分析_20251212111013.xlsx`")
                # 阻止继续执行
                symbol = None
                start_year = None
                end_year = None
                result_file = None  # 标记为无效文件
        else:
            # 未选择文件
            symbol = None
            start_year = None
            end_year = None
            st.info("💡 请上传Excel文件")
    else:
        result_file = None
        # 新建分析模式
        # 股票代码输入
        symbol = st.text_input(
            "股票代码",
            value="603486",
            help="请输入6位股票代码，如：603486（科沃斯）、600519（贵州茅台）",
            placeholder="例如：603486"
        )
        
        # 年份范围选择
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input(
                "起始年份",
                min_value=2000,
                max_value=2030,
                value=2013,
                step=1,
                key="start_year_input"
            )
        with col2:
            end_year = st.number_input(
                "结束年份",
                min_value=2000,
                max_value=2030,
                value=2021,
                step=1,
                key="end_year_input"
            )
        
        # 验证年份范围
        if start_year > end_year:
            st.error("⚠️ 起始年份不能大于结束年份！")
            st.stop()
    
    st.divider()
    
    # 员工数量CSV文件选择（仅在新建分析模式下显示）
    if analysis_mode == "🆕 新建分析":
        st.subheader("👥 员工数量数据（可选）")
        employee_csv_file = st.file_uploader(
            "选择员工数量CSV文件",
            type=['csv'],
            help="选择员工数量CSV文件，格式：股票代码_员工数量.csv，用于计算人均数据",
            key="employee_csv"
        )
        
        if employee_csv_file:
            # 尝试从文件名解析股票代码
            csv_symbol = parse_employee_csv_filename(employee_csv_file.name)
            if csv_symbol:
                st.success(f"✓ 识别到股票代码：{csv_symbol}")
                if symbol != csv_symbol:
                    st.warning(f"⚠️ 文件中的股票代码({csv_symbol})与输入的股票代码({symbol})不一致")
            else:
                st.info("💡 已选择员工数量文件，将在计算人均数据时使用")
    else:
        employee_csv_file = None
    
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
        # 加载模式下不需要选择模块，所有模块都会加载
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
        # 只有在文件合法时才显示加载按钮
        if result_file and file_info:
            load_button = st.button(
                "📂 加载结果文件",
                type="primary",
                use_container_width=True
            )
            # 如果点击了加载按钮，保存数据到 session_state
            if load_button:
                st.session_state['loaded_excel_data'] = load_excel_file(result_file)
                st.session_state['loaded_file_info'] = file_info
                st.session_state['loaded_file_name'] = result_file.name
                st.session_state['loaded_file_content'] = result_file.getvalue()
        elif result_file:
            # 文件不合法，不显示按钮，已经在上方显示了错误信息
            pass
        else:
            # 未选择文件，不显示按钮
            pass
    else:
        analyze_button = st.button(
            "🚀 开始分析",
            type="primary",
            use_container_width=True
        )
        # 如果点击了分析按钮，清除之前加载的数据
        if analyze_button:
            if 'loaded_excel_data' in st.session_state:
                del st.session_state['loaded_excel_data']
                del st.session_state['loaded_file_info']
                del st.session_state['loaded_file_name']
                del st.session_state['loaded_file_content']

# 主内容区 - 加载已有结果
# 检查 session_state 中是否有已加载的数据，或者是否刚点击了加载按钮
if (load_button and result_file) or ('loaded_excel_data' in st.session_state and st.session_state['loaded_excel_data']):
    try:
        # 优先使用 session_state 中的数据
        if 'loaded_excel_data' in st.session_state and st.session_state['loaded_excel_data']:
            excel_data = st.session_state['loaded_excel_data']
            file_info = st.session_state.get('loaded_file_info')
            file_name = st.session_state.get('loaded_file_name', '已加载的文件')
        else:
            # 刚点击加载按钮，读取并保存数据
            excel_data = load_excel_file(result_file)
            file_info = parse_excel_filename(result_file.name)
            file_name = result_file.name
            # 保存到 session_state
            st.session_state['loaded_excel_data'] = excel_data
            st.session_state['loaded_file_info'] = file_info
            st.session_state['loaded_file_name'] = file_name
            st.session_state['loaded_file_content'] = result_file.getvalue()
        
        if excel_data:
            st.success(f"✅ 成功加载文件：{file_name}")
            
            # 解析文件名获取信息
            if file_info:
                company_name_from_file, start_year_from_file, end_year_from_file, _ = file_info
                st.info(f"📋 文件信息：{company_name_from_file} ({start_year_from_file}-{end_year_from_file})")
            
            # 显示结果
            st.divider()
            st.header("📊 分析结果")
            
            # 为每个sheet创建标签页
            tabs = st.tabs(list(excel_data.keys()))
            
            # 从文件名获取年份范围（用于所有sheet）
            chart_start_year = None
            chart_end_year = None
            if file_info:
                _, chart_start_year, chart_end_year, _ = file_info
            
            for idx, (sheet_name, df) in enumerate(excel_data.items()):
                with tabs[idx]:
                    st.subheader(f"📋 {sheet_name}")
                    
                    # 显示数据表 - 将DataFrame转换为字符串类型以避免PyArrow类型转换问题
                    display_df = df.astype(str)
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # 显示公式说明
                    formula_notes = get_formula_notes(sheet_name)
                    if formula_notes:
                        st.markdown("---")
                        st.markdown("### 📝 公式说明")
                        for metric_name, formula in formula_notes.items():
                            st.markdown(f"**{metric_name}**: {formula}")
                    
                    # 创建可视化图表
                    try:
                        # 获取所有指标（排除年份列）
                        indicators = df['科目'].tolist()
                        numeric_cols = [col for col in df.columns if col != '科目' and col.isdigit()]
                        
                        if indicators and numeric_cols:
                            # 确定年份范围
                            if chart_start_year and chart_end_year:
                                # 使用文件名中的年份范围
                                start_year = chart_start_year
                                end_year = chart_end_year
                            else:
                                # 如果无法从文件名获取，从列名推断（列名是字符串格式的年份）
                                numeric_cols_int = [int(col) for col in numeric_cols if col.isdigit()]
                                if numeric_cols_int:
                                    start_year = min(numeric_cols_int)
                                    end_year = max(numeric_cols_int)
                                else:
                                    # 如果还是无法获取，跳过图表
                                    st.warning("⚠️ 无法确定年份范围，跳过图表生成")
                                    continue
                            
                            st.subheader("📈 趋势分析")
                            
                            # 多选指标（缺省选择第一个）
                            default_selection = [indicators[0]] if indicators else []
                            selected_indicators = st.multiselect(
                                f"选择要可视化的指标（{sheet_name}）",
                                options=indicators,
                                default=default_selection,
                                key=f"indicators_{sheet_name}_loaded"
                            )
                            
                            if selected_indicators:
                                # 准备数据
                                amount_df, percentage_df = prepare_chart_data(
                                    df, selected_indicators, start_year, end_year
                                )
                                
                                # 创建图表
                                if (amount_df is not None and not amount_df.empty) and \
                                   (percentage_df is not None and not percentage_df.empty):
                                    # 两种类型都有，使用双Y轴
                                    fig = create_dual_axis_line_chart(
                                        amount_df, percentage_df,
                                        title=f"{sheet_name} - 趋势图"
                                    )
                                elif amount_df is not None and not amount_df.empty:
                                    # 只有金额数据
                                    fig = create_single_axis_line_chart(
                                        amount_df,
                                        title=f"{sheet_name} - 趋势图",
                                        yaxis_title="金额（亿元/万元）"
                                    )
                                elif percentage_df is not None and not percentage_df.empty:
                                    # 只有百分比数据
                                    fig = create_single_axis_line_chart(
                                        percentage_df,
                                        title=f"{sheet_name} - 趋势图",
                                        yaxis_title="百分比（%）"
                                    )
                                else:
                                    st.warning("⚠️ 选中的指标没有有效数据")
                                    fig = None
                                
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("💡 请至少选择一个指标进行可视化")
                    except Exception as e:
                        st.warning(f"⚠️ 图表生成失败：{str(e)}")
                        import traceback
                        with st.expander("查看错误详情"):
                            st.code(traceback.format_exc())
            
            # 提供下载按钮（重新下载原文件）
            file_content = st.session_state.get('loaded_file_content')
            file_name_for_download = st.session_state.get('loaded_file_name', '财务分析结果.xlsx')
            
            if file_content:
                st.download_button(
                    label="📥 重新下载Excel文件",
                    data=file_content,
                    file_name=file_name_for_download,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        else:
            st.error("❌ 加载文件失败")
    except Exception as e:
        st.error(f"❌ 加载文件时出现错误：{str(e)}")
        import traceback
        with st.expander("查看详细错误信息"):
            st.code(traceback.format_exc())

# 主内容区 - 新建分析
# 检查是否有已保存的分析结果，或者是否刚点击了分析按钮
elif analyze_button or ('analysis_results' in st.session_state and st.session_state['analysis_results']):
    # 如果已有结果且不是刚点击按钮，直接使用；否则重新计算
    if 'analysis_results' in st.session_state and st.session_state['analysis_results'] and not analyze_button:
        # 使用已保存的结果
        results = st.session_state['analysis_results']
        company_name = st.session_state.get('analysis_company_name', '')
        start_year = st.session_state.get('analysis_start_year', start_year)
        end_year = st.session_state.get('analysis_end_year', end_year)
        timestamp = st.session_state.get('analysis_timestamp', '')
        filepath = st.session_state.get('analysis_filepath', '')
        
        st.success(f"✓ 公司名称：**{company_name}** ({st.session_state.get('analysis_symbol', symbol)})")
        st.info(f"📅 分析年份范围：{start_year} - {end_year}")
        
        # 提供下载按钮（如果文件存在）
        if filepath and os.path.exists(filepath):
            file_content = st.session_state.get('analysis_file_content')
            if not file_content:
                with open(filepath, "rb") as f:
                    file_content = f.read()
                    st.session_state['analysis_file_content'] = file_content
            
            filename = os.path.basename(filepath)
            st.download_button(
                label="📥 下载完整Excel报告",
                data=file_content,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        # 重新计算（刚点击了分析按钮）
        # 显示进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 初始化结果存储
        results = {}
        company_name = None
        
        try:
            # 步骤1：获取公司名称
            status_text.text("📝 正在获取公司信息...")
            progress_bar.progress(10)
            company_name = get_symbol_name(symbol)
            
            if not company_name or company_name == symbol.replace('.SZ', '').replace('.SH', ''):
                st.warning(f"⚠️ 未能获取公司名称，使用股票代码：{symbol}")
                company_name = symbol.replace('.SZ', '').replace('.SH', '')
            
            st.success(f"✓ 公司名称：**{company_name}** ({symbol})")
            st.info(f"📅 分析年份范围：{start_year} - {end_year}")
            
            # 生成时间戳
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # 步骤2：计算各项指标
            total_steps = sum([
                analyze_revenue, analyze_expense, analyze_growth, 
                analyze_balance, analyze_wc, analyze_fixed_asset, analyze_roi, 
                analyze_asset_turnover, analyze_per_capita
            ])
            current_step = 0
            
            # 营收基本数据
            if analyze_revenue:
                current_step += 1
                status_text.text(f"📊 正在计算营收基本数据... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                revenue_df = calculate_revenue_metrics(symbol, start_year, end_year)
                if revenue_df is not None and not revenue_df.empty:
                    results['营收基本数据'] = revenue_df
            
            # 费用构成
            if analyze_expense:
                current_step += 1
                status_text.text(f"💰 正在计算费用构成... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                expense_df = calculate_expense_metrics(symbol, start_year, end_year)
                if expense_df is not None and not expense_df.empty:
                    results['费用构成'] = expense_df
            
            # 增长率
            if analyze_growth:
                current_step += 1
                status_text.text(f"📈 正在计算增长率... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                growth_df = calculate_growth_metrics(symbol, start_year, end_year)
                if growth_df is not None and not growth_df.empty:
                    results['增长'] = growth_df
            
            # 资产负债
            if analyze_balance:
                current_step += 1
                status_text.text(f"🏦 正在计算资产负债... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                balance_df = calculate_balance_sheet_metrics(symbol, start_year, end_year)
                if balance_df is not None and not balance_df.empty:
                    results['资产负债'] = balance_df
            
            # WC分析
            if analyze_wc:
                current_step += 1
                status_text.text(f"💼 正在计算WC分析... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                wc_df = calculate_wc_metrics(symbol, start_year, end_year)
                if wc_df is not None and not wc_df.empty:
                    results['WC分析'] = wc_df
            
            # 固定资产投入分析
            if analyze_fixed_asset:
                current_step += 1
                status_text.text(f"🏗️ 正在计算固定资产投入分析... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                fixed_asset_df = calculate_fixed_asset_metrics(symbol, start_year, end_year)
                if fixed_asset_df is not None and not fixed_asset_df.empty:
                    results['固定资产投入分析'] = fixed_asset_df
            
            # 收益率和杜邦分析
            if analyze_roi:
                current_step += 1
                status_text.text(f"📊 正在计算收益率和杜邦分析... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                roi_df = calculate_roi_metrics(symbol, start_year, end_year)
                if roi_df is not None and not roi_df.empty:
                    results['收益率和杜邦分析'] = roi_df
            
            # 资产周转
            if analyze_asset_turnover:
                current_step += 1
                status_text.text(f"🔄 正在计算资产周转... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                asset_turnover_df = calculate_asset_turnover_metrics(symbol, start_year, end_year)
                if asset_turnover_df is not None and not asset_turnover_df.empty:
                    results['资产周转'] = asset_turnover_df
            
            # 人均数据
            if analyze_per_capita:
                current_step += 1
                status_text.text(f"👥 正在计算人均数据... ({current_step}/{total_steps})")
                progress_bar.progress(10 + int(70 * current_step / total_steps))
                
                # 如果提供了员工数量CSV文件，读取并使用
                employee_data_dict = None
                if employee_csv_file:
                    try:
                        employee_df = load_employee_csv(employee_csv_file)
                        if employee_df is not None:
                            # 创建年份到员工数量的字典
                            employee_data_dict = {}
                            for _, row in employee_df.iterrows():
                                year = int(row['年份'])
                                count = row['员工数量']
                                if pd.notna(count) and count != '':
                                    try:
                                        employee_data_dict[year] = int(float(count))
                                    except:
                                        pass
                            
                            if employee_data_dict:
                                st.info(f"✓ 已加载员工数量数据，共 {len(employee_data_dict)} 个年份")
                                # 显示已加载的年份范围
                                if employee_data_dict:
                                    min_year = min(employee_data_dict.keys())
                                    max_year = max(employee_data_dict.keys())
                                    st.info(f"📅 数据年份范围：{min_year}-{max_year}")
                    except Exception as e:
                        st.warning(f"⚠️ 读取员工数量CSV文件失败：{str(e)}，将使用默认方法获取")
                
                # 将CSV文件保存到临时文件，然后传递给calculate_per_capita_metrics
                employee_csv_path = None
                if employee_csv_file and employee_data_dict:
                    # 创建临时CSV文件
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    temp_csv_path = os.path.join(temp_dir, f"{symbol.replace('.SZ', '').replace('.SH', '')}_员工数量_temp.csv")
                    # 将employee_data_dict转换为DataFrame并保存
                    temp_df = pd.DataFrame({
                        '年份': list(employee_data_dict.keys()),
                        '员工数量': list(employee_data_dict.values())
                    })
                    temp_df.to_csv(temp_csv_path, index=False, encoding='utf-8-sig')
                    employee_csv_path = temp_csv_path
                
                per_capita_df = calculate_per_capita_metrics(symbol, start_year, end_year, employee_csv_path=employee_csv_path)
                
                # 清理临时文件
                if employee_csv_path and os.path.exists(employee_csv_path):
                    try:
                        os.remove(employee_csv_path)
                    except:
                        pass
                
                if per_capita_df is not None and not per_capita_df.empty:
                    results['人均数据'] = per_capita_df
            
            # 完成
            progress_bar.progress(100)
            status_text.text("✅ 分析完成！")
            
            # 保存到Excel
            if results:
                status_text.text("💾 正在保存Excel文件...")
                for sheet_name, df in results.items():
                    save_to_excel(df, symbol, company_name, start_year, end_year, sheet_name, timestamp=timestamp)
                
                # 生成文件路径
                symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
                filename = f"{company_name}_{start_year}-{end_year}_财务分析_{timestamp}.xlsx"
                filepath = os.path.join("output", filename)
                
                # 保存结果到 session_state
                st.session_state['analysis_results'] = results
                st.session_state['analysis_company_name'] = company_name
                st.session_state['analysis_symbol'] = symbol
                st.session_state['analysis_start_year'] = start_year
                st.session_state['analysis_end_year'] = end_year
                st.session_state['analysis_timestamp'] = timestamp
                st.session_state['analysis_filepath'] = filepath
                
                # 显示结果
                st.success(f"✅ 所有分析完成！共生成 {len(results)} 个分析模块")
                
                # 提供下载按钮
                if os.path.exists(filepath):
                    with open(filepath, "rb") as f:
                        file_content = f.read()
                        st.session_state['analysis_file_content'] = file_content
                        st.download_button(
                            label="📥 下载完整Excel报告",
                            data=file_content,
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
            
            # 清除进度条
            progress_bar.empty()
            status_text.empty()
        except Exception as e:
            st.error(f"❌ 分析过程中出现错误：{str(e)}")
            import traceback
            with st.expander("查看详细错误信息"):
                st.code(traceback.format_exc())
            results = {}
    
    # 显示结果（无论是刚计算的还是从 session_state 读取的）
    if 'analysis_results' in st.session_state and st.session_state['analysis_results']:
        results = st.session_state['analysis_results']
        start_year = st.session_state.get('analysis_start_year', start_year)
        end_year = st.session_state.get('analysis_end_year', end_year)
        company_name = st.session_state.get('analysis_company_name', '')
        
        if results:
            st.divider()
            st.header("📊 分析结果")
            
            # 为每个结果创建标签页
            tabs = st.tabs(list(results.keys()))
            
            for idx, (sheet_name, df) in enumerate(results.items()):
                with tabs[idx]:
                    st.subheader(f"📋 {sheet_name}")
                    
                    # 显示数据表 - 将DataFrame转换为字符串类型以避免PyArrow类型转换问题
                    display_df = df.astype(str)
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # 显示公式说明
                    formula_notes = get_formula_notes(sheet_name)
                    if formula_notes:
                        st.markdown("---")
                        st.markdown("### 📝 公式说明")
                        for metric_name, formula in formula_notes.items():
                            st.markdown(f"**{metric_name}**: {formula}")
                    
                    # 创建可视化图表
                    try:
                        # 获取所有指标（排除年份列）
                        indicators = df['科目'].tolist()
                        numeric_cols = [col for col in df.columns if col != '科目' and col.isdigit()]
                        
                        if indicators and numeric_cols:
                            st.subheader("📈 趋势分析")
                            
                            # 多选指标（缺省选择第一个）
                            default_selection = [indicators[0]] if indicators else []
                            selected_indicators = st.multiselect(
                                f"选择要可视化的指标（{sheet_name}）",
                                options=indicators,
                                default=default_selection,
                                key=f"indicators_{sheet_name}"
                            )
                            
                            if selected_indicators:
                                # 准备数据
                                amount_df, percentage_df = prepare_chart_data(
                                    df, selected_indicators, start_year, end_year
                                )
                                
                                # 创建图表
                                if (amount_df is not None and not amount_df.empty) and \
                                   (percentage_df is not None and not percentage_df.empty):
                                    # 两种类型都有，使用双Y轴
                                    fig = create_dual_axis_line_chart(
                                        amount_df, percentage_df,
                                        title=f"{sheet_name} - 趋势图"
                                    )
                                elif amount_df is not None and not amount_df.empty:
                                    # 只有金额数据
                                    fig = create_single_axis_line_chart(
                                        amount_df,
                                        title=f"{sheet_name} - 趋势图",
                                        yaxis_title="金额（亿元/万元）"
                                    )
                                elif percentage_df is not None and not percentage_df.empty:
                                    # 只有百分比数据
                                    fig = create_single_axis_line_chart(
                                        percentage_df,
                                        title=f"{sheet_name} - 趋势图",
                                        yaxis_title="百分比（%）"
                                    )
                                else:
                                    st.warning("⚠️ 选中的指标没有有效数据")
                                    fig = None
                                
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("💡 请至少选择一个指标进行可视化")
                    except Exception as e:
                        st.warning(f"⚠️ 图表生成失败：{str(e)}")
                        import traceback
                        with st.expander("查看错误详情"):
                            st.code(traceback.format_exc())

else:
    # 欢迎页面
    st.markdown("""
    ## 👋 欢迎使用财务分析工具
    
    这是一个基于 **AKShare** 和 **Streamlit** 构建的上市公司财务分析工具。
    
    ### ✨ 主要功能
    
    1. **📊 营收基本数据**：收入、净利润、现金流、自由现金流等核心指标
    2. **💰 费用构成**：毛利率、净利率、各项费用率分析
    3. **📈 增长率**：年度增长率和复合增长率（3年/5年）
    4. **🏦 资产负债**：资产、负债结构分析
    5. **💼 WC分析**：营运资金相关指标
    6. **🏗️ 固定资产投入分析**：固定资产与收入的关系
    7. **📊 收益率和杜邦分析**：ROE、ROA、ROIC、销售净利率、资产周转率、权益乘数
    8. **🔄 资产周转**：总资产、平均总资产、平均流动资产、平均存货、归母净资产、平均归母净资产，以及各类资产周转天数
    8. **👥 人均数据**：人均收入、人均利润、人均薪酬
    
    ### 🚀 使用步骤
    
    1. 在左侧边栏输入**股票代码**（如：603486）
    2. 选择**年份范围**（起始年份和结束年份）
    3. 勾选要分析的**模块**
    4. 点击 **"开始分析"** 按钮
    5. 查看结果并下载Excel报告
    
    ### 📝 使用示例
    
    - **科沃斯**：603486
    - **贵州茅台**：600519
    - **平安银行**：000001
    - **万科A**：000002
    
    ### ⚠️ 注意事项
    
    - 数据来源于公开数据源，仅供参考
    - 首次分析可能需要较长时间（数据获取）
    - 建议选择合理的年份范围（通常5-10年）
    - 某些股票可能缺少部分年份的数据
    
    ---
    
    **开始分析**：请在左侧边栏设置参数，然后点击"开始分析"按钮。
    """)

