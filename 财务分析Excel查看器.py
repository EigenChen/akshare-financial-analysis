# -*- coding: utf-8 -*-
"""
财务分析Excel查看器

功能：
1. 上传之前保存的财务分析Excel文件
2. 在界面上显示数据表格和图表
3. 支持所有财务分析sheet的查看

注意：只支持财务分析的Excel文件格式
"""

import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
from typing import Dict, Optional

# -----------------------------
# 页面配置
# -----------------------------
st.set_page_config(
    page_title="财务分析Excel查看器",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
# 验证Excel文件格式
# -----------------------------
def validate_excel_file(file_path: str) -> tuple[bool, str, Optional[Dict[str, pd.DataFrame]]]:
    """
    验证Excel文件是否是财务分析文件格式
    
    参数:
        file_path: Excel文件路径
    
    返回:
        (是否有效, 错误信息, 数据字典)
    """
    try:
        # 读取所有sheet
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        
        # 检查是否有财务分析的sheet名称
        expected_sheets = [
            '营收基本数据', '费用构成', '增长', '资产负债', 'WC分析',
            '固定资产投入分析', '收益率和杜邦分析', '资产周转', '人均数据'
        ]
        
        found_sheets = [name for name in sheet_names if name in expected_sheets]
        
        if not found_sheets:
            return False, "未找到财务分析sheet，请确保上传的是财务分析Excel文件", None
        
        # 读取所有sheet数据
        results = {}
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                
                # 验证数据格式：应该有"科目"列
                if df.empty:
                    continue
                
                # 检查是否有"科目"列
                if "科目" not in df.columns:
                    # 跳过不符合格式的sheet（可能是公式说明等）
                    continue
                
                # 验证数据格式：第一列应该是"科目"，其他列应该是年份
                # 至少应该有科目列和至少一列年份数据
                if len(df.columns) < 2:
                    continue
                
                # 清理数据：移除可能存在的公式说明行（包含"公式说明"文本的行）
                # 查找"公式说明"所在的行索引
                formula_row_idx = None
                for idx, row in df.iterrows():
                    if pd.notna(row.get("科目", "")) and "公式说明" in str(row.get("科目", "")):
                        formula_row_idx = idx
                        break
                
                # 如果有公式说明行，只保留之前的数据
                if formula_row_idx is not None:
                    df = df.iloc[:formula_row_idx].copy()
                
                # 确保"科目"列存在且不为空
                df = df[df["科目"].notna()].copy()
                
                if df.empty:
                    continue
                
                results[sheet_name] = df
            except Exception as e:
                # 如果某个sheet读取失败，跳过
                continue
        
        if not results:
            return False, "Excel文件中没有找到有效的数据sheet", None
        
        return True, "", results
        
    except Exception as e:
        return False, f"读取Excel文件失败: {str(e)}", None

# -----------------------------
# 显示数据表格和图表
# -----------------------------
def display_sheet_data(sheet_name: str, df: pd.DataFrame):
    """
    显示单个sheet的数据表格和图表
    
    参数:
        sheet_name: Sheet名称
        df: 数据框
    """
    # 显示数据表格
    st.subheader(f"📊 {sheet_name}")
    # 将DataFrame转换为字符串类型以避免PyArrow类型转换问题（混合类型：数值和"-"）
    display_df = df.astype(str)
    st.dataframe(display_df, width='stretch', height=420)
    
    # 显示公式注释
    formula_notes = get_formula_notes(sheet_name)
    if formula_notes:
        st.markdown("---")
        st.subheader("📝 公式说明")
        for metric_name, formula in formula_notes.items():
            st.markdown(f"**{metric_name}**: {formula}")
    
    # 趋势图（仅显示数值指标）
    try:
        # DataFrame 格式：第一列是"科目"，其他列是年份（如'2020', '2021'等）
        if "科目" in df.columns:
            # 获取所有年份列（数字字符串或整数）
            year_cols = []
            for col in df.columns:
                if col != "科目":
                    # 尝试转换为年份（可能是字符串"2020"或整数2020）
                    try:
                        year_val = int(float(str(col)))
                        if 2000 <= year_val <= 2100:  # 合理的年份范围
                            year_cols.append(str(year_val))
                    except (ValueError, TypeError):
                        pass
            
            if len(year_cols) >= 2:  # 至少需要2年数据才能画趋势
                st.subheader("📈 趋势图")
                
                # 获取所有科目（指标）
                all_metrics = df["科目"].tolist()
                
                # 用户选择要显示的指标
                selected_metrics = st.multiselect(
                    "选择要可视化的指标",
                    options=all_metrics,
                    default=all_metrics[:min(3, len(all_metrics))],  # 默认选前3个
                    key=f"chart_metrics_{sheet_name}"
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
                            title=f"{sheet_name} - 趋势图"
                        )
                        fig.update_layout(hovermode="x unified")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("💡 所选指标没有可绘制的数值数据")
    except Exception as e:
        st.warning(f"⚠️ 图表生成失败：{str(e)}")
        import traceback
        st.code(traceback.format_exc())

# -----------------------------
# 主界面
# -----------------------------
st.title("📊 财务分析Excel查看器")
st.caption("上传财务分析Excel文件，查看数据表格和图表")
st.markdown("---")

# 侧边栏：文件上传
st.sidebar.header("📁 文件上传")
uploaded_file = st.sidebar.file_uploader(
    "选择财务分析Excel文件",
    type=["xlsx", "xls"],
    help="请上传之前保存的财务分析Excel文件"
)

# 加载按钮
load_btn = st.sidebar.button("🔄 加载文件", type="primary", use_container_width=True)

# 主内容区
if uploaded_file is None and not load_btn:
    st.info("👈 请在左侧上传财务分析Excel文件，然后点击【加载文件】按钮")
else:
    # 如果点击了加载按钮
    if load_btn:
        if uploaded_file is None:
            st.error("❌ 请先上传Excel文件")
        else:
            # 保存上传的文件到临时目录
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, uploaded_file.name)
            
            try:
                # 保存文件
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                # 验证文件格式
                is_valid, error_msg, results = validate_excel_file(temp_file_path)
                
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                else:
                    # 保存到session_state
                    st.session_state['excel_data'] = results
                    st.session_state['excel_file_name'] = uploaded_file.name
                    st.success(f"✅ 文件加载成功！共找到 {len(results)} 个分析sheet")
                    
                    # 清理临时文件
                    try:
                        os.remove(temp_file_path)
                    except:
                        pass
                    
                    # 重新运行以显示数据
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ 处理文件失败：{str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    # 显示已加载的数据
    if 'excel_data' in st.session_state and st.session_state['excel_data']:
        results = st.session_state['excel_data']
        file_name = st.session_state.get('excel_file_name', '未知文件')
        
        st.success(f"📄 已加载文件：{file_name}")
        st.markdown("---")
        
        # Sheet选择器
        sheet = st.selectbox("选择要查看的Sheet", list(results.keys()))
        
        # 显示选中的sheet数据
        if sheet in results:
            display_sheet_data(sheet, results[sheet])
        else:
            st.warning(f"Sheet '{sheet}' 数据不存在")
