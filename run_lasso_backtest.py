"""LASSO 5大正交兵种多因子实战回测与全透明对比大屏

执行流程:
1. 从数据库读取真实股票行情 (默认腾讯 00700.SEHK 或 苹果 AAPL.NASDAQ)
2. 运行 LASSO L1 正则化回归与相关性聚类，现场演示如何将 285 个因子降维提炼出 5 大互补兵种
3. 驱动 VeighNa CTA 回测引擎，扣除印花税、佣金与滑点，跑出真实逐日资金曲线
4. 对比「多因子策略 vs 买入并持有基准 (Buy & Hold)」
5. 输出高颜值交互网页大屏: lasso_ensemble_report.html
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_factor_demo import load_bars_from_db
from gemini_quant.portfolio.lasso_selector import run_lasso_selection
from strategies.lasso_ensemble_strategy import LassoEnsembleStrategy

from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import BarData


def run_backtest_with_engine(symbol: str, df: pd.DataFrame, capital: float = 1_000_000):
    """驱动 VeighNa 回测引擎进行严格扣费回测"""
    engine = BacktestingEngine()
    
    parts = symbol.split(".")
    raw_symbol = parts[0]
    exchange = Exchange(parts[1]) if len(parts) > 1 else Exchange.SEHK

    # 费率与滑点设定
    if exchange == Exchange.SEHK:
        rate = 0.0015       # 港股印花税+佣金千1.5
        slippage = 0.05     # 港股滑点 0.05
        pricetick = 0.01
    elif exchange in [Exchange.NASDAQ, Exchange.NYSE]:
        rate = 0.0005       # 美股万5
        slippage = 0.01
        pricetick = 0.01
    else:
        rate = 0.0003       # A股万3
        slippage = 0.01
        pricetick = 0.01

    start_dt = df["date"].iloc[0]
    end_dt = df["date"].iloc[-1]
    start_py = start_dt.to_pydatetime() if hasattr(start_dt, "to_pydatetime") else pd.to_datetime(start_dt).to_pydatetime()
    end_py = end_dt.to_pydatetime() if hasattr(end_dt, "to_pydatetime") else pd.to_datetime(end_dt).to_pydatetime()

    engine.set_parameters(
        vt_symbol=f"{raw_symbol}.{exchange.value}",
        interval=Interval.DAILY,
        start=start_py,
        end=end_py,
        rate=rate,
        slippage=slippage,
        size=1,
        pricetick=pricetick,
        capital=capital
    )

    engine.add_strategy(LassoEnsembleStrategy, {
        "fixed_size": 2000 if exchange == Exchange.SEHK else 100,
        "threshold_buy": 0.58,
        "threshold_sell": 0.42,
        "trailing_stop_pct": 0.06
    })

    # 将 DataFrame 转换为 vnpy BarData 并载入引擎
    history_data = []
    for _, row in df.iterrows():
        dt = row["date"]
        pydt = dt.to_pydatetime() if hasattr(dt, "to_pydatetime") else pd.to_datetime(dt).to_pydatetime()
        bar = BarData(
            symbol=raw_symbol,
            exchange=exchange,
            datetime=pydt,
            interval=Interval.DAILY,
            volume=float(row["volume"]),
            open_price=float(row["open"]),
            high_price=float(row["high"]),
            low_price=float(row["low"]),
            close_price=float(row["close"]),
            gateway_name="DB"
        )
        history_data.append(bar)

    engine.history_data = history_data
    print(f"🚀 开始在 {symbol} 历史上执行 VeighNa 逐日事件驱动回测...")
    engine.run_backtesting()
    
    df_daily = engine.calculate_result()
    stats = engine.calculate_statistics(output=False)
    trades = engine.trades
    
    return df_daily, stats, trades, rate, slippage


def generate_interactive_report(
    symbol: str,
    df: pd.DataFrame,
    df_daily: pd.DataFrame,
    stats: dict,
    trades: dict,
    selected_factors: list,
    output_html: str = "lasso_ensemble_report.html"
):
    """渲染全透明专业级交互对比报表"""
    # 1. 计算基准 (Buy & Hold) 曲线
    first_close = df["close"].iloc[0]
    benchmark_equity = (df["close"] / first_close) * stats.get("capital", 1_000_000)

    # 策略净值序列
    if df_daily is not None and not df_daily.empty and "balance" in df_daily.columns:
        strat_dates = df_daily.index
        strat_net = df_daily["balance"]
        strat_dd = df_daily.get("drawdown", pd.Series([0.0] * len(df_daily), index=strat_dates))
    else:
        strat_dates = df["date"]
        strat_net = pd.Series([stats.get("capital", 1_000_000)] * len(df), index=df["date"])
        strat_dd = pd.Series([0.0] * len(df), index=df["date"])

    # 提取真实交易点位
    buy_dates, buy_prices = [], []
    sell_dates, sell_prices = [], []
    for trade in trades.values():
        if trade.direction.value == "多":
            buy_dates.append(trade.datetime)
            buy_prices.append(trade.price)
        else:
            sell_dates.append(trade.datetime)
            sell_prices.append(trade.price)

    # 2. 绘制双轴交互图表
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("📈 资金曲线全景对照 (LASSO 多因子策略 vs 买入并持有基准)", "🌊 动态回撤风险对比"),
        row_heights=[0.7, 0.3]
    )

    # 主曲线 1: 策略净值
    fig.add_trace(go.Scatter(
        x=strat_dates, y=strat_net,
        name="🤖 LASSO 5大正交兵种策略",
        line=dict(color="#00e676", width=2.5),
        hovertemplate="日期: %{x}<br>策略资产: %{y:,.0f} 元<extra></extra>"
    ), row=1, col=1)

    # 主曲线 2: 买入并持有基准
    fig.add_trace(go.Scatter(
        x=df["date"], y=benchmark_equity,
        name=f"⚪ {symbol} 买入并持有基准 (Buy & Hold)",
        line=dict(color="#90a4ae", width=1.8, dash="dot"),
        hovertemplate="日期: %{x}<br>基准资产: %{y:,.0f} 元<extra></extra>"
    ), row=1, col=1)

    # 买入标记
    if buy_dates:
        fig.add_trace(go.Scatter(
            x=buy_dates, y=[strat_net.loc[d] if d in strat_net.index else strat_net.iloc[-1] for d in buy_dates],
            mode="markers",
            name="🟢 买入开仓",
            marker=dict(symbol="triangle-up", size=11, color="#00e676", line=dict(width=1, color="#fff"))
        ), row=1, col=1)

    # 卖出标记
    if sell_dates:
        fig.add_trace(go.Scatter(
            x=sell_dates, y=[strat_net.loc[d] if d in strat_net.index else strat_net.iloc[-1] for d in sell_dates],
            mode="markers",
            name="🔴 平仓/止损",
            marker=dict(symbol="triangle-down", size=11, color="#ff5252", line=dict(width=1, color="#fff"))
        ), row=1, col=1)

    # 子图 2: 策略回撤曲线
    fig.add_trace(go.Scatter(
        x=strat_dates, y=strat_dd,
        name="策略回撤",
        fill="tozeroy",
        line=dict(color="#ff5252", width=1),
        hovertemplate="日期: %{x}<br>回撤金额: %{y:,.0f} 元<extra></extra>"
    ), row=2, col=1)

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    chart_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

    # 3. 构建 5 大正交因子的表格行
    factor_rows_html = ""
    for idx, f in enumerate(selected_factors, 1):
        factor_rows_html += f"""
        <tr>
            <td style="font-weight:bold; color:#58a6ff;">#{idx} {f['name']}</td>
            <td><span class="badge" style="background:#1f6feb33; color:#58a6ff; border:1px solid #1f6feb;">{f['category']}</span></td>
            <td style="color:#f1e05a; font-weight:bold;">{f['rank_ic']:+.4f}</td>
            <td style="color:#a5d6ff;">{f['lasso_coef']:+.4f}</td>
            <td style="color:#c9d1d9;">{f['desc']}</td>
        </tr>
        """

    # 4. 汇总核心 KPI
    total_ret = stats.get("total_return", 0.0)
    annual_ret = stats.get("annual_return", 0.0)
    sharpe = stats.get("sharpe_ratio", 0.0)
    max_dd = stats.get("max_drawdown_percent", 0.0)
    total_commission = stats.get("total_commission", 0.0)
    total_trades = stats.get("total_trade_count", 0)
    bench_ret = ((df["close"].iloc[-1] / first_close) - 1.0) * 100.0

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{symbol} 多因子 LASSO 正交实战回测透视报告</title>
    <style>
        body {{ background:#0d1117; color:#c9d1d9; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding:20px; }}
        h1 {{ color:#fff; text-align:center; margin-bottom:5px; }}
        .subtitle {{ text-align:center; color:#8b949e; margin-bottom:25px; }}
        .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:15px; margin-bottom:25px; }}
        .kpi-card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:15px; text-align:center; }}
        .kpi-val {{ font-size:26px; font-weight:bold; }}
        .kpi-label {{ color:#8b949e; font-size:13px; margin-top:4px; }}
        .chart-box {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:15px; margin-bottom:25px; }}
        table {{ width:100%; border-collapse:collapse; background:#161b22; border-radius:8px; overflow:hidden; }}
        th, td {{ padding:12px 16px; text-align:left; border-bottom:1px solid #30363d; font-size:14px; }}
        th {{ background:#21262d; color:#8b949e; }}
        .badge {{ padding:2px 8px; border-radius:10px; font-size:11px; }}
    </style>
</head>
<body>
    <h1>🏛️ {symbol} 多因子 LASSO 正交实战回测大屏</h1>
    <div class="subtitle">285 因子算法降维 ➔ 5 大正交兵种合成 ➔ 严扣印花税/佣金/滑点实盘压力测试</div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-val" style="color: {'#00e676' if total_ret>0 else '#ff5252'}">{total_ret:+.2f}%</div>
            <div class="kpi-label">策略总收益率</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: {'#00e676' if bench_ret>0 else '#ff5252'}">{bench_ret:+.2f}%</div>
            <div class="kpi-label">买入并持有基准收益</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #58a6ff;">{annual_ret:.2f}%</div>
            <div class="kpi-label">年化复合收益率</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #f1e05a;">{sharpe:.2f}</div>
            <div class="kpi-label">夏普比率 (Sharpe)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #ff5252;">{max_dd:.2f}%</div>
            <div class="kpi-label">最大回撤 (MaxDD)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #a5d6ff;">{total_trades} 笔</div>
            <div class="kpi-label">实操交易次数 (扣佣 {total_commission:.0f}元)</div>
        </div>
    </div>

    <div class="chart-box">
        {chart_html}
    </div>

    <div class="chart-box">
        <h3 style="color:#fff; margin-bottom:12px;">🎖️ 本次策略通过 LASSO 稀疏惩罚提炼出的 5 大正交先锋兵种</h3>
        <table>
            <thead>
                <tr>
                    <th>因子英文代号</th>
                    <th>所属作战梯队</th>
                    <th>Rank IC 预测力</th>
                    <th>LASSO 惩罚权重</th>
                    <th>12岁大白话业务逻辑</th>
                </tr>
            </thead>
            <tbody>
                {factor_rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    Path(output_html).write_text(html_content, encoding="utf-8")
    print(f"🎉 成功生成全透明交互大屏: {Path(output_html).resolve()}")


def main():
    parser = argparse.ArgumentParser(description="LASSO Multi-Factor Backtest Runner")
    parser.add_argument("--symbol", type=str, default="00700.SEHK", help="回测标的 (如 00700.SEHK 或 AAPL.NASDAQ)")
    parser.add_argument("--days", type=int, default=750, help="回测天数 (默认约3年)")
    parser.add_argument("--output", type=str, default="lasso_ensemble_report.html", help="输出HTML报表路径")
    args = parser.parse_args()

    print(f"==================================================")
    print(f"🎯 启动多因子自动化选拔与回测大考: 标的 = {args.symbol}")
    print(f"==================================================")

    # 1. 读取数据库数据
    df = load_bars_from_db(args.symbol, limit=args.days)
    if df.empty:
        print(f"❌ 无法从数据库获取 {args.symbol} 数据，请先运行数据同步！")
        return

    # 2. 现场执行 LASSO 正交降维
    selected_factors = run_lasso_selection(df, forward_days=5, top_n=5, max_corr=0.35)

    # 3. 执行严格扣费回测
    df_daily, stats, trades, rate, slippage = run_backtest_with_engine(args.symbol, df)

    # 4. 生成交互式可视化大屏
    generate_interactive_report(
        symbol=args.symbol,
        df=df,
        df_daily=df_daily,
        stats=stats,
        trades=trades,
        selected_factors=selected_factors,
        output_html=args.output
    )

if __name__ == "__main__":
    main()
