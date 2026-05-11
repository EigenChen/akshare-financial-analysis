# -*- coding: utf-8 -*-
"""
深度调试搜索API - 寻找海康2020年报
"""
import requests
import json

def debug_search_api():
    """深度调试搜索API"""
    print("=" * 70)
    print("Deep Debug: Search API for Hikvision 2020 Report")
    print("=" * 70)

    search_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://www.cninfo.com.cn',
    }

    # 已知信息：announcementId=1209712163, 发布日期=2021-04-17
    # 让我们尝试不同的搜索策略

    strategies = [
        {
            'name': 'Strategy 1: Search by exact date',
            'params': {
                'pageNum': '1',
                'pageSize': '30',
                'column': 'szse',
                'tabName': 'fulltext',
                'plate': '',
                'stock': '',
                'searchkey': '002415',
                'secid': '',
                'category': 'category_ndbg_szsh',
                'trade': '',
                'seDate': '2021-04-17~2021-04-17',  # 精确日期
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
            }
        },
        {
            'name': 'Strategy 2: Search by date range around 2021-04-17',
            'params': {
                'pageNum': '1',
                'pageSize': '30',
                'column': 'szse',
                'tabName': 'fulltext',
                'plate': '',
                'stock': '',
                'searchkey': '002415',
                'secid': '',
                'category': 'category_ndbg_szsh',
                'trade': '',
                'seDate': '2021-04-01~2021-04-30',  # 4月份
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
            }
        },
        {
            'name': 'Strategy 3: No category restriction, search 2021',
            'params': {
                'pageNum': '1',
                'pageSize': '50',
                'column': 'szse',
                'tabName': 'fulltext',
                'plate': '',
                'stock': '',
                'searchkey': '002415',
                'secid': '',
                'category': '',  # 不限制分类
                'trade': '',
                'seDate': '2021-01-01~2021-12-31',
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
            }
        },
        {
            'name': 'Strategy 4: Search by stock code only, no restrictions',
            'params': {
                'pageNum': '1',
                'pageSize': '100',
                'column': 'szse',
                'tabName': 'fulltext',
                'plate': '',
                'stock': '002415',  # 使用stock字段而不是searchkey
                'searchkey': '',
                'secid': '',
                'category': '',
                'trade': '',
                'seDate': '2021-01-01~2021-12-31',
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
            }
        }
    ]

    target_id = "1209712163"

    for strategy in strategies:
        print(f"\n{strategy['name']}")
        print("-" * 50)

        try:
            response = requests.post(search_url, headers=headers, data=strategy['params'], timeout=30)

            if response.status_code == 200:
                result = response.json()
                ann_list = result.get('announcements', [])
                total_count = result.get('totalAnnouncement', 0)

                print(f"Total found: {total_count}")

                found_target = False
                for ann in ann_list:
                    ann_id = ann.get('announcementId', '')
                    title = ann.get('announcementTitle', '')
                    time_str = ann.get('announcementTime', '')

                    if isinstance(time_str, (int, float)):
                        from datetime import datetime
                        time_str = datetime.fromtimestamp(time_str / 1000).strftime('%Y-%m-%d')

                    # 检查是否找到目标公告
                    if str(ann_id) == target_id:
                        print(f"*** FOUND TARGET! ***")
                        print(f"  ID: {ann_id}")
                        print(f"  Title: {title}")
                        print(f"  Time: {time_str}")
                        print(f"  orgId: {ann.get('orgId', 'N/A')}")
                        found_target = True

                    # 显示包含"2020"的公告
                    if '2020' in title:
                        print(f"  2020 Report: {title} ({time_str}) ID:{ann_id}")

                if not found_target:
                    print("Target announcement NOT found in this search")

            else:
                print(f"HTTP Error: {response.status_code}")

        except Exception as e:
            print(f"Error: {e}")

def test_direct_api_call():
    """直接测试API调用，看看能不能获取到公告详情"""
    print("\n" + "=" * 70)
    print("Testing Direct API Call for Announcement Details")
    print("=" * 70)

    # 尝试直接访问公告详情API
    detail_urls = [
        "http://www.cninfo.com.cn/new/disclosure/detail/download?announcementId=1209712163",
        f"http://static.cninfo.com.cn/finalpage/20210417/1209712163.PDF",
        "https://www.cninfo.com.cn/new/disclosure/detail?plate=szse&orgId=9900012688&stockCode=002415&announcementId=1209712163&announcementTime=2021-04-17",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    for url in detail_urls:
        try:
            print(f"\nTesting: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"Content-Length: {response.headers.get('Content-Length', 'N/A')}")

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' in content_type.lower():
                    print("*** This is a PDF! ***")
                elif 'html' in content_type.lower():
                    # 检查是否是重定向页面
                    if len(response.text) < 1000:
                        print(f"HTML content preview: {response.text[:200]}")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    debug_search_api()
    test_direct_api_call()