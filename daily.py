"""每日一条龙: ①增量同步行情 ②批量回测 ③存报告

用法:
    python daily.py                                             # 默认名单 + 默认策略
    python daily.py --symbols 00700.SEHK,AAPL.NASDAQ,000001.SZSE --strategies dual_ma,boll,rsi
    python daily.py --symbols-file watchlist.txt --strategies dual_ma,boll,rsi
    python daily.py --start 2024-01-01 --end 2026-08-27

流程:
    ① save_watchlist 增量同步 (每只只补缺的几天, 秒级)
    ② 批量回测 名单 × 策略
    ③ 排行榜存 research/reports/daily_*.csv
"""

import argparse
import datetime
import os
import time
from pathlib import Path

os.environ.setdefault("VNPY_USE_MIRROR", "false")

import pandas as pd

from batch_backtest import parse_strategy_spec, run_one
from scripts.save_watchlist import detect_exchange, update_symbol

ROOT = Path(__file__).resolve().parent

DEFAULT_SYMBOLS = ["00700.SEHK", "AAPL.NASDAQ", "000001.SZSE"]
DEFAULT_STRATEGIES = ["dual_ma", "boll", "rsi"]
REPORT_DIR = ROOT / "research" / "reports"
WATCHLIST_FILE = ROOT / "watchlist.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="每日一条龙: 同步+回测+报告")
    parser.add_argument("--symbols", default="", help="标的列表, 逗号分隔 (默认读 watchlist.txt 或内置3只)")
    parser.add_argument("--symbols-file", default="", help="名单文件, 每行一个")
    parser.add_argument("--strategies", default=",".join(DEFAULT_STRATEGIES),
                        help="策略列表, 逗号分隔; 可带参数如 ma-fast=5,slow=20")
    parser.add_argument("--days", type=int, default=2500, help="首次全量拉多少天, 默认2500")
    parser.add_argument("--start", default=None, help="回测起始 YYYY-MM-DD, 默认3年前")
    parser.add_argument("--end", default=None, help="回测结束 YYYY-MM-DD, 默认今天")
    parser.add_argument("--capital", type=int, default=1_000_000)
    return parser.parse_args()


def resolve_symbols(args) -> list[str]:
    """确定名单: --symbols > --symbols-file > watchlist.txt > 内置3只。"""
    if args.symbols:
        return [s.strip() for s in args.symbols.split(",") if s.strip()]
    if args.symbols_file:
        p = Path(args.symbols_file)
    elif WATCHLIST_FILE.exists():
        p = WATCHLIST_FILE
    else:
        return DEFAULT_SYMBOLS

    symbols = [line.strip() for line in p.read_text().splitlines()
               if line.strip() and not line.startswith("#")]
    return symbols or DEFAULT_SYMBOLS


def step_sync(symbols: list[str], days: int) -> None:
    """① 增量同步行情。"""
    print("\n" + "=" * 60)
    print(f"① 同步行情 ({len(symbols)} 只, 增量)")
    print("=" * 60)
    for raw in symbols:
        if "." in raw:
            symbol, exchange = raw.rsplit(".", 1)
        else:
            symbol, exchange = raw, detect_exchange(raw)
        try:
            update_symbol(symbol, exchange.upper(), days, buffer=5, force_full=False)
        except Exception as e:
            print(f"  ❌ {raw} 同步失败: {e}")


def step_backtest(symbols: list[str], strategy_specs: list[str],
                  start: datetime.datetime, end: datetime.datetime,
                  capital: int) -> list[dict]:
    """② 批量回测。"""
    print("\n" + "=" * 60)
    print(f"② 批量回测 ({len(symbols)} 标的 × {len(strategy_specs)} 策略)")
    print("=" * 60)
    results = []
    for symbol in symbols:
        for spec in strategy_specs:
            name, setting = parse_strategy_spec(spec)
            label = f"{name}({setting})" if setting else name
            r = run_one(name, setting, symbol, "d", start, end, capital)
            if r:
                results.append(r)
            else:
                print(f"  ⚠️  {symbol} / {label} 无结果")
    return results


def step_report(results: list[dict]) -> None:
    """③ 排行榜 + 存报告。"""
    print("\n" + "=" * 70)
    print("③ 排行榜 (按总收益率)")
    print("=" * 70)
    if not results:
        print("  ⚠️ 没有回测结果")
        return

    df = pd.DataFrame(results).sort_values("Total Return %", ascending=False)
    print(df.to_string(index=False))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out = REPORT_DIR / f"daily_{stamp}.csv"
    df.to_csv(out, index=False)
    print(f"\n✅ 报告已保存: {out}")


def main() -> None:
    args = parse_args()
    symbols = resolve_symbols(args)
    strategy_specs = [s.strip() for s in args.strategies.split(",") if s.strip()]

    start = datetime.datetime.strptime(args.start, "%Y-%m-%d") if args.start \
        else datetime.datetime.now() - datetime.timedelta(days=365 * 3)
    end = datetime.datetime.strptime(args.end, "%Y-%m-%d") if args.end \
        else datetime.datetime.now()

    t0 = time.time()
    print(f"📅 {datetime.datetime.now():%Y-%m-%d %H:%M}  名单 {len(symbols)} 只  "
          f"策略 {len(strategy_specs)} 个  区间 {start.date()}~{end.date()}")

    step_sync(symbols, args.days)
    results = step_backtest(symbols, strategy_specs, start, end, args.capital)
    step_report(results)

    print(f"\n🎉 全部完成, 总用时 {(time.time()-t0)/60:.1f} 分钟")


if __name__ == "__main__":
    main()
