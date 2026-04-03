# -*- coding: utf-8 -*-
"""
测试2020年年报下载功能
"""
import sys
import importlib.util
import os

def test_2020_download():
    """测试2020年年报下载功能"""
    print("=" * 60)
    print("测试2020年年报下载功能")
    print("=" * 60)

    try:
        # 动态导入PDF下载模块
        spec = importlib.util.spec_from_file_location('pdf_downloader', '08_下载年报PDF.py')
        pdf_module = importlib.util.module_from_spec(spec)
        sys.modules['pdf_downloader'] = pdf_module
        spec.loader.exec_module(pdf_module)

        print("✓ PDF下载模块导入成功")

        # 测试搜索功能（不实际下载）
        print("\n测试1: 搜索2020年年报公告")
        print("-" * 40)

        symbol = "002415"  # 海康威视
        year = 2020

        print(f"股票代码: {symbol}")
        print(f"搜索年份: {year}")

        # 测试搜索功能
        announcements = pdf_module.search_announcements_cninfo(symbol, year)

        if announcements:
            print(f"✓ 找到 {len(announcements)} 个年报公告:")
            for i, ann in enumerate(announcements[:3], 1):  # 只显示前3个
                print(f"  {i}. {ann.get('announcementTitle', 'N/A')[:50]}...")
                print(f"     时间: {ann.get('announcementTime', 'N/A')}")
                print(f"     ID: {ann.get('announcementId', 'N/A')}")
            return True
        else:
            print("❌ 未找到2020年年报公告")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_other_years():
    """测试其他年份作为对比"""
    print("\n" + "=" * 60)
    print("对比测试：其他年份年报搜索")
    print("=" * 60)

    try:
        # 动态导入PDF下载模块
        spec = importlib.util.spec_from_file_location('pdf_downloader', '08_下载年报PDF.py')
        pdf_module = importlib.util.module_from_spec(spec)
        sys.modules['pdf_downloader'] = pdf_module
        spec.loader.exec_module(pdf_module)

        symbol = "002415"  # 海康威视
        test_years = [2019, 2021]

        for year in test_years:
            print(f"\n测试年份: {year}")
            print("-" * 20)

            announcements = pdf_module.search_announcements_cninfo(symbol, year)

            if announcements:
                print(f"✓ {year}年: 找到 {len(announcements)} 个公告")
                ann = announcements[0]
                print(f"  标题: {ann.get('announcementTitle', 'N/A')[:50]}...")
                print(f"  时间: {ann.get('announcementTime', 'N/A')}")
            else:
                print(f"❌ {year}年: 未找到公告")

    except Exception as e:
        print(f"❌ 对比测试失败: {e}")

if __name__ == "__main__":
    # 测试2020年
    success_2020 = test_2020_download()

    # 对比测试其他年份
    test_other_years()

    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    if success_2020:
        print("✅ 2020年年报搜索功能修复成功")
        print("   - 扩大了搜索日期范围（2021-2022年）")
        print("   - 增加了专门的搜索策略")
    else:
        print("❌ 2020年年报搜索仍有问题，需要进一步调试")

    print("\n📝 注意: 此测试只验证搜索功能，实际下载需要网络连接")