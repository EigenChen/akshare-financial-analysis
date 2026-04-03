# -*- coding: utf-8 -*-
"""
最终调试：检查2020年报是否真的存在
"""
import sys
import importlib.util
import requests

def final_debug():
    """最终调试2020年报"""
    print("=" * 60)
    print("Final Debug: Check if 2020 Reports Actually Exist")
    print("=" * 60)

    search_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://www.cninfo.com.cn',
    }

    # 测试1：搜索所有002415公告，看看2020年发生了什么
    print("Test 1: All 002415 announcements (2020-2023)")
    print("-" * 50)

    data = {
        'pageNum': '1',
        'pageSize': '30',
        'column': 'szse',
        'tabName': 'fulltext',
        'plate': '',
        'stock': '',
        'searchkey': '002415',
        'secid': '',
        'category': 'category_ndbg_szsh',  # 只看年度报告分类
        'trade': '',
        'seDate': '2020-01-01~2023-12-31',
        'sortName': '',
        'sortType': '',
        'isHLtitle': 'true',
    }

    try:
        response = requests.post(search_url, headers=headers, data=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            ann_list = result.get('announcements', [])

            print(f"Found {len(ann_list)} annual reports for 002415 (2020-2023):")

            years_found = set()
            for ann in ann_list:
                title = ann.get('announcementTitle', '')
                time_str = ann.get('announcementTime', '')

                if isinstance(time_str, (int, float)):
                    from datetime import datetime
                    time_str = datetime.fromtimestamp(time_str / 1000).strftime('%Y-%m-%d')

                # 提取年份
                import re
                year_match = re.search(r'(\d{4})年', title)
                if year_match:
                    year = year_match.group(1)
                    years_found.add(year)
                    print(f"  {year}: {title[:50]}... ({time_str})")

            print(f"\nYears with annual reports found: {sorted(years_found)}")

            if '2020' not in years_found:
                print("\n*** 2020 annual report NOT FOUND in category_ndbg_szsh ***")
                print("This suggests 2020 report might be in a different category or severely delayed")

        # 测试2：不限制分类，搜索所有包含"2020年度"的公告
        print("\n" + "=" * 60)
        print("Test 2: Search ALL categories for '2020年度'")
        print("-" * 50)

        data2 = {
            'pageNum': '1',
            'pageSize': '50',
            'column': 'szse',
            'tabName': 'fulltext',
            'plate': '',
            'stock': '',
            'searchkey': '002415 2020年度',
            'secid': '',
            'category': '',  # 所有分类
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

            print(f"Found {len(ann_list2)} announcements containing '2020年度':")

            for ann in ann_list2[:10]:  # 只显示前10个
                title = ann.get('announcementTitle', '')
                time_str = ann.get('announcementTime', '')

                if isinstance(time_str, (int, float)):
                    from datetime import datetime
                    time_str = datetime.fromtimestamp(time_str / 1000).strftime('%Y-%m-%d')

                print(f"  {title} ({time_str})")

        # 测试3：检查其他知名公司的2020年报情况
        print("\n" + "=" * 60)
        print("Test 3: Check other companies' 2020 reports")
        print("-" * 50)

        test_companies = ['000858', '600519', '000001']  # 五粮液、茅台、平安银行

        for company in test_companies:
            data3 = {
                'pageNum': '1',
                'pageSize': '10',
                'column': 'szse' if company.startswith('00') else 'sse',
                'tabName': 'fulltext',
                'plate': '',
                'stock': '',
                'searchkey': f'{company} 2020年度报告',
                'secid': '',
                'category': '',
                'trade': '',
                'seDate': '',
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
            }

            response3 = requests.post(search_url, headers=headers, data=data3, timeout=30)

            if response3.status_code == 200:
                result3 = response3.json()
                ann_list3 = result3.get('announcements', [])

                if ann_list3:
                    ann = ann_list3[0]
                    title = ann.get('announcementTitle', '')
                    time_str = ann.get('announcementTime', '')

                    if isinstance(time_str, (int, float)):
                        from datetime import datetime
                        time_str = datetime.fromtimestamp(time_str / 1000).strftime('%Y-%m-%d')

                    print(f"  {company}: Found 2020 report - {time_str}")
                else:
                    print(f"  {company}: No 2020 report found")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    final_debug()