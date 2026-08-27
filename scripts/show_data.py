"""从数据库读取行情查看 (验证保存 + 了解数据)

用法:
    python scripts/show_data.py --symbol 00700.SEHK --days 10
    python scripts/show_data.py --symbol 000001.SZSE --tail 5
    python scripts/show_data.py --symbol AAPL.NASDAQ --csv /tmp/aapl.csv
"""

import argparse
import datetime
import os
import sys
from pathlib import Path

os.environ.setdefault("VNPY_USE_MIRROR", "false")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.database import get_database


def main() -> None:
    parser = argparse.ArgumentParser(description="从数据库读取行情")
    parser.add_argument("--symbol", required=True, help="SYMBOL.EXCHANGE, 如 00700.SEHK")
    parser.add_argument("--days", type=int, default=10, help="最近 N 个自然日, 默认 10")
    parser.add_argument("--tail", type=int, default=10, help="打印最近多少根, 默认 10")
    parser.add_argument("--csv", default="", help="导出 CSV 路径")
    args = parser.parse_args()

    symbol, exchange = args.symbol.rsplit(".", 1)
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=args.days)

    db = get_database()
    bars = db.load_bar_data(symbol, Exchange(exchange), Interval.DAILY, start, end)

    if not bars:
        print(f"⚠️  库里 {args.symbol} 最近 {args.days} 天没有数据")
        print(f"   可能是还没同步, 先跑: python scripts/save_watchlist.py --symbols {args.symbol}")
        return

    rows = bars[-args.tail:]
    print(f"📦 {args.symbol}  共 {len(bars)} 根K线 ({bars[0].datetime.date()} ~ {bars[-1].datetime.date()})")
    print(f"   最近 {len(rows)} 根:")
    print(f"   {'日期':<12}{'开盘':>9}{'最高':>9}{'最低':>9}{'收盘':>9}{'成交量':>14}")
    for b in rows:
        print(f"   {str(b.datetime.date()):<12}{b.open_price:>9.2f}{b.high_price:>9.2f}"
              f"{b.low_price:>9.2f}{b.close_price:>9.2f}{b.volume:>14,.0f}")

    if args.csv:
        df = __import__("pandas").DataFrame([
            dict(date=b.datetime.date(), open=b.open_price, high=b.high_price,
                 low=b.low_price, close=b.close_price, volume=b.volume)
            for b in bars
        ])
        df.to_csv(args.csv, index=False)
        print(f"💾 已导出: {args.csv}")


if __name__ == "__main__":
    main()
