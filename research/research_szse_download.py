# -*- coding: utf-8 -*-
"""
深圳证券交易所年报下载研究
研究SZSE官网的年报下载API和方法
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
import re

class SZSEAnnualReportDownloader:
    """深圳证券交易所年报下载器"""

    def __init__(self):
        self.base_url = "http://www.szse.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def search_company_announcements(self, stock_code: str, year: int) -> List[Dict]:
        """搜索公司公告"""
        print(f"[SZSE] 搜索股票 {stock_code} 的 {year} 年报...")

        # 深交所可能的API端点
        search_urls = [
            "http://www.szse.cn/api/search/content",
            "http://www.szse.cn/api/report/ShowReport",
            "http://reportdocs.static.szse.cn/",
            "http://disc.static.szse.cn/",
            "http://www.szse.cn/disclosure/listed/bulletinDetail",
            "http://www.szse.cn/disclosure/supervision/inquire/index.html",
        ]

        results = []

        for url in search_urls:
            try:
                print(f"  尝试API: {url}")

                if "/api/search/content" in url:
                    # 搜索API
                    params = {
                        'serachWord': f"{stock_code} {year}年度报告",
                        'articleType': '',
                        'range': 'title',
                    }
                    response = self.session.get(url, params=params, timeout=30)

                elif "/api/report/ShowReport" in url:
                    # 报告展示API
                    params = {
                        'CATALOGID': '1801_cxda',
                        'TABKEY': 'tab1',
                        'txtStockCode': stock_code,
                        'txtStartDate': f'{year}-01-01',
                        'txtEndDate': f'{year+1}-12-31',
                    }
                    response = self.session.get(url, params=params, timeout=30)

                else:
                    # 直接访问页面
                    if stock_code:
                        params = {'stock_code': stock_code}
                    else:
                        params = {}
                    response = self.session.get(url, params=params, timeout=30)

                print(f"    状态码: {response.status_code}")

                if response.status_code == 200:
                    content = response.text
                    print(f"    响应长度: {len(content)}")

                    # 尝试解析JSON响应
                    try:
                        if content.strip().startswith('{') or content.strip().startswith('['):
                            data = json.loads(content)
                            results.append({
                                'url': url,
                                'data': data,
                                'type': 'json'
                            })
                            print(f"    [成功] 解析到JSON数据")
                    except:
                        # 不是JSON，可能是HTML
                        pass

                    # 检查是否包含年报相关信息
                    if year and str(year) in content and ('年报' in content or '年度报告' in content):
                        print(f"    [发现] 内容包含{year}年报信息")
                        results.append({
                            'url': url,
                            'data': content[:1000],  # 保存前1000字符
                            'type': 'html'
                        })

                time.sleep(1)

            except Exception as e:
                print(f"    [错误] {e}")
                continue

        return results

    def analyze_szse_structure(self):
        """分析深交所网站结构"""
        print("[SZSE] 分析网站结构...")

        # 主要页面
        pages_to_analyze = [
            "http://www.szse.cn/disclosure/listed/fixed/index.html",
            "http://www.szse.cn/disclosure/listed/bulletinDetail/index.html",
            "http://www.szse.cn/English/disclosure/listed/fixed/index.html",
        ]

        for page_url in pages_to_analyze:
            try:
                print(f"\n分析页面: {page_url}")
                response = self.session.get(page_url, timeout=30)

                if response.status_code == 200:
                    content = response.text

                    # 查找API端点
                    api_patterns = [
                        r'www\.szse\.cn/api[^"\s]*',
                        r'/api/[^"\s]*',
                        r'reportdocs\.static\.szse\.cn[^"\s]*',
                        r'disc\.static\.szse\.cn[^"\s]*',
                    ]

                    found_apis = set()
                    for pattern in api_patterns:
                        matches = re.findall(pattern, content)
                        found_apis.update(matches)

                    if found_apis:
                        print("  发现的API端点:")
                        for api in sorted(found_apis)[:10]:
                            print(f"    {api}")

                    # 查找可能的下载链接模式
                    download_patterns = [
                        r'href="[^"]*\.pdf[^"]*"',
                        r'download[^"\s]*',
                        r'attachment[^"\s]*',
                    ]

                    for pattern in download_patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            print(f"  发现下载模式: {pattern}")
                            for match in matches[:3]:
                                print(f"    {match}")

                time.sleep(2)

            except Exception as e:
                print(f"  错误: {e}")

    def test_new_szse_api(self, stock_code: str, year: int) -> List[Dict]:
        """测试新的深交所API"""
        print(f"[SZSE] 测试新API搜索 {stock_code} {year}年报...")

        # 尝试新发现的API格式
        api_tests = [
            {
                'name': 'SZSE信息披露API v1',
                'url': 'http://www.szse.cn/api/disc/announcement/annList',
                'params': {
                    'random': str(int(time.time() * 1000)),
                    'stock': stock_code,
                    'seDate': f'{year+1}-01-01,{year+1}-12-31',
                    'category': '年报',
                }
            },
            {
                'name': 'SZSE信息披露API v2',
                'url': 'http://www.szse.cn/api/disc/announcement/annList',
                'params': {
                    'random': str(int(time.time() * 1000)),
                    'channelCode': '固定报告_annual',
                    'pageSize': '30',
                    'pageNum': '1',
                    'stock': stock_code,
                    'seDate': f'{year}-01-01,{year+2}-12-31',  # 扩大范围
                }
            },
            {
                'name': 'SZSE搜索API',
                'url': 'http://searchweb.szse.cn/was5/web/search',
                'params': {
                    'channelid': '290',
                    'searchword': f'{stock_code} {year}年度报告',
                    'perpage': '20',
                    'outlinepage': '10',
                }
            }
        ]

        results = []

        for test in api_tests:
            try:
                print(f"\n  测试: {test['name']}")
                print(f"    URL: {test['url']}")

                response = self.session.get(test['url'], params=test['params'], timeout=30)
                print(f"    状态码: {response.status_code}")

                if response.status_code == 200:
                    content = response.text
                    print(f"    响应长度: {len(content)}")

                    # 尝试解析JSON
                    try:
                        if content.strip().startswith('{'):
                            data = json.loads(content)
                            print(f"    [JSON] 成功解析")

                            # 查找公告信息
                            if 'data' in data:
                                announcements = data.get('data', [])
                                if isinstance(announcements, list):
                                    print(f"    找到 {len(announcements)} 条公告")
                                    for i, ann in enumerate(announcements[:3]):
                                        title = ann.get('title', ann.get('announcementTitle', '未知标题'))
                                        print(f"      {i+1}. {title}")

                            results.append({
                                'test_name': test['name'],
                                'url': test['url'],
                                'data': data,
                                'success': True
                            })
                        else:
                            print(f"    [HTML] 响应为HTML格式")
                            if str(year) in content:
                                print(f"    [发现] 包含{year}年信息")
                                results.append({
                                    'test_name': test['name'],
                                    'url': test['url'],
                                    'data': content[:500],
                                    'success': False
                                })

                    except json.JSONDecodeError:
                        print(f"    [HTML] 非JSON响应")
                        if str(year) in content and '年报' in content:
                            print(f"    [发现] 包含{year}年报信息")

                time.sleep(2)

            except Exception as e:
                print(f"    [错误] {e}")

        return results

    def test_2020_report_download(self, stock_code: str) -> Optional[str]:
        """测试2020年报下载"""
        print(f"[SZSE] 测试 {stock_code} 的2020年报下载...")

        # 分析网站结构
        self.analyze_szse_structure()

        # 测试新API
        api_results = self.test_new_szse_api(stock_code, 2020)

        # 搜索公告
        search_results = self.search_company_announcements(stock_code, 2020)

        total_results = len(api_results) + len(search_results)
        if total_results > 0:
            print(f"\n总共找到 {total_results} 个结果")
            print(f"  API测试结果: {len(api_results)}")
            print(f"  搜索结果: {len(search_results)}")

        return None

def test_szse_download():
    """测试深交所下载"""
    print("=" * 80)
    print("深圳证券交易所年报下载测试")
    print("=" * 80)

    downloader = SZSEAnnualReportDownloader()

    # 测试深交所股票
    test_stocks = [
        ("002415", "海康威视"),  # 深交所
        ("000858", "五粮液"),   # 深交所
        ("000001", "平安银行"), # 深交所
        ("300750", "宁德时代"), # 创业板
    ]

    for stock_code, name in test_stocks:
        print(f"\n{'='*60}")
        print(f"测试股票: {stock_code} ({name})")
        print(f"{'='*60}")

        try:
            result = downloader.test_2020_report_download(stock_code)
            if result:
                print(f"[成功] {stock_code} 2020年报下载成功: {result}")
            else:
                print(f"[失败] {stock_code} 2020年报下载失败")
        except Exception as e:
            print(f"[错误] {stock_code} 测试出错: {e}")

        time.sleep(3)

if __name__ == "__main__":
    test_szse_download()