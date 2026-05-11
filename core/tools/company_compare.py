# -*- coding: utf-8 -*-
"""
企业财务对比工具

功能：
1. 支持多个企业的财务数据横向对比
2. 可选择特定年份和科目进行对比
3. 生成柱状图展示对比结果
"""

import os
import re
import tempfile
from typing import Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# 页面配置
# -----------------------------
st.set_page_config(
    page_title="企业财务对比分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# 辅助函数：从文件名提取企业名称
# -----------------------------
def extract_company_name_from_filename(filename: str) -> str:
    """
    从Excel文件名中提取企业名称
    
    文件名格式：{公司名称}_{起始年}-{结束年}_财务分析_{时间戳}.xlsx
    
    参数:
        filename: Excel文件名
    
    返回:
        企业名称
    """
    # 移除扩展名
    name_without_ext = os.path.splitext(filename)[0]
    
    # 匹配格式：{公司名称}_{起始年}-{结束年}_财务分析_{时间戳}
    pattern = r'^(.+?)_\d{4}-\d{4}_财务分析_\d+$'
    match = re.match(pattern, name_without_ext)
    
    if match:
        return match.group(1)
    
    # 如果格式不匹配，尝试提取第一个下划线之前的内容
    parts = name_without_ext.split('_')
    if len(parts) > 0:
        return parts[0]
    
    # 如果都不行，返回文件名（不含扩展名）
    return name_without_ext

# -----------------------------
# 辅助函数：验证并读取Excel文件
# -----------------------------
def validate_and_read_excel(file_bytes: bytes, filename: str) -> Tuple[bool, str, Optional[Dict[str, pd.DataFrame]], str]:
    """
    验证并读取Excel文件
    
    参数:
        file_bytes: 文件字节内容
        filename: 文件名
    
    返回:
        (是否有效, 错误信息, 数据字典, 企业名称)
    """
    try:
        # 保存到临时文件
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, filename)
        
        with open(temp_file_path, "wb") as f:
            f.write(file_bytes)
        
        # 读取所有sheet
        excel_file = pd.ExcelFile(temp_file_path)
        sheet_names = excel_file.sheet_names
        
        # 检查是否有财务分析的sheet名称
        expected_sheets = [
            '营收基本数据', '费用构成', '增长', '资产负债', 'WC分析',
            '固定资产投入分析', '收益率和杜邦分析', '资产周转', '人均数据'
        ]
        
        found_sheets = [name for name in sheet_names if name in expected_sheets]
        
        if not found_sheets:
            return False, "未找到财务分析sheet，请确保上传的是财务分析Excel文件", None, ""
        
        # 读取所有sheet数据
        results = {}
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(temp_file_path, sheet_name=sheet_name)
                
                # 验证数据格式：应该有"科目"列
                if df.empty:
                    continue
                
                # 检查是否有"科目"列
                if "科目" not in df.columns:
                    continue
                
                # 验证数据格式：第一列应该是"科目"，其他列应该是年份
                if len(df.columns) < 2:
                    continue
                
                # 清理数据：移除可能存在的公式说明行
                formula_row_idx = None
                for idx, row in df.iterrows():
                    if pd.notna(row.get("科目", "")) and "公式说明" in str(row.get("科目", "")):
                        formula_row_idx = idx
                        break
                
                if formula_row_idx is not None:
                    df = df.iloc[:formula_row_idx].copy()
                
                # 确保"科目"列存在且不为空
                df = df[df["科目"].notna()].copy()
                
                if df.empty:
                    continue
                
                results[sheet_name] = df
            except Exception as e:
                continue
        
        if not results:
            return False, "Excel文件中没有找到有效的数据sheet", None, ""
        
        # 提取企业名称
        company_name = extract_company_name_from_filename(filename)
        
        # 清理临时文件
        try:
            os.remove(temp_file_path)
        except:
            pass
        
        return True, "", results, company_name
        
    except Exception as e:
        return False, f"读取Excel文件失败: {str(e)}", None, ""

