"""
下载上市公司年度报告PDF

支持从以下渠道下载：
1. 巨潮资讯网（cninfo.com.cn）- 推荐
2. 上海证券交易所
3. 深圳证券交易所

下载方法：
1. 手动下载（推荐，最简单可靠）
2. 使用浏览器自动化工具（Selenium）
3. 分析网站API（需要技术能力）

注意：需要遵守网站的使用条款，不要频繁请求
"""

import os
import re
import time
import requests
from typing import Optional, List, Dict
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# 如果需要使用Selenium，需要安装：pip install selenium
# 并下载对应的浏览器驱动（ChromeDriver等）
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠ Selenium未安装，如需使用浏览器自动化功能，请运行: pip install selenium")

def get_stock_market(symbol: str) -> str:
    """
    判断股票所属交易所
    
    参数:
        symbol: 股票代码（6位数字）
    
    返回:
        'SH' 或 'SZ'
    """
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    
    if symbol_clean.startswith(('600', '601', '603', '605', '688')):
        return 'SH'  # 上海证券交易所
    elif symbol_clean.startswith(('000', '001', '002', '300')):
        return 'SZ'  # 深圳证券交易所
    else:
        return 'SZ'  # 默认深交所

def search_announcements_cninfo(symbol: str, year: Optional[int] = None, announcement_type: str = "年度报告") -> List[Dict]:
    """
    从巨潮资讯网搜索公告
    
    参数:
        symbol: 股票代码
        year: 年份（可选，如果为None则搜索所有年份）
        announcement_type: 公告类型，默认为"年度报告"
    
    返回:
        公告列表，每个元素包含公告信息（包括announcementId）
    """
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    
    # 判断交易所
    if symbol_clean.startswith(('600', '601', '603', '605', '688')):
        plate = 'sse'  # 上交所
    else:
        plate = 'szse'  # 深交所
    
    # 巨潮资讯网公告查询API（根据实际网站调整）
    # 注意：这个API可能需要根据网站实际情况调整
    search_url = "http://www.cninfo.com.cn/new/information/topSearch/query"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://www.cninfo.com.cn/',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # 构建搜索参数
    params = {
        'keyWord': symbol_clean,
        'maxSecMarket': plate,
        'minSecMarket': plate,
    }
    
    # 构建完整搜索URL
    from urllib.parse import urlencode
    full_search_url = f"{search_url}?{urlencode(params)}"
    print(f"[搜索URL] {full_search_url}")
    
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            try:
                data = response.json()
            except:
                return []
            
            announcements = []
            
            # 解析返回的数据结构（需要根据实际返回格式调整）
            # 可能的格式：{'records': [...]} 或直接是列表
            records = []
            if isinstance(data, dict):
                # 尝试多种可能的键名
                for key in ['records', 'data', 'list', 'announcements']:
                    if key in data:
                        records = data[key]
                        break
            elif isinstance(data, list):
                records = data
            
            # 筛选公告
            for record in records:
                if not isinstance(record, dict):
                    continue
                
                title = str(record.get('announcementTitle', record.get('title', '')))
                time_str = str(record.get('announcementTime', record.get('time', record.get('announcementDate', ''))))
                
                # 筛选年度报告
                if announcement_type in title:
                    # 如果指定了年份，检查年份
                    if year is None or str(year) in time_str:
                        announcements.append(record)
            
            return announcements
        else:
            return []
            
    except Exception as e:
        return []

