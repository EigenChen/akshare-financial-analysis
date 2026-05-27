"""
GuruFocus 美股指数 PE 历史数据抓取

从 GuruFocus 抓取纳斯达克 100 和标普 500 的 PE 历史数据。

数据文件:
    data/us_index_pe/nasdaq100_pe_history.csv   历史数据（GuruFocus Historical Data）
    data/us_index_pe/sp500_pe_history.csv        历史数据（GuruFocus Historical Data）
    data/us_index_pe/us_index_pe_latest.csv      实时 PE（页面顶部实时值）

用法:
    python -u scrape_gurufocus_pe.py nasdaq100       全量抓取
    python -u scrape_gurufocus_pe.py sp500            全量抓取
    python -u scrape_gurufocus_pe.py all              全量抓取两个指数
    python -u scrape_gurufocus_pe.py update           增量更新（只抓第一页）
    python -u scrape_gurufocus_pe.py update nasdaq100 增量更新指定指数
"""

import csv
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


INDICES = {
    "nasdaq100": {
        "name": "纳斯达克100",
        "url": "https://www.gurufocus.com/economic_indicators/6778/nasdaq-100-pe-ratio",
    },
    "sp500": {
        "name": "标普500",
        "url": "https://www.gurufocus.com/economic_indicators/57/sp-500-pe-ratio",
    },
}

PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "us_index_pe")


def log(msg):
    print(msg, flush=True)


def create_driver():
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(options=opts)


def get_total_pages(driver):
    try:
        pager = driver.find_element(By.CLASS_NAME, "el-pager")
        items = pager.find_elements(By.TAG_NAME, "li")
        return int(items[-1].text)
    except Exception:
        return 0


def scrape_page(driver):
    """抓取当前页面的表格数据，返回 (realtime_row, history_rows)

    页面表格第一行是实时值（如 2026-05-26），之后是 Historical Data。
    返回:
        realtime_row: (date, pe, yoy) 或 None
        history_rows: [(date, pe, yoy), ...]
    """
    tables = driver.find_elements(By.TAG_NAME, "table")
    for table in tables:
        header = table.find_elements(By.TAG_NAME, "th")
        header_texts = [h.text for h in header]
        if "Date" in header_texts and "Value" in header_texts:
            rows = table.find_elements(By.TAG_NAME, "tr")
            all_rows = []
            for row in rows[1:]:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 2:
                    date = cols[0].text.strip()
                    value = cols[1].text.strip()
                    yoy = cols[2].text.strip() if len(cols) > 2 else ""
                    all_rows.append((date, value, yoy))

            if not all_rows:
                return None, []

            # 实时值判断：第一行日期与第二行日期间隔 > 1 天
            # Historical Data 是日频，实时值通常在两个交易日之间
            realtime_row = all_rows[0]
            history_rows = all_rows[1:]

            if len(all_rows) >= 2:
                from datetime import datetime
                try:
                    d0 = datetime.strptime(all_rows[0][0], "%Y-%m-%d")
                    d1 = datetime.strptime(all_rows[1][0], "%Y-%m-%d")
                    if (d0 - d1).days <= 1:
                        # 第一行也是历史数据（没有实时值）
                        realtime_row = None
                        history_rows = all_rows
                except ValueError:
                    pass

            return realtime_row, history_rows
    return None, []


def click_next_page(driver):
    pagination = driver.find_element(By.CLASS_NAME, "data-table-footer-pagination")
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", pagination
    )
    time.sleep(0.3)
    next_btn = driver.find_element(By.CLASS_NAME, "btn-next")
    driver.execute_script("arguments[0].click();", next_btn)
    time.sleep(1.5)


def save_history_csv(index_key, data):
    """保存历史数据 CSV（不含实时值）"""
    csv_path = os.path.join(DATA_DIR, f"{index_key}_pe_history.csv")
    with open(csv_path, "w", newline="", encoding="utf-8", errors="replace") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "pe", "yoy"])
        writer.writerows(data)


def load_history_csv(index_key):
    """加载历史数据 CSV"""
    csv_path = os.path.join(DATA_DIR, f"{index_key}_pe_history.csv")
    if not os.path.exists(csv_path):
        return []
    data = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            data.append(tuple(row))
    return data


def save_latest_csv(index_key, date, pe):
    """更新实时 PE 值到 latest CSV"""
    csv_path = os.path.join(DATA_DIR, "us_index_pe_latest.csv")
    os.makedirs(DATA_DIR, exist_ok=True)

    # 读取已有数据
    latest = {}
    if os.path.exists(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 3:
                    latest[row[0]] = (row[1], row[2])

    # 更新
    latest[index_key] = (date, pe)

    # 写回
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "date", "pe"])
        for key in ["nasdaq100", "sp500"]:
            if key in latest:
                writer.writerow([key, latest[key][0], latest[key][1]])


