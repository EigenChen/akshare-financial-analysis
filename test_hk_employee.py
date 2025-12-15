# -*- coding: utf-8 -*-
"""
测试港股员工数据接口
"""
import akshare as ak
import pandas as pd
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

symbol = "00700"  # 腾讯控股

print("=" * 80)
print("测试港股员工数据接口")
print("=" * 80)

# 1. 测试港股公司概况接口
print("\n1. 测试 stock_hk_company_profile_em（港股公司概况）...")
print("-" * 80)
try:
    profile = ak.stock_hk_company_profile_em(symbol=symbol)
    if profile is not None and not profile.empty:
        print(f"[OK] 获取成功，数据形状: {profile.shape}")
        print(f"列名: {list(profile.columns)}")
        print(f"\n数据内容:")
        print(profile.head(10))
        
        # 查找员工相关字段
        print("\n查找员工相关字段:")
        for col in profile.columns:
            col_str = str(col).lower()
            if '员工' in str(col) or '人数' in str(col) or 'employee' in col_str or 'staff' in col_str:
                print(f"  找到: {col}")
                print(f"    值: {profile[col].iloc[0] if len(profile) > 0 else 'N/A'}")
    else:
        print("[FAIL] 返回空数据")
except Exception as e:
    print(f"[FAIL] 获取失败: {e}")
    import traceback
    traceback.print_exc()

# 2. 测试港股基本信息接口（如果存在）
print("\n2. 测试 stock_individual_basic_info_hk_xq（港股基本信息）...")
print("-" * 80)
try:
    basic_info = ak.stock_individual_basic_info_hk_xq(symbol=symbol)
    if basic_info is not None and not basic_info.empty:
        print(f"[OK] 获取成功，数据形状: {basic_info.shape}")
        print(f"列名: {list(basic_info.columns)}")
        print(f"\n数据内容:")
        print(basic_info.head(10))
        
        # 查找员工相关字段
        print("\n查找员工相关字段:")
        if 'item' in basic_info.columns and 'value' in basic_info.columns:
            for idx, row in basic_info.iterrows():
                item = str(row['item']).lower()
                if '员工' in str(row['item']) or '人数' in str(row['item']) or 'employee' in item or 'staff' in item:
                    print(f"  找到: {row['item']} = {row['value']}")
        else:
            for col in basic_info.columns:
                col_str = str(col).lower()
                if '员工' in str(col) or '人数' in str(col) or 'employee' in col_str or 'staff' in col_str:
                    print(f"  找到: {col}")
                    print(f"    值: {basic_info[col].iloc[0] if len(basic_info) > 0 else 'N/A'}")
    else:
        print("[FAIL] 返回空数据")
except Exception as e:
    print(f"[FAIL] 获取失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 测试港股证券资料接口
print("\n3. 测试 stock_hk_security_profile_em（港股证券资料）...")
print("-" * 80)
try:
    security_profile = ak.stock_hk_security_profile_em(symbol=symbol)
    if security_profile is not None and not security_profile.empty:
        print(f"[OK] 获取成功，数据形状: {security_profile.shape}")
        print(f"列名: {list(security_profile.columns)}")
        print(f"\n数据内容:")
        print(security_profile.head(10))
        
        # 查找员工相关字段
        print("\n查找员工相关字段:")
        for col in security_profile.columns:
            col_str = str(col).lower()
            if '员工' in str(col) or '人数' in str(col) or 'employee' in col_str or 'staff' in col_str:
                print(f"  找到: {col}")
                print(f"    值: {security_profile[col].iloc[0] if len(security_profile) > 0 else 'N/A'}")
    else:
        print("[FAIL] 返回空数据")
except Exception as e:
    print(f"[FAIL] 获取失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 列出所有港股相关接口，查找可能包含员工信息的接口
print("\n4. 搜索所有港股接口，查找可能包含员工信息的接口...")
print("-" * 80)
try:
    all_methods = [m for m in dir(ak) if 'hk' in m.lower()]
    print(f"找到 {len(all_methods)} 个港股相关接口")
    
    # 查找可能包含员工信息的接口
    employee_related = []
    for method_name in all_methods:
        method_lower = method_name.lower()
        if any(keyword in method_lower for keyword in ['profile', 'info', 'basic', 'company', 'individual']):
            employee_related.append(method_name)
    
    print(f"\n可能包含员工信息的接口（{len(employee_related)}个）:")
    for method in employee_related[:10]:  # 只显示前10个
        print(f"  - {method}")
    
    if len(employee_related) > 10:
        print(f"  ... 还有 {len(employee_related) - 10} 个接口")
except Exception as e:
    print(f"[FAIL] 搜索失败: {e}")

print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print("如果以上接口都没有找到员工数据，说明：")
print("1. AKShare港股接口可能不提供员工人数数据")
print("2. 需要从其他数据源获取（如港交所官网、年报PDF等）")
print("3. 或者需要手动提供员工数量CSV文件")

