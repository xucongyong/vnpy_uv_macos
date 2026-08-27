"""一键回测 CLI: 从本地 PostgreSQL 数据库加载行情, 跑 CTA 策略回测。

用法示例:
    # 列出所有可用策略
    python run_backtest.py --list

    # 回测一个策略 (自动识别市场默认费率/滑点)
    python run_backtest.py --strategy rsi --symbol 00700.SEHK --start 2022-01-01

    # 美股 + 覆盖参数 + 保存 CSV 报告
    python run_backtest.py --strategy dual_ma --symbol AAPL.NASDAQ \
        --start 2020-01-01 --params fast_window=5,slow_window=20,fixed_size=500 --csv

    # 手动指定费率
    python run_backtest.py --strategy boll --symbol 000001.SZSE \
        --rate 0.0003 --slippage 0.01 --pricetick 0.01

数据来源: vt_setting.json 配置的 PostgreSQL 数据库。
行情同步: 见 quant_data/sync_full_production.py
"""

import argparse
import datetime
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("VNPY_USE_MIRROR", "false")

from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval
from vnpy.trader.database import get_database

from strategies.registry import get_strategy, list_strategies

REPORT_DIR = Path(__file__).resolve().parent / "research" / "reports"

# 各市场默认交易成本 (可被 --rate/--slippage/--pricetick 覆盖)
# key: 交易所代码
MARKET_DEFAULTS = {
    "SSE":   dict(rate=0.0003, slippage=0.01, pricetick=0.01, size=1),
    "SZSE":  dict(rate=0.0003, slippage=0.01, pricetick=0.01, size=1),
    "BSE":   dict(rate=0.0003, slippage=0.01, pricetick=0.01, size=1),
    "SEHK":  dict(rate=0.0015, slippage=0.05, pricetick=0.01, size=1),
    "NASDAQ": dict(rate=0.0005, slippage=0.01, pricetick=0.01, size=1),
    "NYSE":  dict(rate=0.0005, slippage=0.01, pricetick=0.01, size=1),
    "LOCAL": dict(rate=0.001, slippage=10.0, pricetick=0.1, size=1),
}

INTERVAL_MAP = {
    "1m": Interval.MINUTE,
    "1h": Interval.HOUR,
    "d": Interval.DAILY,
    "1d": Interval.DAILY,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="一键 CTA 策略回测")
    parser.add_argument("--list", action="store_true", help="列出所有可用策略")
    parser.add_argument("--strategy", help="策略名 (类名或归一化名, 如 RsiStrategy / rsi)")
    parser.add_argument("--symbol", help="标的 vt_symbol, 如 00700.SEHK / AAPL.NASDAQ / 000001.SZSE")
    parser.add_argument("--interval", default="d", choices=list(INTERVAL_MAP.keys()),
                        help="K线周期, 默认 d")
    parser.add_argument("--start", default=None, help="开始日期 YYYY-MM-DD, 默认 3 年前")
    parser.add_argument("--end", default=None, help="结束日期 YYYY-MM-DD, 默认今天")
    parser.add_argument("--params", default="", help="策略参数, 逗号分隔 k=v, 如 fast_window=5,slow_window=20")
    parser.add_argument("--capital", type=int, default=1_000_000, help="初始资金, 默认 100 万")
    parser.add_argument("--rate", type=float, default=None, help="手续费率(覆盖市场默认)")
    parser.add_argument("--slippage", type=float, default=None, help="滑点(覆盖市场默认)")
    parser.add_argument("--pricetick", type=float, default=None, help="最小价格跳动(覆盖市场默认)")
    parser.add_argument("--size", type=float, default=None, help="合约乘数(覆盖市场默认)")
    parser.add_argument("--csv", action="store_true", help="保存结果 CSV 到 research/reports/")
    parser.add_argument("--quiet", action="store_true", help="只打印统计摘要, 不打印加载日志")
    return parser.parse_args()


def parse_params(params_str: str) -> dict:
    setting: dict = {}
    for item in params_str.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"参数格式错误: '{item}', 应为 k=v")
        k, v = item.split("=", 1)
        k = k.strip()
        v = v.strip()
        try:
            if "." in v:
                setting[k] = float(v)
            else:
                setting[k] = int(v)
        except ValueError:
            setting[k] = v
    return setting


