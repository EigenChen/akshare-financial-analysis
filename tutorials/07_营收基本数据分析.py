"""
财务分析

从三大报表中提取和计算财务相关指标，包括营收基本数据和费用构成数据
"""

import akshare as ak
import pandas as pd
import os
import time
from datetime import datetime

def get_symbol_name(symbol):
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
    except:
        return symbol.replace('.SZ', '').replace('.SH', '')

def get_annual_data(symbol, start_year=2015, end_year=2024):
    """
    获取指定年份范围的年报数据
    
    参数:
        symbol: 股票代码
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        包含利润表、现金流量表数据的字典
    """
    # 确保有交易所后缀
    symbol_with_suffix = symbol
    if '.' not in symbol:
        if symbol.startswith(('000', '001', '002', '300')):
            symbol_with_suffix = symbol + '.SZ'
        elif symbol.startswith(('600', '601', '603', '605', '688')):
            symbol_with_suffix = symbol + '.SH'
        else:
            symbol_with_suffix = symbol + '.SZ'
    
    results = {
        'profit': None,
        'cash_flow': None
    }
    
    try:
        # 获取利润表
        print("正在获取利润表数据...")
        profit = ak.stock_profit_sheet_by_report_em(symbol=symbol_with_suffix)
        if profit is not None and not profit.empty:
            results['profit'] = profit
            print(f"✓ 利润表数据获取成功，共 {len(profit)} 条记录")
        
        # 获取现金流量表
        print("正在获取现金流量表数据...")
        cash_flow = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol_with_suffix)
        if cash_flow is not None and not cash_flow.empty:
            results['cash_flow'] = cash_flow
            print(f"✓ 现金流量表数据获取成功，共 {len(cash_flow)} 条记录")
        
    except Exception as e:
        print(f"✗ 获取数据失败: {e}")
        import traceback
        traceback.print_exc()
    
    return results

def extract_year_data(df, year, date_col_name='REPORT_DATE'):
    """
    从数据框中提取指定年份的数据
    
    参数:
        df: 数据框
        year: 年份，如 2024
        date_col_name: 报告期列名
    
    返回:
        该年份的数据行（DataFrame），如果没有则返回None
    """
    if df is None or df.empty:
        return None
    
    # 查找报告期列
    date_col = None
    for col in df.columns:
        if date_col_name in col or '报告期' in col:
            date_col = col
            break
    
    if date_col is None:
        return None
    
    # 筛选指定年份的年报数据（12-31）
    year_str = str(year)
    filtered = df[
        (df[date_col].astype(str).str.contains(year_str, na=False)) &
        (df[date_col].astype(str).str.contains('12-31', na=False))
    ]
    
    if not filtered.empty:
        return filtered.iloc[-1]  # 取最后一条（最新的）
    
    return None

def get_value_from_row(row, column_name, default="-", return_numeric=True):
    """
    从数据行中获取指定列的值，转换为数值（亿元）
    
    参数:
        row: 数据行
        column_name: 列名
        default: 默认值，如果数据缺失返回此值（通常为 "-"）
        return_numeric: 是否返回数值，False时返回字符串（用于缺失数据）
    
    返回:
        数值（亿元），保留2位小数；如果数据缺失，返回 default（通常是 "-"）
    """
    if row is None:
        return default
    
    if column_name not in row.index:
        return default
    
    value = row[column_name]
    try:
        num_value = float(value)
        if pd.isna(num_value):
            return default
        # 转换为亿元
        if return_numeric:
            return round(num_value / 100000000, 2)
        else:
            return str(round(num_value / 100000000, 2))
    except (ValueError, TypeError):
        return default

