"""生成直观交互式可视化图表 (HTML 网页报告)

功能:
  1. 回测多因子策略 (如 AAPL.NASDAQ 或 00700.SEHK)
  2. 提取每日 K 线、因子打分、买入/卖出标记点、累计资金净值曲线
  3. 用 Plotly 生成一个精美的交互式网页报告 (report.html)，直接双击即可用浏览器打开查看！
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_factor_demo import load_bars_from_db


def generate_interactive_chart(symbol: str = "AAPL.NASDAQ", days: int = 300, output_html: str = "report.html"):
    print(f"\n📊 正在从数据库读取 {symbol} 真实数据并生成可视化报告...")
    df = load_bars_from_db(symbol, days)
    if df.empty:
        print(f"❌ 未能加载到 {symbol} 的数据")
        return

    # 1. 计算两个核心因子
    # 因子 1: 5日量比 (成交量异动)
    df["vol_ratio"] = df["volume"].rolling(5).mean() / (df["volume"].rolling(20).mean() + 1e-9)
    # 因子 2: RSI 超跌
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / (loss + 1e-9)))
    df["rsi_factor"] = 50.0 - rsi

    # 2. 标准化合成总分 (Alpha Score)
    z_vol = (df["vol_ratio"] - df["vol_ratio"].mean()) / (df["vol_ratio"].std() + 1e-6)
    z_rsi = (df["rsi_factor"] - df["rsi_factor"].mean()) / (df["rsi_factor"].std() + 1e-6)
    df["alpha_score"] = (0.6 * z_vol.clip(-3, 3) + 0.4 * z_rsi.clip(-3, 3)).fillna(0)

    # 3. 模拟策略买卖点与资金曲线
    pos = 0
    cash = 100000.0
    shares = 0
    portfolio_values = []
    buy_dates, buy_prices = [], []
    sell_dates, sell_prices = [], []

    for i, row in df.iterrows():
        score = row["alpha_score"]
        price = row["close"]
        dt = row["date"]

        # 买入信号: 得分 > 0.5 且空仓
        if pos == 0 and score > 0.5:
            shares = int(cash / price)
            cash -= shares * price
            pos = 1
            buy_dates.append(dt)
            buy_prices.append(price)
        # 卖出信号: 得分 < -0.2 且持仓
        elif pos == 1 and score < -0.2:
            cash += shares * price
            shares = 0
            pos = 0
            sell_dates.append(dt)
            sell_prices.append(price)

        total_val = cash + shares * price
        portfolio_values.append(total_val)

    df["portfolio_value"] = portfolio_values
    df["benchmark_value"] = (df["close"] / df["close"].iloc[0]) * 100000.0

    # 4. 构建 Plotly 多子图交互界面
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=(
            f"📈 {symbol} 真实 K 线走势与策略买卖信号 (🟢买入 / 🔴卖出)",
            "🧠 每日多因子综合打分 (Alpha Score: >0.5看多, <-0.2看空)",
            "💰 策略资金收益曲线 vs 买入持有基准"
        ),
        row_heights=[0.5, 0.25, 0.25]
    )

    # 子图 1: 蜡烛 K 线图 + 买卖标记
    fig.add_trace(
        go.Candlestick(
            x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
            name="K线行情", increasing_line_color="#00da3c", decreasing_line_color="#ec0000"
        ),
        row=1, col=1
    )

    # 标记买点 🟢
    if buy_dates:
        fig.add_trace(
            go.Scatter(
                x=buy_dates, y=buy_prices, mode="markers+text",
                marker=dict(symbol="triangle-up", size=14, color="#00ff7f", line=dict(width=1, color="black")),
                text=["🟢买入"] * len(buy_dates), textposition="bottom center", name="买入信号"
            ),
            row=1, col=1
        )

    # 标记卖点 🔴
    if sell_dates:
        fig.add_trace(
            go.Scatter(
                x=sell_dates, y=sell_prices, mode="markers+text",
                marker=dict(symbol="triangle-down", size=14, color="#ff3030", line=dict(width=1, color="black")),
                text=["🔴卖出"] * len(sell_dates), textposition="top center", name="卖出信号"
            ),
            row=1, col=1
        )

    # 子图 2: 因子得分柱状图
    colors = ["#00e676" if s > 0.5 else ("#ff5252" if s < -0.2 else "#90a4ae") for s in df["alpha_score"]]
    fig.add_trace(
        go.Bar(x=df["date"], y=df["alpha_score"], marker_color=colors, name="因子综合得分"),
        row=2, col=1
    )
    # 添加阈值参考线
    fig.add_hline(y=0.5, line_dash="dash", line_color="#00e676", row=2, col=1)
    fig.add_hline(y=-0.2, line_dash="dash", line_color="#ff5252", row=2, col=1)

    # 子图 3: 累计净值曲线
    fig.add_trace(
        go.Scatter(x=df["date"], y=df["portfolio_value"], line=dict(color="#2979ff", width=2.5), name="多因子策略净值"),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df["date"], y=df["benchmark_value"], line=dict(color="#bdbdbd", dash="dot"), name="单纯持有股票"),
        row=3, col=1
    )

    # 布局美化
    fig.update_layout(
        template="plotly_dark",
        height=900,
        title=f"📊 量化多因子体系端到端可视化实战看板 — {symbol}",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=50, r=40, t=80, b=40)
    )

    out_path = ROOT / output_html
    fig.write_html(str(out_path))
    print(f"✅ 可视化图表生成成功！保存于: {out_path}")
    return str(out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="AAPL.NASDAQ")
    parser.add_argument("--days", type=int, default=300)
    parser.add_argument("--out", default="report.html")
    args = parser.parse_args()
    generate_interactive_chart(args.symbol, args.days, args.out)
