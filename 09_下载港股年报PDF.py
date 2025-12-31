# -*- coding: utf-8 -*-
"""
下载港股上市公司年度报告PDF

数据来源：香港交易所披露易（HKEXnews）
网址：https://www.hkexnews.hk

使用方法：
1. 从本地HTML解析下载（推荐）：
   python 09_下载港股年报PDF.py --html "搜索结果.html" --save_dir "小米年报"
   
2. 手动URL下载：
   python 09_下载港股年报PDF.py --url "PDF链接" --save_dir "保存目录"

3. 交互式模式：
   python 09_下载港股年报PDF.py --manual

操作步骤：
1. 在浏览器打开 https://www1.hkexnews.hk/search/titlesearch.xhtml
2. 输入股票代码，选择"年度报告"，搜索
3. Ctrl+S 保存网页为HTML文件
4. 使用 --html 参数指定HTML文件路径进行解析下载
"""

import os
import re
import time
import requests
from typing import Optional, List, Dict
from datetime import datetime
import argparse
import webbrowser


def parse_html_for_annual_reports(html_path: str) -> List[Dict]:
    """
    从本地HTML文件解析年报PDF链接
    
    参数:
        html_path: 本地HTML文件路径
    
    返回:
        年报信息列表，包含 {year, title, pdf_url}
    """
    print(f"[解析] 读取HTML文件: {html_path}")
    
    try:
        # 尝试多种编码
        content = None
        for encoding in ['utf-8', 'gbk', 'gb2312', 'big5']:
            try:
                with open(html_path, 'r', encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if not content:
            print(f"  [X] 无法读取文件，请检查编码")
            return []
        
        print(f"  文件大小: {len(content):,} 字节")
        
        results = []
        
        # 匹配年报PDF链接和标题
        # 格式: <a href="URL">XXXX 年度報告</a> 或 <a href="URL">XXXX年度報告</a>
        pattern = r'<a\s+href="(https://www1\.hkexnews\.hk/listedco/listconews/[^"]+\.pdf)"[^>]*>([^<]*年[度]?報告[^<]*)</a>'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        if not matches:
            # 尝试更宽松的匹配
            pattern = r'href="(https://www1\.hkexnews\.hk/listedco/listconews/[^"]+\.pdf)"[^>]*>([^<]*)</a>'
            matches = re.findall(pattern, content, re.IGNORECASE)
        
        for pdf_url, title in matches:
            title = title.strip()
            
            # 跳过非年报
            if '中期' in title or '半年' in title or 'interim' in title.lower():
                continue
            
            # 提取年份
            year_match = re.search(r'20(\d{2})', title)
            if year_match:
                year = int(f"20{year_match.group(1)}")
            else:
                # 从URL提取年份
                url_year_match = re.search(r'/(\d{4})/', pdf_url)
                if url_year_match:
                    year = int(url_year_match.group(1)) - 1  # URL年份通常是发布年份
                else:
                    year = None
            
            # 确认是年报
            is_annual = ('年報' in title or '年报' in title or 
                        '年度報告' in title or '年度报告' in title or
                        'annual' in title.lower())
            
            if is_annual and year:
                results.append({
                    'year': year,
                    'title': title,
                    'pdf_url': pdf_url,
                })
        
        # 去重（按年份）
        seen_years = set()
        unique_results = []
        for r in results:
            if r['year'] not in seen_years:
                seen_years.add(r['year'])
                unique_results.append(r)
        
        # 按年份排序
        unique_results.sort(key=lambda x: x['year'], reverse=True)
        
        print(f"  [OK] 找到 {len(unique_results)} 个年报")
        for r in unique_results:
            print(f"    {r['year']}年: {r['title'][:30]}...")
        
        return unique_results
        
    except Exception as e:
        print(f"  [X] 解析失败: {e}")
        return []


def download_from_html(html_path: str, save_dir: str = "港股年报PDF", 
                       symbol: str = None, years: List[int] = None) -> dict:
    """
    从HTML文件解析并下载年报
    
    参数:
        html_path: HTML文件路径
        save_dir: 保存目录
        symbol: 股票代码（用于生成文件名）
        years: 指定下载的年份列表，None表示下载所有
    
    返回:
        下载结果统计
    """
    results = {'success': [], 'failed': []}
    
    print("=" * 70)
    print("从HTML文件解析并下载港股年报")
    print(f"HTML文件: {html_path}")
    print(f"保存目录: {save_dir}")
    print("=" * 70)
    
    # 解析HTML
    reports = parse_html_for_annual_reports(html_path)
    
    if not reports:
        print("\n[!] 未找到任何年报链接")
        return results
    
    # 筛选年份
    if years:
        reports = [r for r in reports if r['year'] in years]
        print(f"\n筛选后: {len(reports)} 个年报")
    
    # 尝试从HTML文件名或路径提取股票信息
    if not symbol:
        # 从路径中提取
        path_match = re.search(r'(\d{5})', html_path)
        if path_match:
            symbol = path_match.group(1)
        else:
            symbol = "港股"
    
    symbol_clean = symbol.zfill(5) if symbol.isdigit() else symbol
    
    os.makedirs(save_dir, exist_ok=True)
    
    print(f"\n开始下载 {len(reports)} 个年报...")
    
    for report in reports:
        year = report['year']
        pdf_url = report['pdf_url']
        title = report['title']
        
        print(f"\n[{year}年] {title[:40]}...")
        
        # 生成文件名
        filename = f"{symbol_clean}_{year}年年度报告.pdf"
        save_path = os.path.join(save_dir, filename)
        
        if download_pdf_from_url(pdf_url, save_path):
            results['success'].append({'year': year, 'path': save_path})
        else:
            results['failed'].append({'year': year, 'reason': '下载失败'})
        
        time.sleep(1)
    
    # 打印汇总
    print("\n" + "=" * 70)
    print("下载完成！")
    print(f"成功: {len(results['success'])} 个")
    print(f"失败: {len(results['failed'])} 个")
    
    if results['success']:
        print("\n成功下载:")
        for item in results['success']:
            print(f"  [OK] {item['year']}年: {item['path']}")
    
    if results['failed']:
        print("\n下载失败:")
        for item in results['failed']:
            print(f"  [X] {item['year']}年: {item['reason']}")
    
    print("=" * 70)
    
    return results


def search_hkex_annual_reports(symbol: str, start_year: int, end_year: int) -> List[Dict]:
    """
    搜索港交所披露易获取年报PDF链接
    
    参数:
        symbol: 股票代码（5位）
        start_year: 起始年份
        end_year: 结束年份
    
    返回:
        年报信息列表，包含 {year, title, pdf_url}
    """
    symbol_clean = symbol.zfill(5)
    # 只取数字部分作为stockId
    stock_id = symbol_clean.lstrip('0') or '0'
    
    # 搜索日期范围：年报在次年发布
    from_date = f"{start_year + 1}0101"
    to_date = f"{end_year + 1}1231"
    
    # 港交所搜索API
    url = "https://www1.hkexnews.hk/search/titlesearch.xhtml"
    params = {
        'lang': 'ZH',
        'category': '0',
        'market': 'SEHK',
        'searchType': '0',
        'documentType': '40000',  # 年度报告
        't1code': '40000',
        't2Gcode': '-2',
        't2code': '-2',
        'stockId': stock_id,
        'from': from_date,
        'to': to_date,
        'MB-Ede': '',
        'sortDir': '0',
        'sortByRecordDate': 'true',
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www1.hkexnews.hk/search/titlesearch.xhtml',
    }
    
    print(f"  [搜索] 港交所披露易...")
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"  [X] HTTP状态码: {resp.status_code}")
            return []
        
        # 提取PDF链接和标题
        # 链接格式: href="/listedco/listconews/sehk/2024/0402/2024040200484_c.pdf"
        # 标题格式: >2023 年報</a>
        results = []
        
        # 提取所有PDF链接
        pdf_pattern = r'href="(/listedco/listconews/[^"]+\.pdf)"[^>]*>([^<]*)</a>'
        matches = re.findall(pdf_pattern, resp.text, re.IGNORECASE)
        
        for pdf_path, title in matches:
            title = title.strip()
            full_url = f"https://www1.hkexnews.hk{pdf_path}"
            
            # 尝试从标题或URL中提取年份
            year_match = re.search(r'20(\d{2})', title) or re.search(r'/20(\d{2})/', pdf_path)
            if year_match:
                year = int(f"20{year_match.group(1)}")
                # 如果是次年发布的年报，报告年份是上一年
                if '年報' in title or '年报' in title or 'annual' in title.lower():
                    report_year = year - 1  # 2024发布的是2023年报
                else:
                    report_year = year
            else:
                report_year = None
            
            # 筛选年度报告（排除中期报告等）
            is_annual = (
                ('年報' in title or '年报' in title or 'annual' in title.lower()) and
                '中期' not in title and 'interim' not in title.lower() and
                '半年' not in title
            )
            
            if is_annual:
                results.append({
                    'year': report_year,
                    'title': title,
                    'pdf_url': full_url,
                })
        
        print(f"  [OK] 找到 {len(results)} 个年报")
        return results
        
    except Exception as e:
        print(f"  [X] 搜索失败: {e}")
        return []


