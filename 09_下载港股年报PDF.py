# -*- coding: utf-8 -*-
"""
下载港股上市公司年度报告PDF

数据来源：香港交易所披露易（HKEXnews）
网址：https://www.hkexnews.hk

⚠️ 重要说明：
港交所披露易不提供简单的API接口，数据通过JavaScript动态加载。
本脚本提供两种下载方式：
1. 自动搜索下载（需要Selenium浏览器自动化）
2. 手动输入URL下载（用户从网站复制PDF链接）

使用方法：
1. 命令行：python 09_下载港股年报PDF.py --symbol 00700 --start_year 2020 --end_year 2024
2. 交互式：python 09_下载港股年报PDF.py
3. 手动URL：python 09_下载港股年报PDF.py --url "PDF链接" --save_dir "保存目录"

注意：
- 股票代码为5位数字，如 00700（腾讯）、00941（中国移动）
- 年报通常在次年3-4月发布
"""

import os
import re
import time
import requests
from typing import Optional, List, Dict
from datetime import datetime
import argparse
import webbrowser


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
                    print(f"  ✓ 下载成功: {save_path}")
                    print(f"    文件大小: {file_size/1024/1024:.2f} MB")
                    return True
                else:
                    print(f"    -> ✗ 文件太小 ({file_size}字节)，可能不是有效PDF")
                    os.remove(save_path)
            else:
                print(f"    -> ✗ 响应不是PDF格式")
        else:
            print(f"    -> ✗ HTTP状态码: {response.status_code}")
            
    except Exception as e:
        print(f"    -> ✗ 下载失败: {str(e)}")
    
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
        print("  ⚠ Selenium未安装，请运行: pip install selenium")
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
                        print(f"    ✓ {title[:50] if title else href[-50:]}...")
            except Exception as e:
                continue
        
        driver.quit()
        
    except Exception as e:
        print(f"  ✗ Selenium错误: {e}")
    
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
        print(f"  ⚠ 未找到 {year} 年的年报")
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
            print(f"\n✓ 文件已保存到: {save_path}\n")
        else:
            print(f"\n✗ 下载失败，请检查链接是否正确\n")


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
        use_selenium: 是否使用Selenium自动搜索
    
    返回:
        下载结果统计
    """
    results = {
        'success': [],
        'failed': []
    }
    
    print("=" * 80)
    print("港股年报批量下载")
    print(f"股票代码: {symbol}")
    print(f"年份范围: {start_year} - {end_year}")
    print(f"保存目录: {save_dir}")
    print(f"搜索方式: {'Selenium自动搜索' if use_selenium else '手动搜索'}")
    print("=" * 80)
    
    if not use_selenium:
        # 打开搜索页面让用户手动查找
        print("\n⚠ 港交所披露易需要手动搜索，正在打开浏览器...")
        
        for year in range(start_year, end_year + 1):
            print(f"\n[{year}年] 打开搜索页面...")
            open_hkex_search(symbol, year)
            time.sleep(2)
        
        print("\n" + "=" * 80)
        print("搜索页面已打开")
        print("请在浏览器中找到年报PDF链接，然后进入手动下载模式")
        print("=" * 80)
        
        manual_download_mode(save_dir)
        return results
    
    # 使用Selenium自动搜索
    for year in range(start_year, end_year + 1):
        filepath = download_hk_annual_report_selenium(symbol, year, save_dir)
        
        if filepath:
            results['success'].append({
                'year': year,
                'path': filepath
            })
        else:
            results['failed'].append({
                'year': year,
                'reason': '未找到或下载失败'
            })
        
        time.sleep(2)  # 避免请求过快
    
    # 打印汇总
    print("\n" + "=" * 80)
    print("下载完成！")
    print(f"成功: {len(results['success'])} 个")
    print(f"失败: {len(results['failed'])} 个")
    
    if results['success']:
        print("\n成功下载的年报:")
        for item in results['success']:
            print(f"  ✓ {item['year']}年: {item['path']}")
    
    if results['failed']:
        print("\n下载失败的年报:")
        for item in results['failed']:
            print(f"  ✗ {item['year']}年: {item['reason']}")
    
    print("=" * 80)
    
    return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='下载港股年报PDF',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 手动模式（推荐）：打开搜索页面 + 手动下载
  python 09_下载港股年报PDF.py --symbol 00700 --start_year 2023 --end_year 2023
  
  # 自动模式：使用Selenium自动搜索（需要安装selenium和chromedriver）
  python 09_下载港股年报PDF.py --symbol 00700 --start_year 2020 --end_year 2024 --selenium
  
  # 直接下载：已知PDF链接时
  python 09_下载港股年报PDF.py --url "https://www1.hkexnews.hk/listedco/.../xxx.pdf"
  
  # 手动下载模式：交互式输入多个链接
  python 09_下载港股年报PDF.py --manual
        """
    )
    parser.add_argument('--symbol', type=str, help='股票代码（5位，如 00700）')
    parser.add_argument('--start_year', type=int, help='起始年份')
    parser.add_argument('--end_year', type=int, help='结束年份')
    parser.add_argument('--save_dir', type=str, default='港股年报PDF', help='保存目录')
    parser.add_argument('--url', type=str, help='直接下载指定PDF链接')
    parser.add_argument('--selenium', action='store_true', help='使用Selenium自动搜索')
    parser.add_argument('--manual', action='store_true', help='进入手动下载模式')
    
    args = parser.parse_args()
    
    # 手动下载模式
    if args.manual:
        manual_download_mode(args.save_dir)
        return
    
    # 直接下载指定URL
    if args.url:
        # 生成文件名
        filename = args.url.split('/')[-1]
        if not filename.endswith('.pdf'):
            filename = f"港股年报.pdf"
        save_path = os.path.join(args.save_dir, filename)
        
        os.makedirs(args.save_dir, exist_ok=True)
        download_pdf_from_url(args.url, save_path)
        return
    
    # 交互模式或批量下载
    symbol = args.symbol
    start_year = args.start_year
    end_year = args.end_year
    
    if not symbol:
        print("=" * 60)
        print("港股年报PDF下载工具")
        print("数据来源：香港交易所披露易（HKEXnews）")
        print("=" * 60)
        print("\n⚠ 注意：港交所披露易数据通过JavaScript加载")
        print("本工具提供两种下载方式：")
        print("1. 手动搜索：打开浏览器搜索页面，手动复制链接下载")
        print("2. 自动搜索：使用Selenium自动化（需要安装）\n")
        
        symbol = input("请输入股票代码（5位，如 00700）: ").strip()
    
    if not start_year:
        start_year = int(input("请输入起始年份（如 2020）: ").strip())
    
    if not end_year:
        end_year = int(input("请输入结束年份（如 2024）: ").strip())
    
    # 询问是否使用Selenium
    use_selenium = args.selenium
    if not use_selenium:
        choice = input("\n是否使用Selenium自动搜索？(y/N): ").strip().lower()
        use_selenium = choice == 'y'
    
    # 执行下载
    batch_download_hk_reports(symbol, start_year, end_year, args.save_dir, use_selenium)


if __name__ == "__main__":
    main()
