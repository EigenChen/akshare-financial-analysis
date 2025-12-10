"""
测试获取员工人数的接口

测试不同的akshare接口，查看哪个能获取到员工人数
"""

import akshare as ak
import pandas as pd

def test_stock_individual_basic_info_xq(symbol):
    """
    测试 stock_individual_basic_info_xq 接口
    """
    print("=" * 80)
    print(f"测试接口: stock_individual_basic_info_xq")
    print(f"股票代码: {symbol}")
    print("=" * 80)
    
    try:
        symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
        basic_info = ak.stock_individual_basic_info_xq(symbol=symbol_clean)
        
        if basic_info is not None and not basic_info.empty:
            print(f"\n✓ 成功获取数据")
            print(f"数据形状: {basic_info.shape}")
            print(f"列名: {list(basic_info.columns)}")
            
            # 显示所有数据
            print(f"\n完整数据:")
            print(basic_info.to_string())
            
            # 查找员工人数
            if 'item' in basic_info.columns and 'value' in basic_info.columns:
                staff_num_row = basic_info[basic_info['item'] == 'staff_num']
                if not staff_num_row.empty:
                    print(f"\n✓ 找到员工人数 (staff_num): {staff_num_row.iloc[0]['value']}")
                else:
                    print(f"\n✗ 未找到 staff_num 字段")
            
            return basic_info
        else:
            print("✗ 返回空数据")
            return None
            
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_stock_individual_info_em(symbol):
    """
    测试 stock_individual_info_em 接口
    """
    print("\n" + "=" * 80)
    print(f"测试接口: stock_individual_info_em")
    print(f"股票代码: {symbol}")
    print("=" * 80)
    
    try:
        symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
        stock_info = ak.stock_individual_info_em(symbol=symbol_clean)
        
        if stock_info is not None and not stock_info.empty:
            print(f"\n✓ 成功获取数据")
            print(f"数据形状: {stock_info.shape}")
            print(f"列名: {list(stock_info.columns)}")
            
            # 显示所有数据
            print(f"\n完整数据:")
            print(stock_info.to_string())
            
            # 查找员工人数相关字段
            print(f"\n查找员工人数相关字段:")
            for col in stock_info.columns:
                col_str = str(col).lower()
                if '员工' in str(col) or '人数' in str(col) or 'employee' in col_str or 'staff' in col_str:
                    print(f"  找到: {col} = {stock_info[col].iloc[0] if len(stock_info) > 0 else 'N/A'}")
            
            return stock_info
        else:
            print("✗ 返回空数据")
            return None
            
    except Exception as e:
        print(f"✗ 获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    # 测试股票代码
    symbol = "603486"  # 科沃斯
    
    print("开始测试获取员工人数的接口...\n")
    
    # 测试接口1
    result1 = test_stock_individual_basic_info_xq(symbol)
    
    # 测试接口2
    result2 = test_stock_individual_info_em(symbol)
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    main()