# -----------------------------
# 辅助函数：获取所有可用的Sheet和科目
# -----------------------------
def get_available_sheets_and_subjects(all_data: Dict[str, Dict[str, pd.DataFrame]]) -> Dict[str, List[str]]:
    """
    从所有企业的数据中提取可用的Sheet和科目
    
    参数:
        all_data: 所有企业的数据，格式为 {企业名称: {sheet_name: DataFrame}}
    
    返回:
        {sheet_name: [科目列表]}
    """
    sheets_subjects = {}
    
    for company_name, company_data in all_data.items():
        for sheet_name, df in company_data.items():
            if sheet_name not in sheets_subjects:
                sheets_subjects[sheet_name] = set()
            
            # 获取该Sheet的所有科目
            if "科目" in df.columns:
                subjects = df["科目"].dropna().tolist()
                sheets_subjects[sheet_name].update(subjects)
    
    # 转换为列表并排序
    result = {}
    for sheet_name, subjects_set in sheets_subjects.items():
        result[sheet_name] = sorted(list(subjects_set))
    
    return result

# -----------------------------
# 辅助函数：提取指定年份和科目的数值
# -----------------------------
def extract_value(df: pd.DataFrame, subject: str, year: int) -> Optional[float]:
    """
    从DataFrame中提取指定科目和年份的数值
    
    参数:
        df: 数据框
        subject: 科目名称
        year: 年份
    
    返回:
        数值，如果不存在或为"-"则返回None
    """
    # 查找科目所在行
    subject_row = df[df["科目"] == subject]
    
    if subject_row.empty:
        return None
    
    # 查找年份列（可能是字符串"2024"或整数2024）
    year_str = str(year)
    if year_str not in df.columns:
        # 尝试查找整数类型的年份列
        for col in df.columns:
            if col != "科目":
                try:
                    if int(float(str(col))) == year:
                        year_str = str(col)
                        break
                except:
                    continue
    
    if year_str not in subject_row.columns:
        return None
    
    value = subject_row[year_str].iloc[0]
    
    # 处理缺失值
    if pd.isna(value) or value == "-" or value == "":
        return None
    
    # 转换为数值
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

# -----------------------------
# 主界面
# -----------------------------
st.title("📊 企业财务对比分析")
st.caption("选择多个企业的财务分析Excel文件，进行横向数据对比")
st.markdown("---")

# 初始化session_state
if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []  # [(file_bytes, filename, company_name, data_dict), ...]
if 'selected_subjects' not in st.session_state:
    st.session_state['selected_subjects'] = {}  # {sheet_name: [subject_list]}

