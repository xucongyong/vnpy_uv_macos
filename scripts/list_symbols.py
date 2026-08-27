"""列出数据库里所有的股票代码。

用法:
    python scripts/list_symbols.py                 # 全部代码 + 各市场统计
    python scripts/list_symbols.py --market A      # 只看 A股 (A / HK / US)
    python scripts/list_symbols.py --market US --limit 20
    python scripts/list_symbols.py --keyword 腾讯  # 按名字搜(先映射, 见下)

说明: 代码存在 quant_data 表的 symbol + exchange 两列。
     库是 vt_setting.json 指向的 quant 库。
"""

import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("VNPY_USE_MIRROR", "false")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vnpy.trader.database import get_database

MARKET_MAP = {
    "A": ("SSE", "SZSE", "BSE"),
    "HK": ("SEHK",),
    "US": ("NASDAQ", "NYSE", "AMEX"),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="列出数据库里的股票代码")
    parser.add_argument("--market", default="", help="A=A股, HK=港股, US=美股(留空=全部)")
    parser.add_argument("--limit", type=int, default=0, help="最多显示多少行(0=全部)")
    parser.add_argument("--keyword", default="", help="按代码包含搜索, 如 000 或 A")
    args = parser.parse_args()

    db = get_database()
    rows = []
    for ov in db.get_bar_overview():
        if ov.interval.value != "d":
            continue
        rows.append((ov.symbol, ov.exchange.value))

    if args.market:
        allow = MARKET_MAP.get(args.market.upper())
        if not allow:
            print(f"❌ 市场参数错误: {args.market}, 可选 A / HK / US")
            return
        rows = [r for r in rows if r[1] in allow]
    if args.keyword:
        rows = [r for r in rows if args.keyword.upper() in r[0].upper()]

    rows = sorted(rows, key=lambda r: (r[1], r[0]))

    # 各市场统计
    from collections import Counter
    stats = Counter(r[1] for r in rows)
    total = len(rows)
    print(f"📦 共 {total} 个标的")
    for ex, n in sorted(stats.items()):
        print(f"   {ex}: {n}")

    show = rows if not args.limit else rows[:args.limit]
    if show:
        print("\n代码清单 (symbol.exchange):")
        for symbol, ex in show:
            print(f"   {symbol}.{ex}")


if __name__ == "__main__":
    main()
