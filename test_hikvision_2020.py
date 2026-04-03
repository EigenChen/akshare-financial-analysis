# -*- coding: utf-8 -*-
"""
测试海康威视2020年报的实际URL下载
"""
import sys
import importlib.util

def test_hikvision_2020():
    """测试海康威视2020年报下载"""
    print("=" * 70)
    print("Testing Hikvision 2020 Annual Report Download")
    print("=" * 70)

    # 实际的2020年报URL
    url = "https://www.cninfo.com.cn/new/disclosure/detail?plate=szse&orgId=9900012688&stockCode=002415&announcementId=1209712163&announcementTime=2021-04-17"

    print("URL Parameters Analysis:")
    print(f"  plate: szse")
    print(f"  orgId: 9900012688")  # 注意：这与我们预期的格式不同
    print(f"  stockCode: 002415")
    print(f"  announcementId: 1209712163")
    print(f"  announcementTime: 2021-04-17")  # 确实是2021年4月17日发布

    print("\nKey Findings:")
    print("  1. 发布日期: 2021-04-17 (在我们的搜索范围内)")
    print("  2. orgId格式: 9900012688 (不是我们预期的gssh002415格式)")

    try:
        # 导入PDF下载模块
        spec = importlib.util.spec_from_file_location('pdf_downloader', '08_下载年报PDF.py')
        pdf_module = importlib.util.module_from_spec(spec)
        sys.modules['pdf_downloader'] = pdf_module
        spec.loader.exec_module(pdf_module)

        print("\n" + "=" * 70)
        print("Testing Direct URL Download")
        print("=" * 70)

        # 测试直接URL下载
        result = pdf_module.download_from_cninfo_url(url, save_dir="测试下载")

        if result:
            print(f"[SUCCESS] Download successful: {result}")

            # 检查文件大小
            import os
            if os.path.exists(result):
                size = os.path.getsize(result) / (1024 * 1024)  # MB
                print(f"[INFO] File size: {size:.2f} MB")
        else:
            print("[FAIL] Download failed")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

def analyze_search_failure():
    """分析为什么搜索API没找到这个年报"""
    print("\n" + "=" * 70)
    print("Analyzing Why Search API Failed")
    print("=" * 70)

    print("Possible reasons:")
    print("1. orgId format mismatch:")
    print("   Expected: gssh002415")
    print("   Actual:   9900012688")

    print("\n2. Date range issue:")
    print("   Our search: 2021-01-01~2022-12-31")
    print("   Actual date: 2021-04-17 (should be in range)")

    print("\n3. Search keyword issue:")
    print("   Our keywords: '002415', '002415 2020年'")
    print("   Might not match the exact title format")

    print("\n4. Category classification:")
    print("   The report might be in a different category")
    print("   or have special classification due to delay")

def test_improved_search():
    """测试改进的搜索策略"""
    print("\n" + "=" * 70)
    print("Testing Improved Search Strategy")
    print("=" * 70)

    try:
        # 导入PDF下载模块
        spec = importlib.util.spec_from_file_location('pdf_downloader', '08_下载年报PDF.py')
        pdf_module = importlib.util.module_from_spec(spec)
        sys.modules['pdf_downloader'] = pdf_module
        spec.loader.exec_module(pdf_module)

        # 使用已知的announcementId测试下载
        print("Testing download with known announcementId...")

        result = pdf_module.download_from_cninfo_with_id(
            symbol="002415",
            announcement_id="1209712163",
            announcement_time="2021-04-17",
            save_dir="测试下载2"
        )

        if result:
            print(f"[SUCCESS] Download with ID successful: {result}")
        else:
            print("[FAIL] Download with ID failed")

    except Exception as e:
        print(f"[ERROR] Improved search test failed: {e}")

if __name__ == "__main__":
    test_hikvision_2020()
    analyze_search_failure()
    test_improved_search()