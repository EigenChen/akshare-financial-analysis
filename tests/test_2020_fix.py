# -*- coding: utf-8 -*-
"""
Test 2020 annual report download functionality
"""
import sys
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_2020_download():
    """Test 2020 annual report download functionality"""
    print("=" * 60)
    print("Testing 2020 Annual Report Download")
    print("=" * 60)

    try:
        # Import PDF download module
        spec = importlib.util.spec_from_file_location('pdf_downloader', ROOT / 'core/a_share/annual_report_downloader.py')
        pdf_module = importlib.util.module_from_spec(spec)
        sys.modules['pdf_downloader'] = pdf_module
        spec.loader.exec_module(pdf_module)

        print("[OK] PDF download module imported successfully")

        # Test search functionality
        print("\nTest 1: Search 2020 annual reports")
        print("-" * 40)

        symbol = "002415"  # Hikvision
        year = 2020

        print(f"Stock code: {symbol}")
        print(f"Search year: {year}")

        # Test search function
        announcements = pdf_module.search_announcements_cninfo(symbol, year)

        if announcements:
            print(f"[OK] Found {len(announcements)} annual report announcements:")
            for i, ann in enumerate(announcements[:3], 1):
                title = ann.get('announcementTitle', 'N/A')
                time_str = ann.get('announcementTime', 'N/A')
                ann_id = ann.get('announcementId', 'N/A')
                print(f"  {i}. {title[:50]}...")
                print(f"     Time: {time_str}")
                print(f"     ID: {ann_id}")
            return True
        else:
            print("[FAIL] No 2020 annual reports found")
            return False

    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_other_years():
    """Test other years for comparison"""
    print("\n" + "=" * 60)
    print("Comparison Test: Other Years")
    print("=" * 60)

    try:
        # Import PDF download module
        spec = importlib.util.spec_from_file_location('pdf_downloader', ROOT / 'core/a_share/annual_report_downloader.py')
        pdf_module = importlib.util.module_from_spec(spec)
        sys.modules['pdf_downloader'] = pdf_module
        spec.loader.exec_module(pdf_module)

        symbol = "002415"  # Hikvision
        test_years = [2019, 2021]

        for year in test_years:
            print(f"\nTesting year: {year}")
            print("-" * 20)

            announcements = pdf_module.search_announcements_cninfo(symbol, year)

            if announcements:
                print(f"[OK] {year}: Found {len(announcements)} announcements")
                ann = announcements[0]
                title = ann.get('announcementTitle', 'N/A')
                time_str = ann.get('announcementTime', 'N/A')
                print(f"  Title: {title[:50]}...")
                print(f"  Time: {time_str}")
            else:
                print(f"[FAIL] {year}: No announcements found")

    except Exception as e:
        print(f"[FAIL] Comparison test failed: {e}")

if __name__ == "__main__":
    # Test 2020
    success_2020 = test_2020_download()

    # Compare with other years
    test_other_years()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    if success_2020:
        print("[SUCCESS] 2020 annual report search function fixed")
        print("   - Extended search date range (2021-2022)")
        print("   - Added special search strategy")
    else:
        print("[FAIL] 2020 annual report search still has issues")

    print("\nNote: This test only verifies search functionality")
    print("      Actual download requires network connection")