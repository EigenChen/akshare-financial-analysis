"""
AKShare 基础学习 - 获取股票列表

学习如何获取上市公司的基本信息，包括：
1. 获取所有A股股票代码和名称
2. 筛选特定板块的股票
3. 获取股票的基本信息
"""

import akshare as ak
import pandas as pd

def get_all_stocks():
    """获取所有A股股票代码和名称"""
    print("=" * 60)
    print("获取所有A股股票列表")
    print("=" * 60)
    
    try:
        # 获取所有A股股票代码和名称
        stock_list = ak.stock_info_a_code_name()
        
        print(f"\n✓ 成功获取 {len(stock_list)} 只A股股票")
        print("\n数据列名：", stock_list.columns.tolist())
        print("\n前10只股票：")
        print(stock_list.head(10))
        
        print("\n数据示例（完整信息）：")
        print(stock_list.iloc[0])
        
        return stock_list
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return None

def search_stock_by_name(stock_list, keyword):
    """根据关键词搜索股票"""
    print(f"\n{'=' * 60}")
    print(f"搜索包含 '{keyword}' 的股票")
    print("=" * 60)
    
    # 在股票名称中搜索
    result = stock_list[stock_list['name'].str.contains(keyword, na=False)]
    
    print(f"\n找到 {len(result)} 只相关股票：")
    print(result)
    
    return result

def get_stock_detail_info(symbol):
    """获取单只股票的详细信息"""
    print(f"\n{'=' * 60}")
    print(f"获取股票 {symbol} 的详细信息")
    print("=" * 60)
    
    try:
        # 获取股票基本信息
        stock_info = ak.stock_individual_info_em(symbol=symbol)
        
        print("\n股票详细信息：")
        print(stock_info)
        
        return stock_info
        
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        return None

def main():
    # 1. 获取所有股票列表
    stock_list = get_all_stocks()
    
    if stock_list is None:
        return
    
    # 2. 搜索示例：搜索包含"银行"的股票
    search_stock_by_name(stock_list, "银行")
    
    # 3. 获取单只股票详细信息示例（使用平安银行）
    # 注意：需要完整的股票代码，如 "000001" 或 "000001.SZ"
    print("\n" + "=" * 60)
    print("提示：要获取单只股票的详细信息，可以使用：")
    print("  stock_info = ak.stock_individual_info_em(symbol='000001')")
    print("=" * 60)
    
    # 保存股票列表到CSV（可选）
    save_option = input("\n是否保存股票列表到 CSV 文件？(y/n): ")
    if save_option.lower() == 'y':
        filename = "stock_list.csv"
        stock_list.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✓ 已保存到 {filename}")

if __name__ == "__main__":
    main()

