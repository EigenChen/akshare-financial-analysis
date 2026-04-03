# -*- coding: utf-8 -*-
"""
测试其他公开年报数据源
包括东方财富、新浪财经、腾讯财经等
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import re

class AlternativeDataSourceTester:
    """替代数据源测试器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

    def test_eastmoney_source(self, stock_code: str, year: int) -> Dict:
        """测试东方财富数据源"""
        print(f"\n[东方财富] 测试 {stock_code} {year}年报...")

        # 东方财富可能的API
        apis = [
            {
                'name': '东方财富公告搜索API',
                'url': 'http://search-api-web.eastmoney.com/search/jsonp',
                'params': {
                    'cb': 'jQuery',
                    'param': json.dumps({
                        'uid': '',
                        'keyword': f'{stock_code} {year}年度报告',
                        'type': ['cmsArticleWebOld'],
                        'client': 'web',
                        'clientType': 'web',
                        'clientVersion': 'curr',
                        'param': {'cmsArticleWebOld': {'searchScope': 'default'}}
                    }),
                    'pageindex': '0',
                    'pagesize': '10',
                    'sort': 'default',
                    'source': 'Ths_iwencai_Xuangu',
                    'version': '2.0',
                }
            },
            {
                'name': '东方财富数据中心API',
                'url': 'http://datacenter-web.eastmoney.com/api/data/v1/get',
                'params': {
                    'sortColumns': 'NOTICE_DATE',
                    'sortTypes': '-1',
                    'pageSize': '50',
                    'pageNumber': '1',
                    'reportName': 'RPT_PUBLIC_OP_NEWNOTICE',
                    'columns': 'ALL',
                    'filter': f'(SECURITY_CODE="{stock_code}")AND(NOTICE_TYPE_NAME="年报")',
                }
            }
        ]

        results = {'source': 'eastmoney', 'success': False, 'data': []}

        for api in apis:
            try:
                print(f"  测试: {api['name']}")
                response = self.session.get(api['url'], params=api['params'], timeout=30)
                print(f"    状态码: {response.status_code}")

                if response.status_code == 200:
                    content = response.text
                    print(f"    响应长度: {len(content)}")

                    # 尝试解析JSONP或JSON
                    try:
                        # 处理JSONP响应
                        if content.startswith('jQuery'):
                            json_start = content.find('(') + 1
                            json_end = content.rfind(')')
                            if json_start > 0 and json_end > json_start:
                                json_str = content[json_start:json_end]
                                data = json.loads(json_str)
                        else:
                            data = json.loads(content)

                        print(f"    [成功] 解析JSON数据")
                        if 'result' in data or 'data' in data:
                            results['success'] = True
                            results['data'].append({
                                'api_name': api['name'],
                                'data': data
                            })

                    except:
                        if str(year) in content:
                            print(f"    [发现] 包含{year}年信息")

                time.sleep(1)

            except Exception as e:
                print(f"    错误: {e}")

        return results

    def test_sina_finance_source(self, stock_code: str, year: int) -> Dict:
        """测试新浪财经数据源"""
        print(f"\n[新浪财经] 测试 {stock_code} {year}年报...")

        # 新浪财经可能的API
        apis = [
            {
                'name': '新浪财经公告API',
                'url': 'https://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpAnnouncements/stockid/{}.phtml'.format(stock_code),
            },
            {
                'name': '新浪财经财报API',
                'url': 'https://money.finance.sina.com.cn/corp/go.php/vDOWN_CashFlow/displaytype/4/stockid/{}/ctrl/{}/'.format(stock_code, year),
            }
        ]

        results = {'source': 'sina', 'success': False, 'data': []}

        for api in apis:
            try:
                print(f"  测试: {api['name']}")
                response = self.session.get(api['url'], timeout=30)
                print(f"    状态码: {response.status_code}")

                if response.status_code == 200:
                    content = response.text
                    print(f"    响应长度: {len(content)}")

                    if str(year) in content and ('年报' in content or '年度报告' in content):
                        print(f"    [发现] 包含{year}年报信息")
                        results['success'] = True
                        results['data'].append({
                            'api_name': api['name'],
                            'found_year_report': True
                        })

                time.sleep(2)

            except Exception as e:
                print(f"    错误: {e}")

        return results

    def test_tencent_finance_source(self, stock_code: str, year: int) -> Dict:
        """测试腾讯财经数据源"""
        print(f"\n[腾讯财经] 测试 {stock_code} {year}年报...")

        # 腾讯财经可能的API
        apis = [
            {
                'name': '腾讯财经股票API',
                'url': f'https://qt.gtimg.cn/q=s_{stock_code}',
            },
            {
                'name': '腾讯财经公告搜索',
                'url': 'https://stockapp.finance.qq.com/mstats/',
            }
        ]

        results = {'source': 'tencent', 'success': False, 'data': []}

        for api in apis:
            try:
                print(f"  测试: {api['name']}")
                response = self.session.get(api['url'], timeout=30)
                print(f"    状态码: {response.status_code}")

                if response.status_code == 200:
                    content = response.text
                    print(f"    响应长度: {len(content)}")

                    if stock_code in content:
                        print(f"    [发现] 包含股票信息")
                        results['data'].append({
                            'api_name': api['name'],
                            'has_stock_info': True
                        })

                time.sleep(2)

            except Exception as e:
                print(f"    错误: {e}")

        return results

    def test_csrc_source(self, stock_code: str, year: int) -> Dict:
        """测试证监会数据源"""
        print(f"\n[证监会] 测试 {stock_code} {year}年报...")

        # 证监会可能的数据源
        apis = [
            {
                'name': '证监会信息披露',
                'url': 'http://www.csrc.gov.cn/csrc/c100028/common_list.shtml',
            }
        ]

        results = {'source': 'csrc', 'success': False, 'data': []}

        for api in apis:
            try:
                print(f"  测试: {api['name']}")
                response = self.session.get(api['url'], timeout=30)
                print(f"    状态码: {response.status_code}")

                if response.status_code == 200:
                    content = response.text
                    print(f"    响应长度: {len(content)}")

                time.sleep(2)

            except Exception as e:
                print(f"    错误: {e}")

        return results

    def test_wind_alternative_sources(self, stock_code: str, year: int) -> List[Dict]:
        """测试Wind等替代数据源"""
        print(f"\n[替代源] 测试各种可能的数据源...")

        alternative_sources = [
            {
                'name': '同花顺数据',
                'urls': [
                    f'http://basic.10jqka.com.cn/{stock_code}/',
                    f'http://stockpage.10jqka.com.cn/{stock_code}/',
                ]
            },
            {
                'name': '网易财经',
                'urls': [
                    f'https://quotes.money.163.com/trade/lsjysj_{stock_code}.html',
                ]
            },
            {
                'name': '雪球',
                'urls': [
                    f'https://xueqiu.com/S/SZ{stock_code}' if stock_code.startswith(('000', '002', '300')) else f'https://xueqiu.com/S/SH{stock_code}',
                ]
            }
        ]

        results = []

        for source in alternative_sources:
            print(f"\n  测试数据源: {source['name']}")
            source_result = {'source': source['name'], 'success': False, 'urls_tested': []}

            for url in source['urls']:
                try:
                    print(f"    测试URL: {url}")
                    response = self.session.get(url, timeout=20)
                    print(f"      状态码: {response.status_code}")

                    url_result = {
                        'url': url,
                        'status_code': response.status_code,
                        'success': False
                    }

                    if response.status_code == 200:
                        content = response.text
                        print(f"      响应长度: {len(content)}")

                        # 检查是否包含年报信息
                        year_keywords = [f'{year}年', f'{year}年报', f'{year}年度报告']
                        found_keywords = []

                        for keyword in year_keywords:
                            if keyword in content:
                                found_keywords.append(keyword)

                        if found_keywords:
                            print(f"      [发现] 包含关键词: {found_keywords}")
                            url_result['success'] = True
                            url_result['found_keywords'] = found_keywords
                            source_result['success'] = True

                    source_result['urls_tested'].append(url_result)
                    time.sleep(2)

                except Exception as e:
                    print(f"      错误: {e}")
                    source_result['urls_tested'].append({
                        'url': url,
                        'error': str(e),
                        'success': False
                    })

            results.append(source_result)

        return results