def download_pdf_from_cninfo_url(url: str, save_dir: str = "年报PDF", filename: Optional[str] = None) -> Optional[str]:
    """
    从巨潮资讯网公告详情页下载PDF
    
    参数:
        url: 公告详情页URL（如：https://www.cninfo.com.cn/new/disclosure/detail?plate=sse&orgId=...）
        save_dir: 保存目录
        filename: 保存的文件名（如果为None，自动生成）
    
    返回:
        下载的文件路径，如果失败返回None
    """
    try:
        os.makedirs(save_dir, exist_ok=True)
        
        # 从URL中提取参数
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        stock_code = params.get('stockCode', [''])[0]
        announcement_id = params.get('announcementId', [''])[0]
        announcement_time = params.get('announcementTime', [''])[0]
        
        if not announcement_id:
            return None
        
        # 构建PDF下载URL（尝试多种可能的格式）
        # 格式1：直接下载接口
        download_urls = [
            f"http://www.cninfo.com.cn/new/disclosure/detail/download?announcementId={announcement_id}",
            f"https://www.cninfo.com.cn/new/disclosure/detail/download?announcementId={announcement_id}",
            f"http://static.cninfo.com.cn/finalpage/{announcement_time.replace('-', '')}/{announcement_id}.PDF",
            f"http://www.cninfo.com.cn/new/disclosure/detail?plate={params.get('plate', [''])[0]}&orgId={params.get('orgId', [''])[0]}&stockCode={stock_code}&announcementId={announcement_id}&announcementTime={announcement_time}&download=true",
        ]
        
        print(f"[PDF下载URL列表]")
        for idx, download_url in enumerate(download_urls, 1):
            print(f"  {idx}. {download_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': url,
            'Accept': 'application/pdf,application/octet-stream,*/*'
        }
        
        # 尝试多个下载URL
        response = None
        success_url = None
        
        for idx, download_url in enumerate(download_urls, 1):
            try:
                print(f"[尝试下载 {idx}/{len(download_urls)}] {download_url}")
                test_response = requests.get(download_url, headers=headers, timeout=60, stream=True, allow_redirects=True)
                
                print(f"  -> 状态码: {test_response.status_code}, Content-Type: {test_response.headers.get('Content-Type', 'N/A')}, Content-Length: {test_response.headers.get('Content-Length', 'N/A')}")
                
                # 检查响应
                if test_response.status_code == 200:
                    content_type = test_response.headers.get('Content-Type', '')
                    content_length = test_response.headers.get('Content-Length', '0')
                    # 检查是否是PDF（通过Content-Type或文件大小判断）
                    if 'pdf' in content_type.lower() or int(content_length) > 10000:  # PDF文件通常大于10KB
                        response = test_response
                        success_url = download_url
                        print(f"  -> ✓ 找到有效PDF")
                        break
                    else:
                        print(f"  -> ✗ 不是有效PDF")
                elif test_response.status_code in [302, 301]:
                    # 重定向，尝试跟随
                    redirect_url = test_response.headers.get('Location')
                    if redirect_url:
                        print(f"[重定向URL] {redirect_url}")
                        redirect_response = requests.get(redirect_url, headers=headers, timeout=60, stream=True)
                        if redirect_response.status_code == 200:
                            response = redirect_response
                            success_url = redirect_url
                            break
            except Exception as e:
                continue
        
        if response is None or response.status_code != 200:
            print(f"[下载失败] 所有URL尝试失败，最后状态码: {response.status_code if response else 'None'}")
            return None
        
        if success_url:
            print(f"[成功URL] {success_url}")
        
        # 下载成功，保存文件
        if response.status_code == 200:
            # 生成文件名
            if not filename:
                year = announcement_time[:4] if announcement_time else "未知"
                filename = f"{stock_code}_{year}年年度报告.pdf"
            
            filepath = os.path.join(save_dir, filename)
            
            # 保存文件
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return filepath
        else:
            return None
            
    except Exception as e:
        return None

def download_from_cninfo_with_id(symbol: str, announcement_id: str, announcement_time: str = "", save_dir: str = "年报PDF") -> Optional[str]:
    """
    使用已知的announcementId下载年报PDF
    
    参数:
        symbol: 股票代码
        announcement_id: 公告ID
        announcement_time: 公告时间（可选，格式：2020-04-10）
        save_dir: 保存目录
    
    返回:
        下载的文件路径，如果失败返回None
    """
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    
    # 判断交易所
    if symbol_clean.startswith(('600', '601', '603', '605', '688')):
        plate = 'sse'
    else:
        plate = 'szse'
    
    # 构建orgId（尝试多种格式）
    org_id = f"gssh{symbol_clean}"
    
    # 构建公告详情页URL
    detail_url = f"https://www.cninfo.com.cn/new/disclosure/detail?plate={plate}&orgId={org_id}&stockCode={symbol_clean}&announcementId={announcement_id}"
    if announcement_time:
        detail_url += f"&announcementTime={announcement_time}"
    
    print(f"[公告详情页URL] {detail_url}")
    
    # 生成文件名
    year = announcement_time[:4] if announcement_time else "未知"
    filename = f"{symbol_clean}_{year}年年度报告.pdf"
    
    return download_pdf_from_cninfo_url(detail_url, save_dir, filename)

