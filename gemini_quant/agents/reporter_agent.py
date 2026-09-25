"""大屏秘书特工 (ReporterAgent)

负责汇聚所有智能体的决策产物，渲染交互式 Plotly 多资产轮动净值大屏与交易台账。
"""

from typing import Dict, Any, List
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from gemini_quant.agents.base_agent import BaseAgent, COLOR_BLUE


class ReporterAgent(BaseAgent):
    """负责团队战报汇总与可视化大屏生成的特工"""

    def __init__(self, name: str = "Secretary"):
        super().__init__(
            name=name,
            role_title="大屏汇报秘书",
            emoji="📊",
            color_code=COLOR_BLUE
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        equity_df: pd.DataFrame = context["equity_df"]
        holding_df: pd.DataFrame = context["holding_df"]
        trade_records: List[Dict[str, Any]] = context["trade_records"]
        stats: Dict[str, Any] = context["stats"]
        symbols: List[str] = context.get("symbols", [])
        output_html: str = context.get("output_html", "multi_agent_portfolio_report.html")

        self.log(f"正在汇聚团队成果，渲染交互式多资产大屏: {output_html} ...")

        dates = equity_df["date"]
        portfolio_val = equity_df["equity"]
        benchmark_val = equity_df["benchmark"]

        # 计算动态回撤
        peak_series = equity_df["equity"].cummax()
        drawdown_val = (equity_df["equity"] - peak_series)

        # 3 层交互子图: 净值对比 + 资产权重轮动堆叠面积图 + 动态回撤
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            subplot_titles=(
                "📈 资金净值全景对照 (TradingAgents 5 兵种轮动组合 vs 跨市场等权基准)",
                "🌊 跨市场持仓权重动态轮动图 (美/港/A 资本实时调仓倾斜)",
                "🛡️ 组合动态回撤风险监控 (含 6% 跟踪止损防御)"
            ),
            row_heights=[0.50, 0.30, 0.20]
        )

        # 1. 组合净值 vs 基准
        fig.add_trace(go.Scatter(
            x=dates, y=portfolio_val,
            name="🤖 TradingAgents 跨市场轮动组合",
            line=dict(color="#00e676", width=2.8),
            hovertemplate="日期: %{x|%Y-%m-%d}<br>组合净值: %{y:,.0f} 元<extra></extra>"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=dates, y=benchmark_val,
            name="⚪ 5大标的等权买入并持有基准 (Buy & Hold)",
            line=dict(color="#90a4ae", width=1.8, dash="dot"),
            hovertemplate="日期: %{x|%Y-%m-%d}<br>基准净值: %{y:,.0f} 元<extra></extra>"
        ), row=1, col=1)

        # 2. 资产轮动持仓堆叠图
        asset_colors = ["#29b6f6", "#ab47bc", "#ffa726", "#26a69a", "#ec407a", "#7e57c2"]
        for idx, sym in enumerate(symbols):
            if sym in holding_df.columns:
                fig.add_trace(go.Scatter(
                    x=dates, y=holding_df[sym] * 100,
                    name=f"持仓: {sym}",
                    stackgroup="one",
                    line=dict(width=0.5, color=asset_colors[idx % len(asset_colors)]),
                    hovertemplate=f"{sym}: %{{y:.1f}}%<extra></extra>"
                ), row=2, col=1)

        # 3. 回撤图
        fig.add_trace(go.Scatter(
            x=dates, y=drawdown_val,
            name="组合回撤金额",
            fill="tozeroy",
            line=dict(color="#ff5252", width=1.2),
            hovertemplate="日期: %{x|%Y-%m-%d}<br>回撤金额: %{y:,.0f} 元<extra></extra>"
        ), row=3, col=1)

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0d1117",
            plot_bgcolor="#161b22",
            height=950,
            margin=dict(l=40, r=40, t=60, b=40),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        chart_html = fig.to_html(full_html=False, include_plotlyjs="cdn")

        # 生成交易表格 HTML
        trade_rows_html = ""
        for t in reversed(trade_records[-25:]):  # 展示最近 25 笔
            color = "#00e676" if "建仓" in t["action"] else "#ff5252"
            trade_rows_html += f"""
            <tr>
                <td>{t['date']}</td>
                <td style="font-weight:bold; color:#58a6ff;">{t['symbol']}</td>
                <td style="color:{color}; font-weight:bold;">{t['action']}</td>
                <td>{t['price']:.2f}</td>
                <td>{t['shares']:,}</td>
                <td style="color:#f85149;">-{t['fee']:.2f} 元</td>
                <td style="color:#8b949e;">{t['reason']}</td>
            </tr>
            """

        ret_color = "#00e676" if stats['total_return'] >= 0 else "#ff5252"
        bm_color = "#00e676" if stats['bm_total_return'] >= 0 else "#ff5252"

        full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>TradingAgents 跨市场多资产轮动决策大屏</title>
    <style>
        body {{ background:#0d1117; color:#c9d1d9; font-family:-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding:20px; }}
        h1 {{ color:#fff; text-align:center; margin-bottom:5px; }}
        .subtitle {{ text-align:center; color:#8b949e; margin-bottom:25px; }}
        .kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:15px; margin-bottom:25px; }}
        .kpi-card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:15px; text-align:center; }}
        .kpi-val {{ font-size:24px; font-weight:bold; }}
        .kpi-label {{ color:#8b949e; font-size:12px; margin-top:4px; }}
        .chart-box {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:15px; margin-bottom:25px; }}
        .agent-team {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-bottom:25px; }}
        .agent-card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:12px; font-size:13px; }}
        .agent-title {{ font-weight:bold; color:#58a6ff; margin-bottom:4px; display:flex; align-items:center; gap:6px; }}
        table {{ width:100%; border-collapse:collapse; background:#161b22; border-radius:8px; overflow:hidden; }}
        th, td {{ padding:10px 14px; text-align:left; border-bottom:1px solid #30363d; font-size:13px; }}
        th {{ background:#21262d; color:#8b949e; }}
    </style>
</head>
<body>
    <h1>🏛️ TradingAgents 跨市场多标的多因子轮动实战大屏</h1>
    <div class="subtitle">美股 (AAPL, AMAT, INTC) + 港股 (00700) + A股 (000001) · 5大智能体协同决策大考</div>

    <div class="agent-team">
        <div class="agent-card">
            <div class="agent-title">🕵️‍♂️ 数据清洗特工 · Scout</div>
            <div>统一美/港/A三地休市日历，对齐 750 根有效K线，消除未来函数。</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">🔬 因子挖掘体检官 · Miner</div>
            <div>调动 285 全量因子库，执行每日横截面相对强弱 CS-ZScore 打分。</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">⚖️ 组合轮动特工 · Quartermaster</div>
            <div>每周选拔 Top-2 状元标的资金平分，严格扣减美/港/A跨市场税费。</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">🛡️ 风险与资金管家 · Guardian</div>
            <div>全天候盯盘，单一持仓高点回撤超 6% 坚决触发移动止损保命。</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">📊 大屏汇报秘书 · Secretary</div>
            <div>实时汇总各智能体成果，渲染全景净值曲线与交易账本。</div>
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-val" style="color: {ret_color};">{stats['total_return']:+.2f}%</div>
            <div class="kpi-label">多因子轮动总收益</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: {bm_color};">{stats['bm_total_return']:+.2f}%</div>
            <div class="kpi-label">5标的等权买入持有基准</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #58a6ff;">{stats['annual_return']:+.2f}%</div>
            <div class="kpi-label">年化复合收益率</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #f1e05a;">{stats['sharpe']:.2f}</div>
            <div class="kpi-label">夏普比率 (Sharpe)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #ff5252;">{stats['max_drawdown']:.2f}%</div>
            <div class="kpi-label">最大资产回撤 (MaxDD)</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color: #a5d6ff;">{stats['total_trades']} 笔</div>
            <div class="kpi-label">调仓笔数 (总扣佣 {stats['total_fees']:,.0f}元)</div>
        </div>
    </div>

    <div class="chart-box">
        {chart_html}
    </div>

    <div class="chart-box">
        <h3 style="margin-top:0; color:#fff;">📜 团队最近 25 笔实战调仓与风控执行台账</h3>
        <table>
            <thead>
                <tr>
                    <th>交易日期</th>
                    <th>标的代码</th>
                    <th>调仓动作</th>
                    <th>成交价格</th>
                    <th>成交股数</th>
                    <th>印花税/手续费</th>
                    <th>智能体决策理由</th>
                </tr>
            </thead>
            <tbody>
                {trade_rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(full_html)

        self.log_success(f"大屏渲染完成！战报已安全持久化至 {output_html}")
        return context