# 左侧：条件输入
with st.sidebar:
    st.header("📋 条件输入")
    
    # 1. 年份选择
    st.subheader("📅 年份选择")
    current_year = 2024  # 默认年份
    selected_year = st.number_input(
        "选择对比年份",
        min_value=2000,
        max_value=2035,
        value=current_year,
        step=1,
        help="所有企业将使用该年份的数据进行对比"
    )
    
    st.markdown("---")
    
    # 2. 文件选择
    st.subheader("📁 文件选择")
    uploaded_files = st.file_uploader(
        "选择财务分析Excel文件",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        help="可以上传多个企业的财务分析Excel文件"
    )
    
    # 处理新上传的文件
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # 检查是否已存在
            existing_filenames = [f[1] for f in st.session_state['uploaded_files']]
            if uploaded_file.name not in existing_filenames:
                # 验证并读取文件
                file_bytes = uploaded_file.getvalue()
                is_valid, error_msg, data_dict, company_name = validate_and_read_excel(file_bytes, uploaded_file.name)
                
                if is_valid:
                    st.session_state['uploaded_files'].append((file_bytes, uploaded_file.name, company_name, data_dict))
                    st.success(f"✅ {company_name} ({uploaded_file.name})")
                else:
                    st.error(f"❌ {uploaded_file.name}: {error_msg}")
    
    # 3. 已选企业显示
    if st.session_state['uploaded_files']:
        st.markdown("---")
        st.subheader("✅ 已选企业")
        
        # 显示已选企业列表
        for idx, (file_bytes, filename, company_name, data_dict) in enumerate(st.session_state['uploaded_files']):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• {company_name}")
            with col2:
                if st.button("删除", key=f"delete_{idx}", use_container_width=True):
                    st.session_state['uploaded_files'].pop(idx)
                    st.rerun()
        
        # 清除全部按钮
        if st.button("🗑️ 清除全部", use_container_width=True, type="secondary"):
            st.session_state['uploaded_files'] = []
            st.session_state['selected_subjects'] = {}
            st.rerun()
    
    st.markdown("---")
    
    # 4. 科目选择
    if st.session_state['uploaded_files']:
        st.subheader("📋 科目选择")
        
        # 获取所有可用的Sheet和科目
        all_data = {company_name: data_dict for _, _, company_name, data_dict in st.session_state['uploaded_files']}
        sheets_subjects = get_available_sheets_and_subjects(all_data)
        
        # 初始化selected_subjects
        if not st.session_state['selected_subjects']:
            st.session_state['selected_subjects'] = {sheet: [] for sheet in sheets_subjects.keys()}
        
        # 清理不再存在的Sheet的科目选择
        existing_sheets = set(sheets_subjects.keys())
        sheets_to_remove = [s for s in st.session_state['selected_subjects'].keys() if s not in existing_sheets]
        for sheet in sheets_to_remove:
            del st.session_state['selected_subjects'][sheet]
        
        # 为每个Sheet创建可折叠的选择区域
        selected_count = 0
        for sheet_name in sorted(sheets_subjects.keys()):
            subjects = sheets_subjects[sheet_name]
            
            # 确保该Sheet在selected_subjects中存在
            if sheet_name not in st.session_state['selected_subjects']:
                st.session_state['selected_subjects'][sheet_name] = []
            
            # 清理不再存在的科目
            existing_subjects = set(subjects)
            st.session_state['selected_subjects'][sheet_name] = [
                s for s in st.session_state['selected_subjects'][sheet_name] 
                if s in existing_subjects
            ]
            
            # 使用expander实现折叠
            selected_in_sheet = len(st.session_state['selected_subjects'][sheet_name])
            with st.expander(f"📄 {sheet_name} ({len(subjects)} 个科目, 已选 {selected_in_sheet})", expanded=False):
                # 全选/取消全选按钮（需同步更新每个 checkbox 的 session_state，否则带 key 的控件不会刷新）
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("全选", key=f"select_all_{sheet_name}", use_container_width=True):
                        st.session_state['selected_subjects'][sheet_name] = subjects.copy()
                        for sub in subjects:
                            st.session_state[f"subject_{sheet_name}_{sub}"] = True
                        st.rerun()
                with col2:
                    if st.button("取消全选", key=f"deselect_all_{sheet_name}", use_container_width=True):
                        st.session_state['selected_subjects'][sheet_name] = []
                        for sub in subjects:
                            st.session_state[f"subject_{sheet_name}_{sub}"] = False
                        st.rerun()
                
                # 科目复选框
                for subject in subjects:
                    is_selected = subject in st.session_state['selected_subjects'][sheet_name]
                    checkbox_key = f"subject_{sheet_name}_{subject}"
                    new_value = st.checkbox(
                        subject,
                        value=is_selected,
                        key=checkbox_key
                    )
                    
                    # 更新session_state
                    if new_value and subject not in st.session_state['selected_subjects'][sheet_name]:
                        st.session_state['selected_subjects'][sheet_name].append(subject)
                    elif not new_value and subject in st.session_state['selected_subjects'][sheet_name]:
                        st.session_state['selected_subjects'][sheet_name].remove(subject)
            
            selected_count += len(st.session_state['selected_subjects'][sheet_name])
        
        # 显示总选择数量
        if selected_count > 0:
            st.info(f"📊 共选择了 {selected_count} 个科目")
    
    st.markdown("---")
    
    # 5. 开始对比按钮
    compare_btn = st.button(
        "🚀 开始对比",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state['uploaded_files'] or selected_count == 0
    )

