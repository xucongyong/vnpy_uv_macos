"""批量回测: 多标的 × 多策略 × 多参数, 一键对比。

用法:
    # 默认: 一组美股/港股/ A 股标的, 多策略对比
    python batch_backtest.py

    # 自定义股票池和策略 (逗号分隔; 策略可带参数 k=v;k=v)
    python batch_backtest.py --symbols AAPL.NASDAQ,00700.SEHK,000001.SZSE \
        --strategies dual_ma,rsisize=300,boll

    # 指定时间范围
    python batch_backtest.py --start 2022-01-01 --end 2024-12-31

结果保存到 batch_backtest_results.csv
"""

import argparse
import datetime
import os

os.environ.setdefault("VNPY_USE_MIRROR", "false")

import pandas as pd

from vnpy_ctastrategy.backtesting import BacktestingEngine

from strategies.registry import get_strategy, list_strategies
from run_backtest import INTERVAL_MAP, MARKET_DEFAULTS, fast_load_data, parse_params

DEFAULT_SYMBOLS = ["AAPL.NASDAQ", "00700.SEHK", "000001.SZSE", "NVDA.NASDAQ", "TSLA.NASDAQ"]
DEFAULT_STRATEGIES = ["dual_ma", "boll", "rsi"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="批量回测对比")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                        help="标的列表, 逗号分隔")
    parser.add_argument("--strategies", default=",".join(DEFAULT_STRATEGIES),
                        help="策略列表, 逗号分隔; 可带参数如 ma-fast=5,slow=20")
    parser.add_argument("--interval", default="d", choices=list(INTERVAL_MAP.keys()))
    parser.add_argument("--start", default=None, help="YYYY-MM-DD, 默认 3 年前")
    parser.add_argument("--end", default=None, help="YYYY-MM-DD, 默认今天")
    parser.add_argument("--capital", type=int, default=1_000_000)
    parser.add_argument("--list", action="store_true", help="列出可用策略")
    return parser.parse_args()


def parse_strategy_spec(spec: str) -> tuple[str, dict]:
    """'dual_ma-fast=5,slow=20' -> ('dual_ma', {'fast':5,'slow':20})"""
    if "-" in spec:
        name, params_str = spec.split("-", 1)
        return name, parse_params(params_str)
    return spec, {}


def run_one(strategy_name: str, setting: dict, symbol: str,
            interval: str, start: datetime.datetime, end: datetime.datetime,
            capital: int) -> dict:
    try:
        strategy_cls = get_strategy(strategy_name)
    except KeyError as e:
        print(f"  ⚠️  {e}")
        return {}

    exchange = symbol.split(".", 1)[1].upper()
    d = MARKET_DEFAULTS.get(exchange, dict(rate=0.0005, slippage=0.01, pricetick=0.01, size=1))

    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=symbol,
        interval=INTERVAL_MAP[interval],
        start=start,
        end=end,
        rate=d["rate"],
        slippage=d["slippage"],
        size=d["size"],
        pricetick=d["pricetick"],
        capital=capital,
    )
    engine.add_strategy(strategy_cls, setting)
    fast_load_data(engine)

    if not engine.history_data:
        return {}

    engine.output = lambda msg: None   # 静音
    engine.run_backtesting()
    engine.calculate_result()
    stats = engine.calculate_statistics(output=False)

    return {
        "Symbol": symbol,
        "Strategy": strategy_cls.__name__,
        "Params": setting,
        "Total Return %": stats.get("total_return", 0),
        "Annual %": stats.get("annual_return", 0),
        "Sharpe": stats.get("sharpe_ratio", 0),
        "Max DD %": stats.get("max_ddpercent", 0),
        "Return/DD": stats.get("return_drawdown_ratio", 0),
        "Trades": stats.get("total_trade_count", 0),
    }


def main() -> None:
    args = parse_args()

    if args.list:
        for norm, clsname in list_strategies():
            print(f"  {clsname:<32} (别名: {norm})")
        return

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    strategy_specs = [s.strip() for s in args.strategies.split(",") if s.strip()]

    start = datetime.datetime.strptime(args.start, "%Y-%m-%d") if args.start \
        else datetime.datetime.now() - datetime.timedelta(days=365 * 3)
    end = datetime.datetime.strptime(args.end, "%Y-%m-%d") if args.end \
        else datetime.datetime.now()

    print(f"批量回测: {len(symbols)} 标的 × {len(strategy_specs)} 策略")
    print(f"区间: {start.date()} ~ {end.date()}")
    print("=" * 80)

    results = []
    for symbol in symbols:
        for spec in strategy_specs:
            name, setting = parse_strategy_spec(spec)
            label = f"{name}({setting})" if setting else name
            print(f"▶  {symbol} / {label}")
            r = run_one(name, setting, symbol, args.interval, start, end, args.capital)
            if r:
                results.append(r)

    if not results:
        print("⚠️  没有产生任何回测结果")
        return

    df = pd.DataFrame(results)
    df_sorted = df.sort_values("Total Return %", ascending=False)

    print("\n" + "=" * 100)
    print("🏆 排行榜 (按总收益率排序)")
    print("=" * 100)
    print(df_sorted.to_string(index=False))

    csv_file = "batch_backtest_results.csv"
    df_sorted.to_csv(csv_file, index=False)
    print(f"\n✅ 完整结果已保存: {csv_file}")


if __name__ == "__main__":
    main()
