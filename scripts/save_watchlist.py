"""保存自选股行情到数据库 (akshare → PostgreSQL)

用法:
    python scripts/save_watchlist.py --symbols 00700.SEHK --days 2500
    python scripts/save_watchlist.py --symbols 00700.SEHK --force-full   # 强制全量重拉
    python scripts/save_watchlist.py --symbols 000001,600519,00700,AAPL
    python scripts/save_watchlist.py --symbols-file watchlist.txt

规则:
    - 带交易所后缀: 00700.SEHK / AAPL.NASDAQ / 000001.SZSE (推荐)
    - 不带后缀自动识别: 6位数字=A股, 5位数字=港股, 字母=美股(默认 NASDAQ)
    - 默认增量: 只拉"库里最新日期 - buffer天" 到今天; 库里没有就全量拉 --days 天
    - --force-full: 无视库里已有数据, 强制拉满 --days 天 (演示/修复用)

数据存进 vt_setting.json 配置的 PostgreSQL (vnpy 标准 dbbardata 表, upsert 自动去重)。
"""

import argparse
import datetime
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("VNPY_USE_MIRROR", "false")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import akshare as ak
import pandas as pd

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import get_database
from vnpy.trader.object import BarData

# 美股东财代码前缀 (stock_us_hist 需要 "105.AAPL" 这种格式)
US_EM_PREFIX = {"NASDAQ": "105", "NYSE": "106", "AMEX": "107"}


def pick(row, *keys):
    """从一行 DataFrame 里按多个候选列名取值 (兼容中文/英文列名)。"""
    for k in keys:
        if k in row and row[k] is not None:
            return row[k]
    return None


def detect_exchange(symbol: str) -> str:
    """不带后缀时自动判断市场。"""
    if symbol.isdigit():
        if len(symbol) == 6:
            return "SZSE" if symbol[0] in "023" else "SSE"
        if len(symbol) == 5:
            return "SEHK"
    return "NASDAQ"


def fetch_df(symbol: str, exchange: str, start: datetime.datetime,
             end: datetime.datetime) -> pd.DataFrame:
    """按市场调用对应的 akshare 接口, 返回日线 DataFrame。

    优先用东财接口(支持日期范围, 增量快); 失败自动降级到新浪接口(全量+过滤)。
    """
    s = start.strftime("%Y%m%d")
    e = end.strftime("%Y%m%d")

    if exchange in ("SSE", "SZSE", "BSE"):
        return ak.stock_zh_a_hist(symbol=symbol, period="daily",
                                  start_date=s, end_date=e, adjust="qfq")

    if exchange == "SEHK":
        try:
            return ak.stock_hk_hist(symbol=symbol, period="daily",
                                    start_date=s, end_date=e, adjust="qfq")
        except Exception:
            df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
            df["date"] = pd.to_datetime(df["date"])
            return df[(df["date"] >= start) & (df["date"] <= end)]

    # 美股: 东财需要交易所前缀; 失败降级新浪
    code = f"{US_EM_PREFIX.get(exchange, '105')}.{symbol}"
    try:
        return ak.stock_us_hist(symbol=code, period="daily",
                                start_date=s, end_date=e, adjust="qfq")
    except Exception:
        df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
        df["date"] = pd.to_datetime(df["date"])
        return df[(df["date"] >= start) & (df["date"] <= end)]


def df_to_bars(df: pd.DataFrame, symbol: str, exchange: str) -> list[BarData]:
    """把 akshare DataFrame 转成 vnpy BarData。"""
    bars: list[BarData] = []
    for _, row in df.iterrows():
        dt = pd.to_datetime(pick(row, "日期", "date", "Date"))
        if dt.tzinfo is not None:
            dt = dt.tz_convert(None)
        bar = BarData(
            symbol=symbol,
            exchange=Exchange(exchange),
            datetime=dt.to_pydatetime(),
            interval=Interval.DAILY,
            open_price=float(pick(row, "开盘", "open") or 0),
            high_price=float(pick(row, "最高", "high") or 0),
            low_price=float(pick(row, "最低", "low") or 0),
            close_price=float(pick(row, "收盘", "close") or 0),
            volume=float(pick(row, "成交量", "volume") or 0),
            turnover=float(pick(row, "成交额", "amount") or 0),
            gateway_name="AKSHARE",
        )
        bars.append(bar)
    return bars


def get_latest_bar_date(db, symbol: str, exchange: Exchange):
    """查库里该标的最新K线日期, 没有返回 None。"""
    for ov in db.get_bar_overview():
        if (ov.symbol == symbol and ov.exchange == exchange
                and ov.interval == Interval.DAILY):
            return ov.end
    return None


def update_symbol(symbol: str, exchange: str, days: int, buffer: int,
                  force_full: bool) -> int:
    """保存一只股票, 返回本次存进去的K线数。"""
    db = get_database()
    today = datetime.datetime.now().replace(hour=0, minute=0, second=0)

    # 决定抓取起点: 增量 or 全量
    if force_full:
        start = today - datetime.timedelta(days=days)
    else:
        last = get_latest_bar_date(db, symbol, Exchange(exchange))
        if last is not None:
            start = last - datetime.timedelta(days=buffer)
        else:
            start = today - datetime.timedelta(days=days)

    # 抓数据
    df = fetch_df(symbol, exchange, start, today)
    if df is None or df.empty:
        print(f"  ⚠️ {symbol}.{exchange}: akshare 返回空数据")
        return 0

    # 转 BarData 并存入 (upsert, 重复自动覆盖)
    bars = df_to_bars(df, symbol, exchange)
    db.save_bar_data(bars)

    n = len(bars)
    first, last = bars[0].datetime.date(), bars[-1].datetime.date()
    print(f"  ✓ {symbol}.{exchange} 保存 {n} 根K线  {first} ~ {last}  "
          f"最新收盘 {bars[-1].close_price:g}")
    return n


def main() -> None:
    parser = argparse.ArgumentParser(description="保存自选股行情到数据库")
    parser.add_argument("--symbols", default="", help="标的列表, 逗号分隔, 如 00700.SEHK,AAPL.NASDAQ")
    parser.add_argument("--symbols-file", default="", help="名单文件, 每行一个标的")
    parser.add_argument("--days", type=int, default=2500, help="全量拉多少天, 默认 2500(约10年)")
    parser.add_argument("--buffer", type=int, default=5, help="增量缓冲天数, 默认 5")
    parser.add_argument("--force-full", action="store_true", help="强制全量重拉, 忽略库里已有数据")
    args = parser.parse_args()

    if args.symbols_file:
        symbols = [line.strip() for line in Path(args.symbols_file).read_text().splitlines()
                   if line.strip() and not line.startswith("#")]
    else:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    if not symbols:
        print("❌ 请提供 --symbols 或 --symbols-file")
        sys.exit(1)

    total = 0
    t0 = time.time()
    print(f"🚀 开始同步 {len(symbols)} 只标的 (days={args.days}, force_full={args.force_full})")
    for raw in symbols:
        if "." in raw:
            symbol, exchange = raw.rsplit(".", 1)
        else:
            symbol, exchange = raw, detect_exchange(raw)
        exchange = exchange.upper()
        try:
            total += update_symbol(symbol, exchange, args.days, args.buffer, args.force_full)
        except Exception as e:
            print(f"  ❌ {symbol}.{exchange} 失败: {e}")

    print(f"🎉 完成, 共保存 {total} 根K线, 用时 {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
