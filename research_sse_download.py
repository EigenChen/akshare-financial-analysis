# -*- coding: utf-8 -*-
"""
上海证券交易所年报下载研究
研究SSE官网的年报下载API和方法
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
import re

class SSEAnnualReportDownloader:
    """上海证券交易所年报下载器"""

    def __init__(self):
        self.base_url = "http://www.sse.com.cn"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def search_company_announcements(self, stock_code: str, year: int) -> List[Dict]:
        """搜索公司公告"""
        print(f"[SSE] 搜索股票 {stock_code} 的 {year} 年报...")

        # 上交所可能的API端点
        search_urls = [
            "http://query.sse.com.cn/security/stock/getStockListData2.do",
            "http://query.sse.com.cn/commonQuery.do",
            "http://www.sse.com.cn/disclosure/listedinfo/announcement/",
            "http://query.sse.com.cn/infodisplay/queryLatestBulletinNew.do",
        ]

        results = []

        for url in search_urls:
            try:
                print(f"  尝试API: {url}")

                if "getStockListData2.do" in url:
                    # 尝试获取股票列表数据
                    params = {
                        'jsonCallBack': 'jsonpCallback123456',
                        'isPagination': 'true',
                        'stockCode': stock_code,
                        'csrcCode': '',
                        'areaName': '',
                        'stockType': '1',  # A股
                    }

                elif "commonQuery.do" in url:
                    # 通用查询接口
                    params = {
                        'jsonCallBack': 'jsonpCallback123456',
                        'sqlId': 'COMMON_SSE_XXPL_CXDA_L_NEW_SEARCH_001_01',
                        'COMPANY_CODE': stock_code,
                        'BULLETIN_TYPE': '年度报告',
                        'pageHelp.pageSize': '25',
                        'pageHelp.pageNo': '1',
                        'pageHelp.beginPage': '1',
                        'pageHelp.endPage': '5'
                    }

                elif "queryLatestBulletinNew.do" in url:
                    # 最新公告查询
                    params = {
                        'jsonCallBack': 'jsonpCallback123456',
                        'productId': stock_code,
                        'reportType2': '年度报告',
                    }

                else:
                    # 直接访问页面
                    params = {
                        'productId': stock_code
                    }

                response = self.session.get(url, params=params, timeout=30)
                print(f"    状态码: {response.status_code}")

                if response.status_code == 200:
                    content = response.text
                    print(f"    响应长度: {len(content)}")

                    # 尝试解析JSONP响应
                    if 'jsonpCallback' in content:
                        # 提取JSON部分
                        json_start = content.find('(') + 1
                        json_end = content.rfind(')')
                        if json_start > 0 and json_end > json_start:
                            json_str = content[json_start:json_end]
                            try:
                                data = json.loads(json_str)
                                results.append({
                                    'url': url,
                                    'data': data,
                                    'type': 'jsonp'
                                })
                                print(f"    [成功] 解析到JSONP数据")
                            except:
                                print(f"    [失败] JSONP解析失败")

                    # 检查是否包含年报相关信息
                    if year and str(year) in content and '年报' in content:
                        print(f"    [发现] 内容包含{year}年报信息")
                        results.append({
                            'url': url,
                            'data': content[:1000],  # 保存前1000字符
                            'type': 'html'
                        })

                time.sleep(1)  # 避免请求过快

            except Exception as e:
                print(f"    [错误] {e}")
                continue

        return results

    def analyze_sse_structure(self):
        """分析上交所网站结构"""
        print("[SSE] 分析网站结构...")

        # 主要页面
        pages_to_analyze = [
            "http://www.sse.com.cn/disclosure/listedinfo/announcement/",
            "http://www.sse.com.cn/disclosure/listedinfo/regular/",
            "http://query.sse.com.cn/",
        ]

        for page_url in pages_to_analyze:
            try:
                print(f"\n分析页面: {page_url}")
                response = self.session.get(page_url, timeout=30)

                if response.status_code == 200:
                    content = response.text

                    # 查找API端点
                    api_patterns = [
                        r'query\.sse\.com\.cn[^"\s]*',
                        r'www\.sse\.com\.cn/[^"\s]*\.do',
                        r'/[^"\s]*query[^"\s]*\.do',
                        r'/[^"\s]*search[^"\s]*\.do',
                    ]

                    found_apis = set()
                    for pattern in api_patterns:
                        matches = re.findall(pattern, content)
                        found_apis.update(matches)

                    if found_apis:
                        print("  发现的API端点:")
                        for api in sorted(found_apis)[:10]:  # 只显示前10个
                            print(f"    {api}")

                time.sleep(2)

            except Exception as e:
                print(f"  错误: {e}")

    def test_2020_report_download(self, stock_code: str) -> Optional[str]:
        """测试2020年报下载"""
        print(f"[SSE] 测试 {stock_code} 的2020年报下载...")

        # 首先分析网站结构
        self.analyze_sse_structure()

        # 搜索公告
        results = self.search_company_announcements(stock_code, 2020)

        if results:
            print(f"\n找到 {len(results)} 个搜索结果:")
            for i, result in enumerate(results, 1):
                print(f"  结果 {i}: {result['url']} ({result['type']})")

        return None

def test_sse_download():
    """测试上交所下载"""
    print("=" * 80)
    print("上海证券交易所年报下载测试")
    print("=" * 80)

    downloader = SSEAnnualReportDownloader()

    # 测试海康威视 (深交所股票，但也测试一下)
    # 测试上交所股票
    test_stocks = [
        ("600519", "贵州茅台"),  # 上交所
        ("600036", "招商银行"),  # 上交所
        ("600000", "浦发银行"),  # 上交所
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

        time.sleep(3)  # 避免请求过快

if __name__ == "__main__":
    test_sse_download()