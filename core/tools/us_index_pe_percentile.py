"""
美股指数 PE 百分位计算

基于 GuruFocus 抓取的历史 PE 数据，计算当前 PE 在 5/10/20 年内的百分位。

数据文件:
    data/us_index_pe/nasdaq100_pe_history.csv   历史数据
    data/us_index_pe/sp500_pe_history.csv        历史数据
    data/us_index_pe/us_index_pe_latest.csv      实时 PE

用法:
    python -u us_index_pe_percentile.py nasdaq100
    python -u us_index_pe_percentile.py sp500
    python -u us_index_pe_percentile.py all
    python -u us_index_pe_percentile.py nasdaq100 2024-01-01
"""

import os
from datetime import timedelta

import pandas as pd


PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "us_index_pe")


def load_pe_data(index_key):
    """加载历史 PE 数据"""
    csv_path = os.path.join(DATA_DIR, f"{index_key}_pe_history.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"数据文件不存在: {csv_path}")

    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    df["pe"] = pd.to_numeric(df["pe"].astype(str).str.replace(",", ""), errors="coerce")
    df = df.dropna(subset=["pe"]).sort_values("date").reset_index(drop=True)
    return df


def load_latest_pe(index_key):
    """加载实时 PE 值"""
    csv_path = os.path.join(DATA_DIR, "us_index_pe_latest.csv")
    if not os.path.exists(csv_path):
        return None, None

    df = pd.read_csv(csv_path)
    row = df[df["index"] == index_key]
    if row.empty:
        return None, None

    return row.iloc[0]["date"], row.iloc[0]["pe"]


def calc_pe_percentile(df, reference_date=None, current_pe=None, periods=(5, 10, 20)):
    """
    计算 PE 在各时间段内的百分位

    Args:
        df: 包含 date 和 pe 列的 DataFrame
        reference_date: 参考日期，默认为数据中最新日期
        current_pe: 当前 PE 值，默认取 reference_date 当天的 PE
        periods: 计算百分位的时间段（年）

    Returns:
        dict
    """
    if reference_date is None:
        reference_date = df["date"].max()
    else:
        reference_date = pd.Timestamp(reference_date)

    if current_pe is None:
        current_pe = df.loc[df["date"] <= reference_date, "pe"].iloc[-1]

    result = {
        "reference_date": reference_date.strftime("%Y-%m-%d"),
        "current_pe": round(current_pe, 2),
    }

    for period in periods:
        start_date = reference_date - timedelta(days=period * 365)
        window = df[(df["date"] >= start_date) & (df["date"] <= reference_date)]

        if len(window) == 0:
            result[f"{period}y"] = None
            continue

        percentile = (window["pe"] < current_pe).sum() / len(window) * 100

        result[f"{period}y"] = {
            "percentile": round(percentile, 1),
            "data_points": len(window),
            "min": round(window["pe"].min(), 2),
            "max": round(window["pe"].max(), 2),
            "median": round(window["pe"].median(), 2),
            "mean": round(window["pe"].mean(), 2),
        }

    return result


def format_report(index_key, result):
    """格式化输出百分位报告"""
    names = {
        "nasdaq100": "纳斯达克100",
        "sp500": "标普500",
    }
    name = names.get(index_key, index_key)

    lines = [
        f"{'='*50}",
        f"  {name} PE 百分位报告",
        f"  参考日期: {result['reference_date']}",
        f"  当前 PE:  {result['current_pe']}",
        f"{'='*50}",
    ]

    for period in [5, 10, 20]:
        key = f"{period}y"
        info = result.get(key)
        if info is None:
            lines.append(f"\n  {period}年: 数据不足")
            continue

        lines.append(
            f"\n  {period}年百分位: {info['percentile']}%\n"
            f"    数据点数: {info['data_points']}\n"
            f"    最小值:   {info['min']}\n"
            f"    中位数:   {info['median']}\n"
            f"    平均值:   {info['mean']}\n"
            f"    最大值:   {info['max']}"
        )

    lines.append(f"\n{'='*50}")
    return "\n".join(lines)


def get_pe_percentile(index_key, reference_date=None, use_latest=True):
    """
    获取指数 PE 百分位

    Args:
        index_key: "nasdaq100" 或 "sp500"
        reference_date: 参考日期，None 则用最新历史日期
        use_latest: 是否使用实时 PE 值（仅在 reference_date 为 None 时生效）

    Returns:
        dict: 百分位结果
    """
    df = load_pe_data(index_key)

    # 确定当前 PE 和参考日期
    current_pe = None
    if use_latest and reference_date is None:
        _, latest_pe = load_latest_pe(index_key)
        if latest_pe is not None:
            current_pe = float(latest_pe)

    result = calc_pe_percentile(df, reference_date, current_pe)
    report = format_report(index_key, result)
    print(report)
    return result


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    ref_date = sys.argv[2] if len(sys.argv) > 2 else None

    if target in ("nasdaq100", "all"):
        get_pe_percentile("nasdaq100", ref_date)
    if target in ("sp500", "all"):
        get_pe_percentile("sp500", ref_date)