def download_from_cninfo(symbol: str, year: int, save_dir: str = "年报PDF") -> Optional[str]:
    """
    从巨潮资讯网下载年报PDF
    
    参数:
        symbol: 股票代码
        year: 年份
        save_dir: 保存目录
    
    返回:
        下载的文件路径，如果失败返回None
    """
    try:
        # 搜索年报公告
        announcements = search_announcements_cninfo(symbol, year)
        
        if not announcements:
            return None
        
        # 使用第一个匹配的公告
        announcement = announcements[0]
        announcement_id = announcement.get('announcementId') or announcement.get('id')
        announcement_time = announcement.get('announcementTime') or announcement.get('time') or announcement.get('announcementDate', '')
        
        if not announcement_id:
            return None
        
        # 构建公告详情页URL
        symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
        if symbol_clean.startswith(('600', '601', '603', '605', '688')):
            plate = 'sse'
        else:
            plate = 'szse'
        
        # 尝试从公告数据中获取orgId，如果没有则使用默认格式
        org_id = announcement.get('orgId') or announcement.get('orgCode') or f"gssh{symbol_clean}"
        
        detail_url = f"https://www.cninfo.com.cn/new/disclosure/detail?plate={plate}&orgId={org_id}&stockCode={symbol_clean}&announcementId={announcement_id}"
        if announcement_time:
            detail_url += f"&announcementTime={announcement_time}"
        
        print(f"[公告详情页URL] {detail_url}")
        
        # 下载PDF
        filename = f"{symbol_clean}_{year}年年度报告.pdf"
        return download_pdf_from_cninfo_url(detail_url, save_dir, filename)
            
    except Exception as e:
        return None

def download_from_sse(symbol: str, year: int, save_dir: str = "年报PDF") -> Optional[str]:
    """
    从上海证券交易所下载年报PDF
    
    参数:
        symbol: 股票代码
        year: 年份
        save_dir: 保存目录
    
    返回:
        下载的文件路径，如果失败返回None
    """
    try:
        os.makedirs(save_dir, exist_ok=True)
        return None
        
    except Exception as e:
        return None

def download_from_szse(symbol: str, year: int, save_dir: str = "年报PDF") -> Optional[str]:
    """
    从深圳证券交易所下载年报PDF
    
    参数:
        symbol: 股票代码
        year: 年份
        save_dir: 保存目录
    
    返回:
        下载的文件路径，如果失败返回None
    """
    try:
        os.makedirs(save_dir, exist_ok=True)
        return None
        
    except Exception as e:
        return None

def download_from_cninfo_url(url: str, save_dir: str = "年报PDF") -> Optional[str]:
    """
    直接从巨潮资讯网公告详情页URL下载PDF
    
    参数:
        url: 公告详情页URL（完整URL，如：https://www.cninfo.com.cn/new/disclosure/detail?plate=sse&orgId=...）
        save_dir: 保存目录
    
    返回:
        下载的文件路径，如果失败返回None
    
    示例:
        url = "https://www.cninfo.com.cn/new/disclosure/detail?plate=sse&orgId=gssh0600728&stockCode=600728&announcementId=1207475136&announcementTime=2020-04-10"
        download_from_cninfo_url(url)
    """
    # 从URL中提取信息
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    stock_code = params.get('stockCode', [''])[0]
    announcement_time = params.get('announcementTime', [''])[0]
    year = announcement_time[:4] if announcement_time else "未知"
    
    # 生成文件名
    filename = f"{stock_code}_{year}年年度报告.pdf"
    
    return download_pdf_from_cninfo_url(url, save_dir, filename)

