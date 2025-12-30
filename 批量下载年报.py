# -*- coding: utf-8 -*-
"""
批量下载年报PDF工具

功能：
1. 从巨潮资讯网站下载指定企业的年报PDF
2. 支持指定股票代码、开始年份、结束年份和下载目录
3. 自动批量下载多年年报

使用方法：
    python 批量下载年报.py --symbol 600900 --start_year 2020 --end_year 2024 --save_dir 年报PDF

或者直接运行脚本，按提示输入参数
"""

import os
import sys
import argparse
from typing import Optional

# 导入现有的下载功能
# 注意：Python模块名不能以数字开头，所以使用importlib动态导入
import importlib.util

# 动态导入08_下载年报PDF.py模块
spec = importlib.util.spec_from_file_location("download_report", "08_下载年报PDF.py")
download_report = importlib.util.module_from_spec(spec)
sys.modules["download_report"] = download_report
spec.loader.exec_module(download_report)

# 获取需要的函数
download_annual_report = download_report.download_annual_report
search_announcements_cninfo = download_report.search_announcements_cninfo


def batch_download_reports(symbol: str, start_year: int, end_year: int, save_dir: str = "年报PDF") -> dict:
    """
    批量下载年报PDF
    
    参数:
        symbol: 股票代码（6位数字，如 600900）
        start_year: 开始年份
        end_year: 结束年份
        save_dir: 下载目录
    
    返回:
        字典，格式为 {年份: 文件路径}，失败的年份值为None
    """
    results = {}
    
    # 清理股票代码（移除.SZ/.SH后缀）
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    
    print("=" * 80)
    print(f"开始批量下载年报")
    print(f"股票代码: {symbol_clean}")
    print(f"年份范围: {start_year} - {end_year}")
    print(f"保存目录: {save_dir}")
    print("=" * 80)
    print()
    
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)
    
    # 遍历年份
    for year in range(start_year, end_year + 1):
        print(f"[{year}年] 正在下载...")
        
        try:
            # 下载年报
            file_path = download_annual_report(symbol_clean, year, save_dir, source="cninfo")
            
            if file_path and os.path.exists(file_path):
                results[year] = file_path
                print(f"  ✓ 下载成功: {file_path}")
            else:
                results[year] = None
                print(f"  ✗ 下载失败: 未找到 {year} 年年报")
        
        except Exception as e:
            results[year] = None
            print(f"  ✗ 下载失败: {str(e)}")
        
        print()  # 空行分隔
    
    # 统计结果
    print("=" * 80)
    print("下载完成统计")
    print("=" * 80)
    success_count = sum(1 for v in results.values() if v is not None)
    total_count = len(results)
    print(f"成功: {success_count}/{total_count}")
    print(f"失败: {total_count - success_count}/{total_count}")
    print()
    
    # 显示详细结果
    if success_count > 0:
        print("成功下载的文件:")
        for year, file_path in results.items():
            if file_path:
                print(f"  {year}年: {file_path}")
        print()
    
    if success_count < total_count:
        print("未成功下载的年份:")
        for year, file_path in results.items():
            if file_path is None:
                print(f"  {year}年")
        print()
    
    return results


def main():
    """主函数：支持命令行参数和交互式输入"""
    parser = argparse.ArgumentParser(description='批量下载上市公司年报PDF')
    parser.add_argument('--symbol', type=str, help='股票代码（6位数字，如 600900）')
    parser.add_argument('--start_year', type=int, help='开始年份（如 2020）')
    parser.add_argument('--end_year', type=int, help='结束年份（如 2024）')
    parser.add_argument('--save_dir', type=str, default='年报PDF', help='下载目录（默认：年报PDF）')
    
    args = parser.parse_args()
    
    # 如果命令行参数不完整，使用交互式输入
    if not args.symbol or not args.start_year or not args.end_year:
        print("=" * 80)
        print("批量下载年报PDF工具")
        print("=" * 80)
        print()
        
        # 输入股票代码
        if not args.symbol:
            symbol = input("请输入股票代码（6位数字，如 600900）: ").strip()
        else:
            symbol = args.symbol
        
        # 输入开始年份
        if not args.start_year:
            start_year_str = input("请输入开始年份（如 2020）: ").strip()
            try:
                start_year = int(start_year_str)
            except ValueError:
                print("错误：年份必须是数字")
                return
        else:
            start_year = args.start_year
        
        # 输入结束年份
        if not args.end_year:
            end_year_str = input("请输入结束年份（如 2024）: ").strip()
            try:
                end_year = int(end_year_str)
            except ValueError:
                print("错误：年份必须是数字")
                return
        else:
            end_year = args.end_year
        
        # 输入保存目录
        if not args.save_dir or args.save_dir == '年报PDF':
            save_dir = input("请输入下载目录（直接回车使用默认：年报PDF）: ").strip()
            if not save_dir:
                save_dir = "年报PDF"
        else:
            save_dir = args.save_dir
    else:
        symbol = args.symbol
        start_year = args.start_year
        end_year = args.end_year
        save_dir = args.save_dir
    
    # 验证输入
    if not symbol:
        print("错误：股票代码不能为空")
        return
    
    if start_year > end_year:
        print("错误：开始年份不能大于结束年份")
        return
    
    if start_year < 2000 or end_year > 2035:
        print("错误：年份范围不合理（应在2000-2035之间）")
        return
    
    # 执行批量下载
    try:
        results = batch_download_reports(symbol, start_year, end_year, save_dir)
        
        # 返回退出码
        success_count = sum(1 for v in results.values() if v is not None)
        if success_count == 0:
            sys.exit(1)  # 全部失败
        elif success_count < len(results):
            sys.exit(2)  # 部分成功
        else:
            sys.exit(0)  # 全部成功
    
    except KeyboardInterrupt:
        print("\n\n用户中断下载")
        sys.exit(130)
    except Exception as e:
        print(f"\n错误：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