def calculate_revenue_metrics(symbol, start_year, end_year):
    """
    计算营收基本数据指标
    
    参数:
        symbol: 股票代码
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        包含所有指标数据的DataFrame
    """
    print("=" * 80)
    print(f"开始计算 {symbol} 的营收基本数据（{start_year}-{end_year}）")
    print("=" * 80)
    
    # 获取数据
    data = get_annual_data(symbol, start_year, end_year)
    
    if data['profit'] is None or data['cash_flow'] is None:
        print("✗ 数据获取不完整，无法计算")
        return None
    
    # 准备结果数据
    metrics = {
        '科目': [],
    }
    
    # 初始化年份列
    for year in range(start_year, end_year + 1):
        metrics[str(year)] = []
    
    # 先初始化所有科目名称
    metrics['科目'] = [
        '收入（亿元）',
        '归母净利润（亿元）',
        '净利润率（%）',
        '扣非净利润（亿元）',
        '经营净现金流（亿元）',
        'CAPEX（亿元）',
        '自由现金流（亿元）',
        '扣非/净利润（%）',
        '经营现金流/净利润（%）',
        '金融利润（亿元）',
        '经营利润（亿元）',
        '经营利润/归母利润（%）',
        '金融利润/归母利润（%）'
    ]
    
    # 初始化所有年份的数据列表（默认值为 "-" 表示数据缺失）
    for year in range(start_year, end_year + 1):
        for _ in range(len(metrics['科目'])):
            metrics[str(year)].append("-")
    
    # 逐年计算指标
    for year in range(start_year, end_year + 1):
        print(f"\n处理 {year} 年数据...")
        
        # 获取该年份的数据
        profit_row = extract_year_data(data['profit'], year)
        cash_flow_row = extract_year_data(data['cash_flow'], year)
        
        if profit_row is None:
            print(f"  ⚠ {year} 年利润表数据缺失，使用默认值0")
        if cash_flow_row is None:
            print(f"  ⚠ {year} 年现金流量表数据缺失，使用默认值0")
        
        year_idx = year - start_year
        
        # 检查数据是否可用
        data_available = (profit_row is not None) and (cash_flow_row is not None)
        
        if not data_available:
            print(f"  ⚠ {year} 年数据缺失，该年份所有指标显示为 '-'")
            # 所有指标保持为 "-"（已在初始化时设置）
            continue
        
        # 1. 收入（亿元）- 营业收入
        revenue = get_value_from_row(profit_row, 'OPERATE_INCOME', "-")
        if revenue == "-":
            print(f"  ⚠ {year} 年营业收入数据缺失")
            continue  # 如果基础数据缺失，跳过该年份
        metrics[str(year)][0] = revenue
        
        # 2. 归母净利润（亿元）
        parent_net_profit = get_value_from_row(profit_row, 'PARENT_NETPROFIT', "-")
        if parent_net_profit == "-":
            print(f"  ⚠ {year} 年归母净利润数据缺失")
            continue
        metrics[str(year)][1] = parent_net_profit
        
        # 3. 净利润率（%）
        net_profit_margin = round((parent_net_profit / revenue * 100) if revenue != 0 else 0, 2)
        metrics[str(year)][2] = net_profit_margin
        
        # 4. 扣非净利润（亿元）
        deduct_parent_net_profit = get_value_from_row(profit_row, 'DEDUCT_PARENT_NETPROFIT', "-")
        metrics[str(year)][3] = deduct_parent_net_profit
        
        # 5. 经营净现金流（亿元）
        operate_cash_flow = get_value_from_row(cash_flow_row, 'NETCASH_OPERATE', "-")
        metrics[str(year)][4] = operate_cash_flow
        
        # 6. CAPEX（亿元）- 购建固定资产、无形资产和其他长期资产支付的现金
        capex = get_value_from_row(cash_flow_row, 'CONSTRUCT_LONG_ASSET', "-")
        metrics[str(year)][5] = capex
        
        # 7. 自由现金流（亿元）= 经营净现金流 - CAPEX
        if operate_cash_flow != "-" and capex != "-":
            free_cash_flow = round(operate_cash_flow - capex, 2)
            metrics[str(year)][6] = free_cash_flow
        else:
            metrics[str(year)][6] = "-"
        
        # 8. 扣非/净利润（%）
        if deduct_parent_net_profit != "-" and parent_net_profit != "-" and parent_net_profit != 0:
            deduct_net_ratio = round((deduct_parent_net_profit / parent_net_profit * 100), 2)
            metrics[str(year)][7] = deduct_net_ratio
        else:
            metrics[str(year)][7] = "-"
        
        # 9. 经营现金流/净利润（%）
        if operate_cash_flow != "-" and parent_net_profit != "-" and parent_net_profit != 0:
            cash_profit_ratio = round((operate_cash_flow / parent_net_profit * 100), 2)
            metrics[str(year)][8] = cash_profit_ratio
        else:
            metrics[str(year)][8] = "-"
        
        # 10. 金融利润（亿元）= 公允价值变动收益 + 投资收益
        # 注意：如果科目不存在或为空，可能返回0或"-"，需要统一处理
        fairvalue_change = get_value_from_row(profit_row, 'FAIRVALUE_CHANGE_INCOME', 0)
        invest_income = get_value_from_row(profit_row, 'INVEST_INCOME', 0)
        # 如果值为 "-" 或 None，视为0；否则计算
        if fairvalue_change == "-" or fairvalue_change is None:
            fairvalue_change = 0
        if invest_income == "-" or invest_income is None:
            invest_income = 0
        financial_profit = round(fairvalue_change + invest_income, 2)
        metrics[str(year)][9] = financial_profit
        
        # 11. 经营利润（亿元）= 归母净利润 - 金融利润
        if parent_net_profit != "-" and metrics[str(year)][9] != "-":
            operate_profit = round(parent_net_profit - metrics[str(year)][9], 2)
            metrics[str(year)][10] = operate_profit
        else:
            metrics[str(year)][10] = "-"
        
        # 12. 经营利润/归母利润（%）
        if metrics[str(year)][10] != "-" and parent_net_profit != "-" and parent_net_profit != 0:
            operate_profit_ratio = round((metrics[str(year)][10] / parent_net_profit * 100), 2)
            metrics[str(year)][11] = operate_profit_ratio
        else:
            metrics[str(year)][11] = "-"
        
        # 13. 金融利润（%）- 金融利润占归母净利润的比例
        if metrics[str(year)][9] != "-" and parent_net_profit != "-" and parent_net_profit != 0:
            financial_profit_ratio = round((metrics[str(year)][9] / parent_net_profit * 100), 2)
            metrics[str(year)][12] = financial_profit_ratio
        else:
            metrics[str(year)][12] = "-"
        
        print(f"  ✓ {year} 年数据计算完成")
    
    # 创建DataFrame
    result_df = pd.DataFrame(metrics)
    
    return result_df