def scrape_index(index_key, max_pages=None):
    """全量抓取单个指数的 PE 历史数据"""
    cfg = INDICES[index_key]
    os.makedirs(DATA_DIR, exist_ok=True)

    driver = create_driver()
    try:
        log(f"[{cfg['name']}] 正在加载页面...")
        driver.get(cfg["url"])
        time.sleep(8)

        if "Just a moment" in driver.title:
            log(f"[{cfg['name']}] Cloudflare 挑战中，等待...")
            time.sleep(15)

        if "Just a moment" in driver.title:
            log(f"[{cfg['name']}] 无法通过 Cloudflare，退出")
            return []

        total_pages = get_total_pages(driver)
        if max_pages:
            total_pages = min(total_pages, max_pages)
        log(f"[{cfg['name']}] 共 {total_pages} 页，开始抓取...")

        all_history = []
        realtime_row = None

        for page in range(1, total_pages + 1):
            rt, hist = scrape_page(driver)
            if page == 1 and rt:
                realtime_row = rt
            all_history.extend(hist)

            if page % 20 == 0 or page == total_pages:
                log(f"[{cfg['name']}] 第 {page}/{total_pages} 页，累计 {len(all_history)} 行")
                save_history_csv(index_key, all_history)

            if page < total_pages:
                click_next_page(driver)

        # 保存
        save_history_csv(index_key, all_history)
        if realtime_row:
            save_latest_csv(index_key, realtime_row[0], realtime_row[1])

        log(f"[{cfg['name']}] 完成！历史数据 {len(all_history)} 行"
            + (f"，实时 PE {realtime_row[1]} ({realtime_row[0]})" if realtime_row else ""))

    except Exception as e:
        log(f"[{cfg['name']}] Error: {e}")
        raise
    finally:
        driver.quit()

    return all_history


def update_pe_data(index_key=None):
    """增量更新：只抓第一页，比对 CSV 末尾，有新数据则追加

    Args:
        index_key: 指定指数，None 则更新全部
    """
    targets = [index_key] if index_key else list(INDICES.keys())
    os.makedirs(DATA_DIR, exist_ok=True)

    driver = create_driver()
    try:
        for key in targets:
            cfg = INDICES[key]
            log(f"[{cfg['name']}] 增量更新...")

            driver.get(cfg["url"])
            time.sleep(8)

            if "Just a moment" in driver.title:
                log(f"[{cfg['name']}] Cloudflare 挑战中，等待...")
                time.sleep(15)

            if "Just a moment" in driver.title:
                log(f"[{cfg['name']}] 无法通过 Cloudflare，跳过")
                continue

            # 抓取第一页
            realtime_row, page_history = scrape_page(driver)

            # 保存实时值
            if realtime_row:
                save_latest_csv(key, realtime_row[0], realtime_row[1])
                log(f"[{cfg['name']}] 实时 PE: {realtime_row[1]} ({realtime_row[0]})")

            # 加载已有历史数据（倒序：最新在前）
            existing = load_history_csv(key)
            if not existing:
                log(f"[{cfg['name']}] 无历史数据，请先全量抓取")
                continue

            # CSV 第一行是最新日期
            last_date = existing[0][0]

            # 筛选新数据（日期比已有最新日期更晚）
            new_rows = [row for row in page_history if row[0] > last_date]

            if new_rows:
                # 追加到列表头部（保持倒序）
                existing = new_rows + existing
                save_history_csv(key, existing)
                log(f"[{cfg['name']}] 新增 {len(new_rows)} 行 (从 {new_rows[-1][0]} 到 {new_rows[0][0]})")
            else:
                log(f"[{cfg['name']}] 无新数据 (最新: {last_date})")

    except Exception as e:
        log(f"增量更新 Error: {e}")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target == "update":
        index = sys.argv[2] if len(sys.argv) > 2 else None
        update_pe_data(index)
    elif target in ("nasdaq100", "sp500", "all"):
        if target in ("nasdaq100", "all"):
            scrape_index("nasdaq100")
        if target in ("sp500", "all"):
            scrape_index("sp500")
    else:
        log(f"未知参数: {target}")
        log("用法: python -u scrape_gurufocus_pe.py [nasdaq100|sp500|all|update [nasdaq100|sp500]]")