def fast_load_data(engine: BacktestingEngine) -> None:
    """一次性全量加载行情(替代引擎的 30 天分块查询, 快 ~20 倍)。"""
    db = get_database()
    bars = db.load_bar_data(
        engine.symbol, engine.exchange, engine.interval, engine.start, engine.end
    )
    engine.history_data = list(bars)
    if not engine.history_data:
        print(f"⚠️  数据库中没有 {engine.vt_symbol} 的行情, 请先运行 quant_data/sync_*.py 同步数据")
        return
    print(f"行情加载完成: {len(engine.history_data)} 根K线")


def run_backtest(args: argparse.Namespace) -> dict:
    if "." not in args.symbol:
        raise ValueError(
            f"symbol 格式应为 SYMBOL.EXCHANGE, 如 00700.SEHK / AAPL.NASDAQ, 实际: {args.symbol}"
        )

    symbol, exchange = args.symbol.split(".", 1)
    defaults = MARKET_DEFAULTS.get(exchange.upper(), dict(rate=0.0005, slippage=0.01, pricetick=0.01, size=1))

    start = datetime.datetime.strptime(args.start, "%Y-%m-%d") if args.start \
        else datetime.datetime.now() - datetime.timedelta(days=365 * 3)
    end = datetime.datetime.strptime(args.end, "%Y-%m-%d") if args.end else datetime.datetime.now()

    setting = parse_params(args.params)
    strategy_cls = get_strategy(args.strategy)

    print("=" * 60)
    print(f"策略: {strategy_cls.__name__}   标的: {args.symbol}")
    print(f"周期: {args.interval}   区间: {start.date()} ~ {end.date()}")
    if setting:
        print(f"参数: {setting}")
    print("=" * 60)

    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=args.symbol,
        interval=INTERVAL_MAP[args.interval],
        start=start,
        end=end,
        rate=args.rate if args.rate is not None else defaults["rate"],
        slippage=args.slippage if args.slippage is not None else defaults["slippage"],
        size=args.size if args.size is not None else defaults["size"],
        pricetick=args.pricetick if args.pricetick is not None else defaults["pricetick"],
        capital=args.capital,
    )

    engine.add_strategy(strategy_cls, setting)
    fast_load_data(engine)

    if len(engine.history_data) == 0:
        return {}

    # 过滤引擎的进度噪音, 只保留有用的统计行
    def _clean_output(msg: str) -> None:
        skip_markers = (
            "loading progress", "backtesting progress", "historical data",
            "strategy initialization", "start replaying", "historical backtest",
            "start calculating", "calculation is complete", "daily mark-to-market",
            "回测", "加载进度", "回放进度", "回放结束", "初始化完成",
            "逐日盯市", "计算完成", "历史数据", "策略初始化", "开始回放",
        )
        lowered = msg.lower()
        if any(m in lowered for m in skip_markers):
            return
        print(msg)

    engine.output = _clean_output

    engine.run_backtesting()
    engine.calculate_result()
    stats = engine.calculate_statistics(output=False)

    if not args.quiet:
        engine.calculate_statistics(output=True)

    print("\n" + "=" * 60)
    print("📊 绩效摘要")
    print(f"  总收益率:      {stats['total_return']:>10.2f}%")
    print(f"  年化收益:      {stats['annual_return']:>10.2f}%")
    print(f"  夏普比率:      {stats['sharpe_ratio']:>10.2f}")
    print(f"  最大回撤:      {stats['max_ddpercent']:>10.2f}%")
    print(f"  收益回撤比:    {stats['return_drawdown_ratio']:>10.2f}")
    print(f"  成交笔数:      {int(stats['total_trade_count']):>10}")
    print(f"  结束资金:      {stats['end_balance']:>10,.0f}")
    print("=" * 60)

    if args.csv:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        csv_path = REPORT_DIR / f"{strategy_cls.__name__}_{args.symbol}_{stamp}.csv"
        df = engine.daily_df
        df.to_csv(csv_path, index=True)
        print(f"💾 逐日绩效已保存: {csv_path}")

    return stats


def main() -> None:
    args = parse_args()

    if args.list:
        print("可用策略:")
        for norm, clsname in list_strategies():
            print(f"  {clsname:<32} (别名: {norm})")
        return

    if not args.strategy or not args.symbol:
        print("❌ 请提供 --strategy 和 --symbol (用 --list 查看可用策略)")
        sys.exit(1)

    run_backtest(args)


if __name__ == "__main__":
    main()