def calculate_expense_metrics(symbol, start_year, end_year):
    """
    计算费用构成指标
    
    参数:
        symbol: 股票代码
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        包含所有费用指标数据的DataFrame
    """
    print("\n" + "=" * 80)
    print(f"开始计算 {symbol} 的费用构成数据（{start_year}-{end_year}）")
    print("=" * 80)
    
    # 获取数据
    data = get_annual_data(symbol, start_year, end_year)
    
    if data['profit'] is None:
        print("✗ 利润表数据获取不完整，无法计算")
        return None
    
    # 准备结果数据
    metrics = {
        '科目': [],
    }
    
    # 初始化年份列
    for year in range(start_year, end_year + 1):
        metrics[str(year)] = []
    
    # 先初始化所有科目名称
    metrics['科目'] = [
        '毛利率（%）',
        '净利率（%）',
        '研发费用（亿元）',
        '管理费用（亿元）',
        '管理研发费用（亿元）',
        '销售费用（亿元）',
        '财务费用（亿元）',
        '期间费用合计（亿元）',
        '销售费用率（%）',
        '研发费用率（%）',
        '管理费用率（%）',
        '管理研发费用率（%）',
        '期间费用率（%）',
        '毛利率-净利润率（%）'
    ]
    
    # 初始化所有年份的数据列表（默认值为 "-" 表示数据缺失）
    for year in range(start_year, end_year + 1):
        for _ in range(len(metrics['科目'])):
            metrics[str(year)].append("-")
    
    # 逐年计算指标
    for year in range(start_year, end_year + 1):
        print(f"\n处理 {year} 年数据...")
        
        # 获取该年份的数据
        profit_row = extract_year_data(data['profit'], year)
        
        if profit_row is None:
            print(f"  ⚠ {year} 年利润表数据缺失，该年份所有指标显示为 '-'")
            continue
        
        # 1. 收入（亿元）- 营业收入（用于计算各种比率）
        revenue = get_value_from_row(profit_row, 'OPERATE_INCOME', "-")
        if revenue == "-":
            print(f"  ⚠ {year} 年营业收入数据缺失")
            continue
        
        # 2. 营业成本（亿元）- 用于计算毛利率
        operate_cost = get_value_from_row(profit_row, 'OPERATE_COST', "-")
        
        # 3. 归母净利润（亿元）- 用于计算净利率
        parent_net_profit = get_value_from_row(profit_row, 'PARENT_NETPROFIT', "-")
        if parent_net_profit == "-":
            print(f"  ⚠ {year} 年归母净利润数据缺失")
            continue
        
        # 1. 毛利率（%）= (营业收入 - 营业成本) / 营业收入 * 100
        if revenue != "-" and operate_cost != "-" and revenue != 0:
            gross_margin = round(((revenue - operate_cost) / revenue * 100), 2)
            metrics[str(year)][0] = gross_margin
        else:
            metrics[str(year)][0] = "-"
        
        # 2. 净利率（%）= 归母净利润 / 营业收入 * 100
        if revenue != "-" and parent_net_profit != "-" and revenue != 0:
            net_margin = round((parent_net_profit / revenue * 100), 2)
            metrics[str(year)][1] = net_margin
        else:
            metrics[str(year)][1] = "-"
        
        # 3. 研发费用（亿元）
        research_expense = get_value_from_row(profit_row, 'RESEARCH_EXPENSE', "-")
        metrics[str(year)][2] = research_expense
        
        # 4. 管理费用（亿元）
        manage_expense = get_value_from_row(profit_row, 'MANAGE_EXPENSE', "-")
        metrics[str(year)][3] = manage_expense
        
        # 5. 管理研发费用（亿元）= 管理费用 + 研发费用
        if manage_expense != "-" and research_expense != "-":
            manage_research_expense = round(manage_expense + research_expense, 2)
            metrics[str(year)][4] = manage_research_expense
        elif manage_expense != "-" and research_expense == "-":
            # 如果研发费用缺失，只使用管理费用
            metrics[str(year)][4] = manage_expense
        elif manage_expense == "-" and research_expense != "-":
            # 如果管理费用缺失，只使用研发费用
            metrics[str(year)][4] = research_expense
        else:
            metrics[str(year)][4] = "-"
        
        # 6. 销售费用（亿元）
        sale_expense = get_value_from_row(profit_row, 'SALE_EXPENSE', "-")
        metrics[str(year)][5] = sale_expense
        
        # 7. 财务费用（亿元）
        finance_expense = get_value_from_row(profit_row, 'FINANCE_EXPENSE', "-")
        metrics[str(year)][6] = finance_expense
        
        # 8. 期间费用合计（亿元）= 销售费用 + 研发费用 + 管理费用 + 财务费用
        period_expenses = [sale_expense, research_expense, manage_expense, finance_expense]
        # 检查是否有缺失值
        if all(exp != "-" for exp in period_expenses):
            period_expense_total = round(sum(period_expenses), 2)
            metrics[str(year)][7] = period_expense_total
        else:
            # 如果有缺失值，尝试计算非缺失值的和
            valid_expenses = [exp for exp in period_expenses if exp != "-"]
            if valid_expenses:
                period_expense_total = round(sum(valid_expenses), 2)
                metrics[str(year)][7] = period_expense_total
            else:
                metrics[str(year)][7] = "-"
        
        # 9. 销售费用率（%）= 销售费用 / 营业收入 * 100
        if sale_expense != "-" and revenue != "-" and revenue != 0:
            sale_expense_ratio = round((sale_expense / revenue * 100), 2)
            metrics[str(year)][8] = sale_expense_ratio
        else:
            metrics[str(year)][8] = "-"
        
        # 10. 研发费用率（%）= 研发费用 / 营业收入 * 100
        if research_expense != "-" and revenue != "-" and revenue != 0:
            research_expense_ratio = round((research_expense / revenue * 100), 2)
            metrics[str(year)][9] = research_expense_ratio
        else:
            metrics[str(year)][9] = "-"
        
        # 11. 管理费用率（%）= 管理费用 / 营业收入 * 100
        if manage_expense != "-" and revenue != "-" and revenue != 0:
            manage_expense_ratio = round((manage_expense / revenue * 100), 2)
            metrics[str(year)][10] = manage_expense_ratio
        else:
            metrics[str(year)][10] = "-"
        
        # 12. 管理研发费用率（%）= 管理研发费用 / 营业收入 * 100
        if metrics[str(year)][4] != "-" and revenue != "-" and revenue != 0:
            manage_research_ratio = round((metrics[str(year)][4] / revenue * 100), 2)
            metrics[str(year)][11] = manage_research_ratio
        else:
            metrics[str(year)][11] = "-"
        
        # 13. 期间费用率（%）= 期间费用合计 / 营业收入 * 100
        if metrics[str(year)][7] != "-" and revenue != "-" and revenue != 0:
            period_expense_ratio = round((metrics[str(year)][7] / revenue * 100), 2)
            metrics[str(year)][12] = period_expense_ratio
        else:
            metrics[str(year)][12] = "-"
        
        # 14. 毛利率-净利润率（%）= 毛利率 - 净利润率
        if metrics[str(year)][0] != "-" and metrics[str(year)][1] != "-":
            gross_net_diff = round(metrics[str(year)][0] - metrics[str(year)][1], 2)
            metrics[str(year)][13] = gross_net_diff
        else:
            metrics[str(year)][13] = "-"
        
        print(f"  ✓ {year} 年数据计算完成")
    
    # 创建DataFrame
    result_df = pd.DataFrame(metrics)
    
    return result_df