def download_annual_report(symbol: str, year: int, save_dir: str = "年报PDF", source: str = "auto") -> Optional[str]:
    """
    下载年报PDF
    
    参数:
        symbol: 股票代码
        year: 年份
        save_dir: 保存目录
        source: 数据源，可选 'cninfo', 'sse', 'szse', 'auto'（自动选择）
    
    返回:
        下载的文件路径，如果失败返回None
    """
    symbol_clean = symbol.replace('.SZ', '').replace('.SH', '')
    
    # 自动选择数据源（默认使用巨潮资讯网，支持所有股票）
    if source == "auto":
        source = 'cninfo'
    
    # 根据数据源下载
    if source == 'cninfo':
        return download_from_cninfo(symbol_clean, year, save_dir)
    elif source == 'sse':
        return download_from_sse(symbol_clean, year, save_dir)
    elif source == 'szse':
        return download_from_szse(symbol_clean, year, save_dir)
    else:
        print(f"✗ 未知的数据源: {source}")
        return None

def batch_download_annual_reports(symbol: str, years: List[int], save_dir: str = "年报PDF") -> Dict[int, str]:
    """
    批量下载多年年报
    
    参数:
        symbol: 股票代码
        years: 年份列表
        save_dir: 保存目录
    
    返回:
        字典，键为年份，值为文件路径
    """
    results = {}
    
    for year in sorted(years):
        file_path = download_annual_report(symbol, year, save_dir)
        if file_path:
            results[year] = file_path
        else:
            results[year] = None
        
        # 避免请求过快
        time.sleep(1)
    
    return results

def download_with_selenium_cninfo(symbol: str, year: int, save_dir: str = "年报PDF", headless: bool = False) -> Optional[str]:
    """
    使用Selenium从巨潮资讯网下载年报PDF（示例）
    
    参数:
        symbol: 股票代码
        year: 年份
        save_dir: 保存目录
        headless: 是否使用无头模式
    
    返回:
        下载的文件路径，如果失败返回None
    
    注意：
    1. 需要安装Selenium: pip install selenium
    2. 需要下载ChromeDriver并配置PATH
    3. 此函数为示例，需要根据网站实际结构调整
    """
    if not SELENIUM_AVAILABLE:
        return None
    
    try:
        os.makedirs(save_dir, exist_ok=True)
        
        # 配置Chrome浏览器
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless')
        
        # 设置下载目录
        prefs = {
            "download.default_directory": os.path.abspath(save_dir),
            "download.prompt_for_download": False,
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=options)
        
        try:
            # 访问巨潮资讯网搜索页面
            search_url = f"http://www.cninfo.com.cn/new/information/topSearch/query?keyWord={symbol}"
            driver.get(search_url)
            
            # 等待页面加载
            time.sleep(2)
            
            # 这里需要根据实际网页结构来定位元素
            # 示例：查找年报链接并点击下载
            # 注意：实际实现需要分析网页HTML结构
            
            return None
            
        finally:
            driver.quit()
            
    except Exception as e:
        return None

