"""
AKShare 基础学习 - 验证安装

这个脚本用于验证 AKShare 是否正确安装，并展示基本的数据获取方法。
"""

import akshare as ak
import pandas as pd

def main():
    print("=" * 60)
    print("AKShare 安装验证")
    print("=" * 60)
    
    # 1. 检查 AKShare 版本
    try:
        print(f"\n✓ AKShare 版本: {ak.__version__}")
    except:
        print("\n✗ 无法获取版本信息")
        return
    
    # 2. 测试获取股票基本信息（简单接口，用于验证）
    print("\n正在测试数据获取功能...")
    try:
        # 获取股票代码和名称列表（这是一个轻量级的接口）
        stock_info = ak.stock_info_a_code_name()
        print(f"✓ 成功获取股票列表，共 {len(stock_info)} 只股票")
        print("\n前5只股票信息：")
        print(stock_info.head())
        
        print("\n" + "=" * 60)
        print("✓ AKShare 安装成功，可以正常使用！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 数据获取失败: {e}")
        print("请检查网络连接或 AKShare 安装是否正确")
        return

if __name__ == "__main__":
    main()