def get_hkex_search_url(symbol: str, year: int) -> str:
    """
    生成港交所披露易搜索URL
    
    参数:
        symbol: 股票代码（5位）
        year: 年份
    
    返回:
        搜索页面URL
    """
    symbol_clean = symbol.zfill(5)
    # 年报在次年发布
    from_date = f"{year + 1}-01-01"
    to_date = f"{year + 1}-12-31"
    
    # 港交所披露易搜索页面URL
    search_url = (
        f"https://www1.hkexnews.hk/search/titlesearch.xhtml?"
        f"lang=ZH&"
        f"category=0&"
        f"market=SEHK&"
        f"searchType=0&"
        f"documentType=9&"  # 9=年度报告
        f"t1code=40000&"  # 年度报告类别
        f"stockCode={symbol_clean}&"
        f"from={from_date}&"
        f"to={to_date}"
    )
    
    return search_url


def download_pdf_from_url(pdf_url: str, save_path: str) -> bool:
    """
    从URL下载PDF文件
    
    参数:
        pdf_url: PDF文件URL
        save_path: 保存路径
    
    返回:
        是否下载成功
    """
    # 确保URL完整
    if not pdf_url.startswith('http'):
        if pdf_url.startswith('/'):
            pdf_url = f"https://www1.hkexnews.hk{pdf_url}"
        else:
            pdf_url = f"https://www1.hkexnews.hk/{pdf_url}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.hkexnews.hk/',
        'Accept': 'application/pdf,*/*',
    }
    
    print(f"  [下载] {pdf_url}")
    
    try:
        response = requests.get(pdf_url, headers=headers, timeout=300, stream=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            content_length = int(response.headers.get('Content-Length', 0))
            
            print(f"    -> Content-Type: {content_type}")
            print(f"    -> 文件大小: {content_length/1024/1024:.2f} MB")
            
            # 检查是否是PDF
            if 'pdf' in content_type.lower() or content_length > 100000:
                # 创建目录
                save_dir = os.path.dirname(save_path)
                if save_dir:
                    os.makedirs(save_dir, exist_ok=True)
                
                # 保存文件（显示进度）
                downloaded = 0
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if content_length > 0:
                            progress = downloaded / content_length * 100
                            print(f"\r    -> 下载进度: {progress:.1f}%", end='')
                
                print()  # 换行
                
                # 验证文件大小
                file_size = os.path.getsize(save_path)
                if file_size > 50000:  # 至少50KB
                    print(f"  [OK] 下载成功: {save_path}")
                    print(f"    文件大小: {file_size/1024/1024:.2f} MB")
                    return True
                else:
                    print(f"    -> [X] 文件太小 ({file_size}字节)，可能不是有效PDF")
                    os.remove(save_path)
            else:
                print(f"    -> [X] 响应不是PDF格式")
        else:
            print(f"    -> [X] HTTP状态码: {response.status_code}")
            
    except Exception as e:
        print(f"    -> [X] 下载失败: {str(e)}")
    
    return False


def search_with_selenium(symbol: str, year: int) -> List[Dict]:
    """
    使用Selenium搜索港交所公告
    
    参数:
        symbol: 股票代码
        year: 年份
    
    返回:
        公告列表
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.options import Options
    except ImportError:
        print("  [!] Selenium未安装，请运行: pip install selenium")
        return []
    
    symbol_clean = symbol.zfill(5)
    from_date = f"{year + 1}0101"
    to_date = f"{year + 1}1231"
    
    # 搜索URL
    search_url = get_hkex_search_url(symbol, year)
    
    print(f"  [Selenium] 启动浏览器...")
    
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    announcements = []
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(search_url)
        
        # 等待搜索结果加载
        print(f"  [Selenium] 等待搜索结果...")
        time.sleep(5)  # 等待JavaScript执行
        
        # 查找PDF链接
        links = driver.find_elements(By.CSS_SELECTOR, 'a[href*=".pdf"]')
        
        print(f"  [Selenium] 找到 {len(links)} 个PDF链接")
        
        for link in links:
            try:
                href = link.get_attribute('href')
                title = link.text or link.get_attribute('title') or ''
                
                # 筛选年度报告
                if href and '.pdf' in href.lower():
                    title_lower = title.lower()
                    is_annual = (
                        '年度' in title or 'annual' in title_lower
                    ) and '中期' not in title and 'interim' not in title_lower
                    
                    if is_annual or not title:  # 如果没有标题，也加入候选
                        announcements.append({
                            'title': title or href.split('/')[-1],
                            'file_link': href,
                            'date': '',
                            'stock_code': symbol_clean,
                        })
                        print(f"    [OK] {title[:50] if title else href[-50:]}...")
            except Exception as e:
                continue
        
        driver.quit()
        
    except Exception as e:
        print(f"  [X] Selenium错误: {e}")
    
    return announcements


def download_hk_annual_report_selenium(symbol: str, year: int, save_dir: str = "港股年报PDF") -> Optional[str]:
    """
    使用Selenium下载港股年报
    
    参数:
        symbol: 股票代码
        year: 年份
        save_dir: 保存目录
    
    返回:
        下载的文件路径
    """
    print(f"\n[{year}年] 使用Selenium搜索...")
    
    announcements = search_with_selenium(symbol, year)
    
    if not announcements:
        print(f"  [!] 未找到 {year} 年的年报")
        return None
    
    # 使用第一个匹配的公告
    announcement = announcements[0]
    file_link = announcement.get('file_link', '')
    title = announcement.get('title', '')
    
    print(f"  [选择] {title[:60]}...")
    
    # 生成文件名
    symbol_clean = symbol.zfill(5)
    filename = f"{symbol_clean}_{year}年年度报告.pdf"
    save_path = os.path.join(save_dir, filename)
    
    os.makedirs(save_dir, exist_ok=True)
    
    if download_pdf_from_url(file_link, save_path):
        return save_path
    
    return None


def manual_download_mode(save_dir: str = "港股年报PDF"):
    """
    手动下载模式：用户输入PDF URL进行下载
    
    参数:
        save_dir: 保存目录
    """
    print("\n" + "=" * 60)
    print("手动下载模式")
    print("=" * 60)
    print("\n请按以下步骤操作：")
    print("1. 打开港交所披露易: https://www.hkexnews.hk")
    print("2. 在搜索框中输入股票代码")
    print("3. 选择'年度报告'类型，设置日期范围")
    print("4. 找到目标年报，右键复制PDF链接")
    print("5. 将链接粘贴到下方\n")
    
    os.makedirs(save_dir, exist_ok=True)
    
    while True:
        pdf_url = input("请输入PDF链接（输入q退出）: ").strip()
        
        if pdf_url.lower() == 'q':
            break
        
        if not pdf_url:
            continue
        
        # 尝试从URL中提取信息生成文件名
        filename = None
        
        # 尝试匹配股票代码
        code_match = re.search(r'(\d{5})', pdf_url)
        year_match = re.search(r'20(\d{2})', pdf_url)
        
        if code_match and year_match:
            stock_code = code_match.group(1)
            year = f"20{year_match.group(1)}"
            filename = f"{stock_code}_{year}年年度报告.pdf"
        else:
            # 使用URL中的文件名
            filename = pdf_url.split('/')[-1]
            if not filename.endswith('.pdf'):
                filename = f"港股年报_{int(time.time())}.pdf"
        
        save_path = os.path.join(save_dir, filename)
        
        if download_pdf_from_url(pdf_url, save_path):
            print(f"\n[OK] 文件已保存到: {save_path}\n")
        else:
            print(f"\n[X] 下载失败，请检查链接是否正确\n")


def open_hkex_search(symbol: str, year: int):
    """
    在浏览器中打开港交所披露易搜索页面
    
    参数:
        symbol: 股票代码
        year: 年份
    """
    search_url = get_hkex_search_url(symbol, year)
    print(f"\n正在打开浏览器...")
    print(f"搜索URL: {search_url}")
    webbrowser.open(search_url)
    print("\n请在浏览器中：")
    print("1. 查看搜索结果")
    print("2. 找到目标年报")
    print("3. 右键复制PDF链接")
    print("4. 使用 --url 参数下载，或进入手动下载模式")


def batch_download_hk_reports(symbol: str, start_year: int, end_year: int, 
                              save_dir: str = "港股年报PDF", use_selenium: bool = False) -> dict:
    """
    批量下载港股年报
    
    参数:
        symbol: 股票代码
        start_year: 起始年份
        end_year: 结束年份
        save_dir: 保存目录
        use_selenium: 是否使用Selenium自动搜索（已弃用，默认使用HTTP请求）
    
    返回:
        下载结果统计
    """
    results = {
        'success': [],
        'failed': []
    }
    
    symbol_clean = symbol.zfill(5)
    
    print("=" * 80)
    print("港股年报批量下载")
    print(f"股票代码: {symbol_clean}")
    print(f"年份范围: {start_year} - {end_year}")
    print(f"保存目录: {save_dir}")
    print("=" * 80)
    
    # 搜索港交所获取PDF链接
    print("\n[步骤1] 搜索港交所披露易...")
    all_reports = search_hkex_annual_reports(symbol, start_year, end_year)
    
    if not all_reports:
        print("\n[!] 未找到任何年报，尝试手动搜索模式...")
        for year in range(start_year, end_year + 1):
            print(f"\n[{year}年] 打开搜索页面...")
            open_hkex_search(symbol, year)
            time.sleep(1)
        print("\n请在浏览器中找到年报PDF链接，然后使用 --manual 模式下载")
        return results
    
    # 按年份整理
    reports_by_year = {}
    for report in all_reports:
        year = report.get('year')
        if year and start_year <= year <= end_year:
            if year not in reports_by_year:
                reports_by_year[year] = report
    
    print(f"\n[步骤2] 开始下载 {len(reports_by_year)} 个年报...")
    os.makedirs(save_dir, exist_ok=True)
    
    for year in range(start_year, end_year + 1):
        print(f"\n[{year}年]")
        
        if year not in reports_by_year:
            print(f"  [!] 未找到 {year} 年的年报")
            results['failed'].append({
                'year': year,
                'reason': '未找到'
            })
            continue
        
        report = reports_by_year[year]
        pdf_url = report['pdf_url']
        title = report['title']
        
        print(f"  标题: {title}")
        
        # 生成文件名
        filename = f"{symbol_clean}_{year}年年度报告.pdf"
        save_path = os.path.join(save_dir, filename)
        
        if download_pdf_from_url(pdf_url, save_path):
            results['success'].append({
                'year': year,
                'path': save_path
            })
        else:
            results['failed'].append({
                'year': year,
                'reason': '下载失败'
            })
        
        time.sleep(1)  # 避免请求过快
    
    # 打印汇总
    print("\n" + "=" * 80)
    print("下载完成！")
    print(f"成功: {len(results['success'])} 个")
    print(f"失败: {len(results['failed'])} 个")
    
    if results['success']:
        print("\n成功下载的年报:")
        for item in results['success']:
            print(f"  [OK] {item['year']}年: {item['path']}")
    
    if results['failed']:
        print("\n下载失败的年报:")
        for item in results['failed']:
            print(f"  [X] {item['year']}年: {item['reason']}")
    
    print("=" * 80)
    
    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='下载港股年报PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 从本地HTML文件解析下载（推荐）
  python 09_下载港股年报PDF.py --html "搜索结果.html" --save_dir "小米年报" --symbol 01810
  
  # 直接下载：已知PDF链接时
  python 09_下载港股年报PDF.py --url "https://www1.hkexnews.hk/listedco/.../xxx.pdf"
  
  # 手动下载模式：交互式输入多个链接
  python 09_下载港股年报PDF.py --manual

操作步骤:
  1. 打开 https://www1.hkexnews.hk/search/titlesearch.xhtml
  2. 输入股票代码，选择"年度报告"，点击搜索
  3. Ctrl+S 保存网页为HTML文件
  4. 运行: python 09_下载港股年报PDF.py --html "保存的文件.html"
        """
    )
    parser.add_argument('--html', type=str, help='本地HTML文件路径（从港交所保存的搜索结果页面）')
    parser.add_argument('--symbol', type=str, help='股票代码（用于生成文件名，如 01810）')
    parser.add_argument('--years', type=str, help='指定下载年份，逗号分隔（如 2022,2023,2024）')
    parser.add_argument('--save_dir', type=str, default='港股年报PDF', help='保存目录')
    parser.add_argument('--url', type=str, help='直接下载指定PDF链接')
    parser.add_argument('--manual', action='store_true', help='进入手动下载模式')
    
    args = parser.parse_args()
    
    # 从HTML文件解析下载
    if args.html:
        years = None
        if args.years:
            years = [int(y.strip()) for y in args.years.split(',')]
        download_from_html(args.html, args.save_dir, args.symbol, years)
        return
    
    # 手动下载模式
    if args.manual:
        manual_download_mode(args.save_dir)
        return
    
    # 直接下载指定URL
    if args.url:
        filename = args.url.split('/')[-1]
        if not filename.endswith('.pdf'):
            filename = f"港股年报.pdf"
        save_path = os.path.join(args.save_dir, filename)
        
        os.makedirs(args.save_dir, exist_ok=True)
        download_pdf_from_url(args.url, save_path)
        return
    
    # 交互模式
    print("=" * 60)
    print("港股年报PDF下载工具")
    print("数据来源：香港交易所披露易（HKEXnews）")
    print("=" * 60)
    print("\n[!] 由于港交所搜索接口限制，推荐使用HTML解析模式：")
    print("1. 打开 https://www1.hkexnews.hk/search/titlesearch.xhtml")
    print("2. 搜索目标公司的年度报告")
    print("3. Ctrl+S 保存网页为HTML文件")
    print("4. 运行: python 09_下载港股年报PDF.py --html '文件路径.html'\n")
    
    choice = input("是否进入手动URL输入模式？(y/N): ").strip().lower()
    if choice == 'y':
        manual_download_mode(args.save_dir)


if __name__ == "__main__":
    main()
