# -*- coding: utf-8 -*-
"""测试获取港股员工数量的各种方式"""
import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test_eastmoney_hk_profile():
    """测试东方财富港股公司概况API"""
    print("=" * 60)
    print("测试东方财富港股公司概况API")
    print("=" * 60)
    
    # 东方财富港股公司概况API
    url = "https://emweb.securities.eastmoney.com/PC_HKF10/CompanyInfo/PageAjax"
    
    params = {
        'code': '00700',
        'type': 'soft'
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://emweb.securities.eastmoney.com/',
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"Keys: {data.keys() if isinstance(data, dict) else type(data)}")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    except Exception as e:
        print(f"Error: {e}")


def test_eastmoney_hk_f10():
    """测试东方财富港股F10数据"""
    print("\n" + "=" * 60)
    print("测试东方财富港股F10员工数据")
    print("=" * 60)
    
    # 尝试不同的API端点
    urls = [
        "https://emweb.securities.eastmoney.com/PC_HKF10/EmployeeInfo/PageAjax?code=00700",
        "https://datacenter.eastmoney.com/securities/api/data/v1/get?reportName=RPT_HKF10_FN_EMPLOYEE&columns=ALL&filter=(SECUCODE=\"00700.HK\")",
        "https://push2.eastmoney.com/api/qt/slist/get?secid=116.00700&fields=f1,f2,f3",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://emweb.securities.eastmoney.com/',
    }
    
    for url in urls:
        print(f"\nTrying: {url[:80]}...")
        try:
            r = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {r.status_code}")
            if r.status_code == 200 and len(r.text) > 10:
                try:
                    data = r.json()
                    print(f"Response: {json.dumps(data, ensure_ascii=False, indent=2)[:1000]}")
                except:
                    print(f"Text: {r.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")


def test_xueqiu_hk():
    """测试雪球港股数据"""
    print("\n" + "=" * 60)
    print("测试雪球港股员工数据")
    print("=" * 60)
    
    # 雪球API需要先获取token
    session = requests.Session()
    
    headers = {
        'User-Agent': 'Mozilla/5.0',
    }
    
    # 先访问主页获取cookie
    session.get('https://xueqiu.com/', headers=headers)
    
    # 获取公司信息
    url = "https://stock.xueqiu.com/v5/stock/f10/cn/company.json"
    params = {
        'symbol': '00700',
        'type': 'hk'
    }
    
    try:
        r = session.get(url, params=params, headers=headers, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Response: {json.dumps(data, ensure_ascii=False, indent=2)[:1500]}")
    except Exception as e:
        print(f"Error: {e}")


def test_akshare_hk():
    """测试akshare港股公司信息"""
    print("\n" + "=" * 60)
    print("测试akshare港股公司信息")
    print("=" * 60)
    
    import akshare as ak
    
    # 尝试获取港股公司概况
    try:
        df = ak.stock_hk_company_profile_em(symbol="00700")
        print("stock_hk_company_profile_em:")
        print(df)
        
        # 查找员工相关字段
        if df is not None:
            for col in df.columns:
                if '员工' in str(col) or 'employ' in str(col).lower():
                    print(f"Found employee column: {col}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 尝试获取港股财务指标
    try:
        df = ak.stock_hk_financial_indicator_em(symbol="00700")
        print("\nstock_hk_financial_indicator_em:")
        print(df.columns.tolist() if df is not None else None)
        print(df.head() if df is not None else None)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_eastmoney_hk_profile()
    test_eastmoney_hk_f10()
    test_xueqiu_hk()
    test_akshare_hk()