def comprehensive_test():
    """全面测试各种数据源"""
    print("=" * 80)
    print("全面年报数据源测试")
    print("=" * 80)

    tester = AlternativeDataSourceTester()

    # 测试股票
    test_stocks = [
        ("002415", "海康威视"),
        ("600519", "贵州茅台"),
    ]

    all_results = []

    for stock_code, name in test_stocks:
        print(f"\n{'='*70}")
        print(f"测试股票: {stock_code} ({name}) - 2020年报")
        print(f"{'='*70}")

        stock_results = {
            'stock_code': stock_code,
            'company_name': name,
            'results': []
        }

        # 测试各种数据源
        try:
            # 东方财富
            result1 = tester.test_eastmoney_source(stock_code, 2020)
            stock_results['results'].append(result1)

            # 新浪财经
            result2 = tester.test_sina_finance_source(stock_code, 2020)
            stock_results['results'].append(result2)

            # 腾讯财经
            result3 = tester.test_tencent_finance_source(stock_code, 2020)
            stock_results['results'].append(result3)

            # 证监会
            result4 = tester.test_csrc_source(stock_code, 2020)
            stock_results['results'].append(result4)

            # 替代数据源
            result5_list = tester.test_wind_alternative_sources(stock_code, 2020)
            stock_results['results'].extend(result5_list)

        except Exception as e:
            print(f"[错误] 股票 {stock_code} 测试出错: {e}")

        all_results.append(stock_results)
        time.sleep(5)  # 避免请求过快

    # 汇总结果
    print(f"\n{'='*80}")
    print("测试结果汇总")
    print(f"{'='*80}")

    for stock_result in all_results:
        print(f"\n股票: {stock_result['stock_code']} ({stock_result['company_name']})")
        print("-" * 50)

        successful_sources = []
        failed_sources = []

        for result in stock_result['results']:
            source_name = result.get('source', '未知')
            if result.get('success', False):
                successful_sources.append(source_name)
            else:
                failed_sources.append(source_name)

        if successful_sources:
            print(f"  [成功] 找到数据的源: {', '.join(successful_sources)}")
        if failed_sources:
            print(f"  [失败] 未找到数据的源: {', '.join(failed_sources)}")

        if not successful_sources:
            print(f"  [结论] 所有测试的数据源都未找到2020年报")

    return all_results

if __name__ == "__main__":
    comprehensive_test()