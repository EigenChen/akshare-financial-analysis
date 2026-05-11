# -*- coding: utf-8 -*-
"""
调试2020年年报搜索问题
"""
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def debug_2020_search():
    """深度调试2020年年报搜索"""
    print("=" * 60)
    print("Debug 2020 Annual Report Search")
    print("=" * 60)

    try:
        # Import PDF download module
        spec = importlib.util.spec_from_file_location('pdf_downloader', ROOT / 'core/a_share/annual_report_downloader.py')
        pdf_module = importlib.util.module_from_spec(spec)
        sys.modules['pdf_downloader'] = pdf_module
        spec.loader.exec_module(pdf_module)

        symbol = "002415"
        year = 2020

        print(f"Stock: {symbol}, Year: {year}")
        print("=" * 60)

        # 策略1：扩大到2023年搜索
        print("\nStrategy 1: Extended search to 2023")
        print("-" * 40)

        # 直接调用API，扩大搜索范围到2023年
        import requests

        # 巨潮资讯网公告历史查询API
        search_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://www.cninfo.com.cn',
        }

        # 扩大搜索到2021-2023年
        data = {
            'pageNum': '1',
            'pageSize': '50',
            'column': 'szse',
            'tabName': 'fulltext',
            'plate': '',
            'stock': '',
            'searchkey': '002415 2020',
            'secid': '',
            'category': '',  # 不限制分类
            'trade': '',
            'seDate': '2021-01-01~2023-12-31',  # 扩大到2023年
            'sortName': '',
            'sortType': '',
            'isHLtitle': 'true',
        }

        print(f"Search params: {data}")

        response = requests.post(search_url, headers=headers, data=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            ann_list = result.get('announcements', [])
            total_count = result.get('totalAnnouncement', 0)

            print(f"Total announcements found: {total_count}")

            if ann_list:
                print("\nAll announcements (first 10):")
                for i, ann in enumerate(ann_list[:10], 1):
                    title = ann.get('announcementTitle', '')
                    time_str = ann.get('announcementTime', '')
                    sec_code = ann.get('secCode', '')

                    # 转换时间戳
                    if isinstance(time_str, (int, float)):
                        from datetime import datetime
                        time_str = datetime.fromtimestamp(time_str / 1000).strftime('%Y-%m-%d')

                    print(f"  {i}. [{sec_code}] {title}")
                    print(f"     Time: {time_str}")

                    # 检查是否包含2020年报
                    if '2020' in title and ('年度报告' in title or '年报' in title):
                        print(f"     *** FOUND 2020 ANNUAL REPORT! ***")

        # 策略2：无日期限制搜索
        print("\n" + "-" * 60)
        print("Strategy 2: No date restriction")
        print("-" * 40)

        data2 = {
            'pageNum': '1',
            'pageSize': '50',
            'column': 'szse',
            'tabName': 'fulltext',
            'plate': '',
            'stock': '',
            'searchkey': '002415 2020年度报告',
            'secid': '',
            'category': '',
            'trade': '',
            'seDate': '',  # 无日期限制
            'sortName': '',
            'sortType': '',
            'isHLtitle': 'true',
        }

        response2 = requests.post(search_url, headers=headers, data=data2, timeout=30)

        if response2.status_code == 200:
            result2 = response2.json()
            ann_list2 = result2.get('announcements', [])
            total_count2 = result2.get('totalAnnouncement', 0)

            print(f"Total announcements found (no date limit): {total_count2}")

            if ann_list2:
                print("\nFiltered 2020 reports:")
                for i, ann in enumerate(ann_list2[:10], 1):
                    title = ann.get('announcementTitle', '')
                    time_str = ann.get('announcementTime', '')

                    if isinstance(time_str, (int, float)):
                        from datetime import datetime
                        time_str = datetime.fromtimestamp(time_str / 1000).strftime('%Y-%m-%d')

                    if '2020' in title:
                        print(f"  {i}. {title}")
                        print(f"     Time: {time_str}")

    except Exception as e:
        print(f"[ERROR] Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_2020_search()