def save_to_excel(df, symbol, company_name, start_year, end_year, sheet_name, output_dir="output", timestamp=None):
    """
    保存数据到Excel文件
    
    参数:
        df: 数据框
        symbol: 股票代码
        company_name: 公司名称
        start_year: 起始年份
        end_year: 结束年份
        sheet_name: Sheet名称
        output_dir: 输出目录
        timestamp: 时间戳（格式：YYYYMMDDHHmmss），如果为None则自动生成
    """
    if df is None or df.empty:
        print(f"✗ 没有数据可保存到 {sheet_name}")
        return None
    
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 生成时间戳（如果未提供）
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 生成文件名
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    filename = f"{company_name}_{start_year}-{end_year}_财务分析_{timestamp}.xlsx"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # 如果文件已存在，追加sheet；否则创建新文件
        if os.path.exists(filepath):
            # 确保之前的文件句柄已关闭，等待一小段时间
            time.sleep(0.1)
            # 使用 openpyxl 加载工作簿，确保文件已关闭
            from openpyxl import load_workbook
            try:
                # 尝试加载工作簿，如果文件被占用会抛出异常
                wb = load_workbook(filepath)
                wb.close()
            except:
                # 如果加载失败，再等待一下
                time.sleep(0.2)
            
            # 追加模式写入
            with pd.ExcelWriter(filepath, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"✓ {sheet_name} 已追加/更新到现有Excel文件")
        else:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"✓ 已创建新Excel文件")
        
        # 确保文件句柄已关闭
        time.sleep(0.1)
        
        print(f"  文件路径: {filepath}")
        print(f"  Sheet名称: {sheet_name}")
        return filepath
        
    except Exception as e:
        print(f"\n✗ 保存Excel文件失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    # 指定股票代码和年份范围
    symbol = "603486"  # 可以修改为其他股票代码
    start_year = 2013  # 起始年份
    end_year = 2021     # 结束年份
    
    # 生成时间戳（用于文件名，确保所有sheet保存到同一个文件）
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # 获取股票名称
    company_name = get_symbol_name(symbol)
    print(f"股票代码: {symbol}")
    print(f"公司名称: {company_name}")
    print(f"分析年份: {start_year}-{end_year}\n")
    
    # 计算营收基本数据
    result_df = calculate_revenue_metrics(symbol, start_year, end_year)
    
    if result_df is not None and not result_df.empty:
        # 打印到控制台
        print("\n" + "=" * 80)
        print(f"营收基本数据（{start_year}-{end_year}）")
        print("=" * 80)
        print(result_df.to_string(index=False))
        
        # 保存到Excel
        save_to_excel(result_df, symbol, company_name, start_year, end_year, '营收基本数据', timestamp=timestamp)
    else:
        print("\n✗ 未能生成营收基本数据")
    
    # 计算费用构成数据
    expense_df = calculate_expense_metrics(symbol, start_year, end_year)
    
    if expense_df is not None and not expense_df.empty:
        # 打印到控制台
        print("\n" + "=" * 80)
        print(f"费用构成数据（{start_year}-{end_year}）")
        print("=" * 80)
        print(expense_df.to_string(index=False))
        
        # 保存到Excel（追加到同一个文件）
        save_to_excel(expense_df, symbol, company_name, start_year, end_year, '费用构成', timestamp=timestamp)
    else:
        print("\n✗ 未能生成费用构成数据")
    
    # 最终提示
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    filename = f"{company_name}_{start_year}-{end_year}_财务分析_{timestamp}.xlsx"
    filepath = os.path.join("output", filename)
    if os.path.exists(filepath):
        print(f"\n{'='*80}")
        print(f"✓ 所有数据已保存到: {filepath}")
        print(f"{'='*80}")

if __name__ == "__main__":
    main()