# 右侧：结果展示
if compare_btn and st.session_state['uploaded_files']:
    st.markdown("---")
    st.header("📊 对比结果")
    
    # 准备数据
    all_data = {company_name: data_dict for _, _, company_name, data_dict in st.session_state['uploaded_files']}
    
    # 按科目分组收集数据
    comparison_data = {}  # {subject: {company: value}}
    
    for sheet_name, subjects in st.session_state['selected_subjects'].items():
        if not subjects:
            continue
        
        for subject in subjects:
            comparison_data[f"{sheet_name} - {subject}"] = {}
            
            for company_name, data_dict in all_data.items():
                if sheet_name in data_dict:
                    df = data_dict[sheet_name]
                    value = extract_value(df, subject, selected_year)
                    comparison_data[f"{sheet_name} - {subject}"][company_name] = value
    
    # 生成图表
    if comparison_data:
        for full_subject_name, company_values in comparison_data.items():
            # 准备图表数据
            chart_data = []
            companies = []
            values = []
            
            for company, value in company_values.items():
                companies.append(company)
                if value is not None:
                    values.append(value)
                else:
                    values.append("-")
            
            # 创建DataFrame
            chart_df = pd.DataFrame({
                '企业': companies,
                '数值': values
            })
            
            # 过滤掉值为"-"的数据点（用于绘图）
            plot_df = chart_df[chart_df['数值'] != "-"].copy()
            
            if not plot_df.empty:
                # 转换为数值类型
                plot_df['数值'] = pd.to_numeric(plot_df['数值'], errors='coerce')
                plot_df = plot_df.dropna()
                
                if not plot_df.empty:
                    # 创建柱状图
                    fig = go.Figure()
                    
                    # 格式化数值标签
                    def format_value(x):
                        if pd.isna(x):
                            return '-'
                        # 根据数值大小选择格式
                        if abs(x) >= 1000:
                            return f'{x:,.0f}' if x == int(x) else f'{x:,.2f}'
                        elif abs(x) >= 1:
                            return f'{x:.2f}'
                        elif abs(x) >= 0.01:
                            return f'{x:.4f}'
                        else:
                            # 非常小的数值，使用科学计数法或更多小数位
                            return f'{x:.6f}'
                    
                    # 计算Y轴范围，为标签留出空间
                    y_min = plot_df['数值'].min()
                    y_max = plot_df['数值'].max()
                    y_range = y_max - y_min
                    
                    # 如果范围太小，设置最小范围
                    if y_range < 0.1:
                        y_range = 0.1
                    
                    # 增加上下边距（约15%），确保标签完整显示
                    y_padding = y_range * 0.15
                    y_axis_min = y_min - y_padding
                    y_axis_max = y_max + y_padding
                    
                    # 添加柱状图（使用更深的蓝色）
                    fig.add_trace(go.Bar(
                        x=plot_df['企业'],
                        y=plot_df['数值'],
                        text=plot_df['数值'].apply(format_value),
                        textposition='outside',
                        marker_color='#2563EB',  # 更深的蓝色
                        name=full_subject_name,
                        hovertemplate='<b>%{x}</b><br>数值: %{y:,.4f}<extra></extra>'
                    ))
                    
                    # 更新布局
                    fig.update_layout(
                        title=f"📈 {full_subject_name}",
                        xaxis_title="企业",
                        yaxis_title="数值",
                        height=400,
                        showlegend=False,
                        hovermode='closest',  # 改为closest，确保显示正确的数据点
                        # 设置Y轴范围，确保标签不被截断
                        yaxis=dict(
                            range=[y_axis_min, y_axis_max]
                        ),
                        # 增加上下边距，确保标签完整显示
                        margin=dict(t=50, b=80, l=50, r=50)
                    )
                    
                    # 显示图表
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning(f"⚠️ {full_subject_name}: 所有企业的数据都缺失或无效")
            else:
                st.warning(f"⚠️ {full_subject_name}: 所有企业的数据都缺失")
            
            st.markdown("---")
    else:
        st.warning("⚠️ 没有找到可对比的数据，请检查选择的科目和年份")

elif not st.session_state['uploaded_files']:
    st.info("👈 请在左侧上传财务分析Excel文件并选择对比科目")
elif selected_count == 0:
    st.info("👈 请在左侧选择要对比的科目")