def main():
    """
    主函数
    
    使用说明：
    
    方法1：手动下载（推荐，最简单可靠）
    ==========================================
    1. 巨潮资讯网（推荐）：
       - 访问：http://www.cninfo.com.cn
       - 在搜索框输入股票代码（如：600728）
       - 点击"定期报告"
       - 筛选"年度报告"
       - 选择年份，点击下载PDF
    
    2. 上海证券交易所：
       - 访问：http://www.sse.com.cn
       - 点击"披露" -> "定期报告"
       - 搜索股票代码，筛选年报
    
    3. 深圳证券交易所：
       - 访问：http://www.szse.cn
       - 点击"信息披露" -> "定期报告"
       - 搜索股票代码，筛选年报
    
    方法2：使用浏览器自动化（需要技术能力）
    ==========================================
    1. 安装Selenium: pip install selenium
    2. 下载ChromeDriver: https://chromedriver.chromium.org/
    3. 分析目标网站的HTML结构
    4. 编写自动化脚本
    
    方法3：分析网站API（高级）
    ==========================================
    1. 使用浏览器开发者工具（F12）
    2. 分析网络请求，找到API接口
    3. 模拟请求下载PDF
    
    推荐工具：
    - 浏览器开发者工具（F12）
    - Postman（测试API）
    - Selenium（浏览器自动化）
    """
    print("=" * 80)
    print("上市公司年度报告PDF下载工具")
    print("=" * 80)
    print("\n📋 下载方法说明：")
    print("\n【方法1】手动下载（推荐）")
    print("-" * 80)
    print("1. 访问巨潮资讯网：http://www.cninfo.com.cn")
    print("2. 搜索股票代码（如：600728）")
    print("3. 点击'定期报告' -> 筛选'年度报告'")
    print("4. 选择年份，下载PDF")
    print("\n【方法2】浏览器自动化（需要Selenium）")
    print("-" * 80)
    print("1. 安装: pip install selenium")
    print("2. 下载ChromeDriver并配置")
    print("3. 使用download_with_selenium_cninfo()函数（需要根据网站调整）")
    print("\n【方法3】分析API（高级）")
    print("-" * 80)
    print("1. 使用浏览器F12开发者工具")
    print("2. 分析网络请求，找到PDF下载链接")
    print("3. 使用requests库直接下载")
    print("\n【方法4】直接使用URL下载（最简单）")
    print("-" * 80)
    print("如果你已经有公告详情页的URL，可以直接使用：")
    print("download_from_cninfo_url(url)")
    print("\nURL格式示例：")
    print("https://www.cninfo.com.cn/new/disclosure/detail?plate=sse&orgId=gssh0600728&stockCode=600728&announcementId=1207475136&announcementTime=2020-04-10")
    print("\n" + "=" * 80)
    print("\n💡 提示：")
    print("- 手动下载最可靠，适合少量文件")
    print("- 使用URL下载：如果你有公告URL，可以直接下载")
    print("- 自动化下载适合批量处理，但需要技术能力")
    print("- 建议先手动下载几个文件，了解网站结构后再考虑自动化")
    print("=" * 80)
    
    # ========== 实际执行代码 ==========
    # 取消下面的注释来执行下载
    
    # 示例1：使用URL直接下载（如果你有公告详情页URL）
    # url = "https://www.cninfo.com.cn/new/disclosure/detail?plate=sse&orgId=gssh0600728&stockCode=600728&announcementId=1207475136&announcementTime=2020-04-10"
    # print("\n" + "=" * 80)
    # print("示例1：使用URL直接下载")
    # print("=" * 80)
    # download_from_cninfo_url(url, save_dir="年报PDF")
    
    # 示例2：使用股票代码和年份下载（自动搜索announcementId）
    # symbol = "600728"
    # year = 2020
    # print("\n" + "=" * 80)
    # print(f"示例2：下载 {symbol} {year} 年年报")
    # print("=" * 80)
    # download_annual_report(symbol, year, save_dir="年报PDF")
    
    # 示例3：批量下载多年年报
    # symbol = "600728"
    # years = [2020, 2021, 2022, 2023, 2024]
    # print("\n" + "=" * 80)
    # print(f"示例3：批量下载 {symbol} 的年报")
    # print("=" * 80)
    # batch_download_annual_reports(symbol, years, save_dir="年报PDF")
    
    # 示例4：先搜索公告，查看announcementId
    # symbol = "600728"
    # year = 2020
    # print("\n" + "=" * 80)
    # print(f"示例4：搜索 {symbol} {year} 年的年报公告")
    # print("=" * 80)
    # announcements = search_announcements_cninfo(symbol, year)
    # if announcements:
    #     print(f"\n找到 {len(announcements)} 个公告")
    #     for ann in announcements:
    #         print(f"  - {ann.get('announcementTitle', '未知')}")
    #         print(f"    ID: {ann.get('announcementId', '未知')}")
    #         print(f"    时间: {ann.get('announcementTime', '未知')}")
    
    # ========== 实际执行示例（取消注释来执行）==========
    
    # 方式1：使用URL直接下载（推荐，如果你有URL）
    # url = "https://www.cninfo.com.cn/new/disclosure/detail?plate=sse&orgId=gssh0600728&stockCode=600728&announcementId=1207475136&announcementTime=2020-04-10"
    # download_from_cninfo_url(url, save_dir="年报PDF")
    
    # 方式2：使用股票代码和年份（自动搜索announcementId）
    symbol = "600728"
    year = 2020
    result = download_annual_report(symbol, year, save_dir="年报PDF")
    if result:
        print(f"✓ 下载成功: {result}")
    else:
        print(f"✗ 下载失败")

if __name__ == "__main__":
    main()

