# -*- coding: utf-8 -*-
"""
专门测试海康2020年报搜索 - 基于已知信息
"""
import requests
import json

def test_known_announcement():
    """基于已知信息测试搜索"""
    print("=" * 70)
    print("Test Search for Known Hikvision 2020 Report")
    print("=" * 70)

    # 已知信息
    known_info = {
        'announcementId': '1209712163',
        'announcementTime': '2021-04-17',
        'orgId': '9900012688',
        'stockCode': '002415',
        'plate': 'szse'
    }

    print("Known Information:")
    for key, value in known_info.items():
        print(f"  {key}: {value}")

    search_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://www.cninfo.com.cn',
    }

    # 尝试各种搜索参数组合
    test_cases = [
        {
            'name': 'Test 1: Search by orgId',
            'params': {
                'pageNum': '1',
                'pageSize': '30',
                'column': 'szse',
                'tabName': 'fulltext',
                'plate': 'szse',
                'stock': '',
                'searchkey': '',
                'secid': '',
                'category': '',
                'trade': '',
                'seDate': '2021-04-17~2021-04-17',
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
                'orgId': '9900012688',  # 尝试直接使用orgId
            }
        },
        {
            'name': 'Test 2: Search by exact title pattern',
            'params': {
                'pageNum': '1',
                'pageSize': '50',
                'column': 'szse',
                'tabName': 'fulltext',
                'plate': '',
                'stock': '',
                'searchkey': '海康威视 2020年度报告',
                'secid': '',
                'category': '',
                'trade': '',
                'seDate': '2021-01-01~2021-12-31',
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
            }
        },
        {
            'name': 'Test 3: Search all 002415 reports in 2021',
            'params': {
                'pageNum': '1',
                'pageSize': '100',
                'column': 'szse',
                'tabName': 'fulltext',
                'plate': '',
                'stock': '002415',
                'searchkey': '',
                'secid': '',
                'category': '',
                'trade': '',
                'seDate': '2021-01-01~2021-12-31',
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
            }
        },
        {
            'name': 'Test 4: Search with secCode filter',
            'params': {
                'pageNum': '1',
                'pageSize': '100',
                'column': 'szse',
                'tabName': 'fulltext',
                'plate': '',
                'stock': '',
                'searchkey': '年度报告',
                'secid': '',
                'category': 'category_ndbg_szsh',
                'trade': '',
                'seDate': '2021-04-01~2021-05-01',
                'sortName': '',
                'sortType': '',
                'isHLtitle': 'true',
            }
        }
    ]

    target_id = "1209712163"

    for test_case in test_cases:
        print(f"\n{test_case['name']}")
        print("-" * 50)

        try:
            response = requests.post(search_url, headers=headers, data=test_case['params'], timeout=30)

            if response.status_code == 200:
                result = response.json()
                ann_list = result.get('announcements', [])
                total_count = result.get('totalAnnouncement', 0)

                print(f"Total found: {total_count}")

                if ann_list:
                    found_target = False
                    for ann in ann_list:
                        ann_id = str(ann.get('announcementId', ''))
                        title = ann.get('announcementTitle', '')
                        time_str = ann.get('announcementTime', '')
                        sec_code = ann.get('secCode', '')
                        org_id = ann.get('orgId', '')

                        if isinstance(time_str, (int, float)):
                            from datetime import datetime
                            time_str = datetime.fromtimestamp(time_str / 1000).strftime('%Y-%m-%d')

                        # 检查是否是目标公告
                        if ann_id == target_id:
                            print(f"*** FOUND TARGET ANNOUNCEMENT! ***")
                            print(f"  ID: {ann_id}")
                            print(f"  Title: {title}")
                            print(f"  Time: {time_str}")
                            print(f"  SecCode: {sec_code}")
                            print(f"  OrgId: {org_id}")
                            found_target = True

                        # 显示002415相关的公告
                        if sec_code == '002415':
                            marker = " *** TARGET ***" if ann_id == target_id else ""
                            print(f"  002415: {title[:50]}... ({time_str}) ID:{ann_id}{marker}")

                    if not found_target:
                        print("Target announcement NOT found")

            else:
                print(f"HTTP Error: {response.status_code}")

        except Exception as e:
            print(f"Error: {e}")

    # 最后尝试：直接访问已知URL看看是否能解析出PDF链接
    print("\n" + "=" * 70)
    print("Final Test: Direct URL Analysis")
    print("=" * 70)

    known_url = "https://www.cninfo.com.cn/new/disclosure/detail?plate=szse&orgId=9900012688&stockCode=002415&announcementId=1209712163&announcementTime=2021-04-17"

    try:
        response = requests.get(known_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=30)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            # 尝试从HTML中提取PDF链接
            content = response.text
            if 'PDF' in content or 'pdf' in content:
                print("Page contains PDF references")
                # 可以进一步解析HTML来找到实际的PDF下载链接
            else:
                print("No PDF references found in page")

    except Exception as e:
        print(f"URL access error: {e}")

if __name__ == "__main__":
    test_known_announcement()