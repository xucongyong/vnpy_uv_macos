"""组合轮动特工 (PortfolioAgent)

负责资产池动态资金分配、每周横截面选股轮动、跨市场不同费率精准扣减及组合净值核算。
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
from gemini_quant.agents.base_agent import BaseAgent, COLOR_GREEN


def get_market_fee_rate(symbol: str) -> float:
    """根据标的交易所获取精准费率"""
    if symbol.endswith(".SEHK"):
        return 0.0015  # 港股千1.5印花税与佣金
    elif symbol.endswith(".SZSE") or symbol.endswith(".SSE"):
        return 0.0003  # A股万3
    else:
        return 0.0005  # 美股万5


class PortfolioAgent(BaseAgent):
    """负责跨市场多资产横截面调仓与资金轮动的特工"""

    def __init__(self, name: str = "Quartermaster"):
        super().__init__(
            name=name,
            role_title="组合轮动特工",
            emoji="⚖️",
            color_code=COLOR_GREEN
        )

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        bars_dict: Dict[str, pd.DataFrame] = context["bars_dict"]
        aligned_dates: List[pd.Timestamp] = context["aligned_dates"]
        alpha_scores_df: pd.DataFrame = context["alpha_scores_df"]
        top_k: int = context.get("top_k", 2)
        rebalance_days: int = context.get("rebalance_days", 5)
        initial_capital: float = context.get("initial_capital", 1_000_000.0)
        trailing_stop_pct: float = context.get("risk_rules", {}).get("trailing_stop_pct", 0.06)

        symbols = list(bars_dict.keys())
        self.log(f"开始启动跨市场多资产组合回测 (初始本金: {initial_capital:,.0f} 元, 每 {rebalance_days} 天轮动 Top-{top_k} 强股)...")

        # 整理价格收盘矩阵
        close_matrix = pd.DataFrame(
            {sym: bars_dict[sym]["close"].values for sym in symbols},
            index=aligned_dates
        )

        cash = initial_capital
        holdings: Dict[str, float] = {sym: 0.0 for sym in symbols}
        peak_prices: Dict[str, float] = {sym: 0.0 for sym in symbols}

        daily_equity = []
        trade_records = []
        holding_history = []
        total_fees = 0.0

        num_days = len(aligned_dates)

        for i in range(num_days):
            current_date = aligned_dates[i]
            today_prices = close_matrix.iloc[i]

            # 1. 每日盘中硬风控：盯防个股 6% 移动追踪止损
            for sym in symbols:
                if holdings[sym] > 0:
                    px = today_prices[sym]
                    if px > peak_prices[sym]:
                        peak_prices[sym] = px
                    
                    # 检查是否回撤超过止损线
                    dd = (peak_prices[sym] - px) / peak_prices[sym]
                    if dd >= trailing_stop_pct:
                        # 强制平仓止损
                        shares = holdings[sym]
                        revenue = shares * px
                        fee = revenue * get_market_fee_rate(sym)
                        cash += (revenue - fee)
                        total_fees += fee
                        holdings[sym] = 0.0
                        peak_prices[sym] = 0.0
                        
                        trade_records.append({
                            "date": current_date.strftime("%Y-%m-%d"),
                            "symbol": sym,
                            "action": "🚨 强制止损",
                            "price": px,
                            "shares": shares,
                            "fee": fee,
                            "reason": f"高点回撤 {dd*100:.1f}% 触发 6% 硬止损"
                        })
                        self.log_warning(f"[{current_date.strftime('%Y-%m-%d')}] {sym} 触碰止损线 (回撤 {dd*100:.1f}%)，立即强制清仓！")

            # 2. 定期周期轮动 (每 rebalance_days 天调仓)
            if i % rebalance_days == 0 and i > 60:
                # 获取昨天的因子打分进行选拔 (规避未来函数)
                scores = alpha_scores_df.iloc[i - 1].dropna()
                if len(scores) >= top_k:
                    top_candidates = list(scores.nlargest(top_k).index)
                    
                    # 卖出不在候选名单中的落后持仓
                    for sym in symbols:
                        if holdings[sym] > 0 and sym not in top_candidates:
                            px = today_prices[sym]
                            shares = holdings[sym]
                            revenue = shares * px
                            fee = revenue * get_market_fee_rate(sym)
                            cash += (revenue - fee)
                            total_fees += fee
                            holdings[sym] = 0.0
                            peak_prices[sym] = 0.0
                            
                            trade_records.append({
                                "date": current_date.strftime("%Y-%m-%d"),
                                "symbol": sym,
                                "action": "🔴 轮动剔除",
                                "price": px,
                                "shares": shares,
                                "fee": fee,
                                "reason": "因子得分落后，轮动换马"
                            })

                    # 计算当前总资产，并为目标股票平分资金
                    current_portfolio_val = cash + sum(holdings[s] * today_prices[s] for s in symbols)
                    target_val_per_stock = current_portfolio_val / float(top_k)

                    # 买入或补齐目标资产
                    for sym in top_candidates:
                        px = today_prices[sym]
                        current_stock_val = holdings[sym] * px
                        delta_val = target_val_per_stock - current_stock_val

                        # 若需要增仓且现金充足
                        if delta_val > 5000 and cash > 5000:
                            buy_val = min(delta_val, cash * 0.98)
                            fee_rate = get_market_fee_rate(sym)
                            net_val = buy_val / (1.0 + fee_rate)
                            shares = int(net_val / px)
                            if shares > 0:
                                cost = shares * px
                                fee = cost * fee_rate
                                cash -= (cost + fee)
                                total_fees += fee
                                holdings[sym] += shares
                                peak_prices[sym] = max(peak_prices[sym], px)

                                trade_records.append({
                                    "date": current_date.strftime("%Y-%m-%d"),
                                    "symbol": sym,
                                    "action": "🟢 轮动建仓",
                                    "price": px,
                                    "shares": shares,
                                    "fee": fee,
                                    "reason": f"综合因子得分排名前 {top_k}"
                                })

            # 3. 计算当日总资产净值
            stock_value = sum(holdings[s] * today_prices[s] for s in symbols)
            total_net = cash + stock_value
            daily_equity.append({
                "date": current_date,
                "equity": total_net,
                "cash": cash,
                "stock_value": stock_value
            })

            today_holdings = {s: holdings[s] * today_prices[s] / total_net for s in symbols}
            today_holdings["date"] = current_date
            holding_history.append(today_holdings)

        equity_df = pd.DataFrame(daily_equity)
        holding_df = pd.DataFrame(holding_history)

        # 4. 计算等权买入并持有基准 (Equal-Weight Benchmark)
        benchmark_returns = close_matrix.pct_change().mean(axis=1).fillna(0.0)
        benchmark_equity = initial_capital * (1.0 + benchmark_returns).cumprod()
        equity_df["benchmark"] = benchmark_equity.values

        # 绩效核心指标核算
        final_equity = equity_df["equity"].iloc[-1]
        total_return = (final_equity / initial_capital - 1.0) * 100
        bm_final = equity_df["benchmark"].iloc[-1]
        bm_total_return = (bm_final / initial_capital - 1.0) * 100

        # 最大回撤
        peak_series = np.maximum.accumulate(equity_df["equity"])
        drawdowns = (equity_df["equity"] - peak_series) / peak_series
        max_drawdown = drawdowns.min() * 100

        # 年化收益率与夏普
        days_total = (aligned_dates[-1] - aligned_dates[0]).days
        years = max(days_total / 365.25, 0.5)
        annual_return = ((final_equity / initial_capital) ** (1.0 / years) - 1.0) * 100
        
        daily_ret = equity_df["equity"].pct_change().dropna()
        sharpe = (daily_ret.mean() / (daily_ret.std() + 1e-6)) * np.sqrt(252)

        self.log_success(f"组合回测圆满结束！")
        self.log(f"  策略总收益率: {total_return:+.2f}% | 等权基准收益: {bm_total_return:+.2f}%")
        self.log(f"  年化收益率: {annual_return:+.2f}% | 最大回撤: {max_drawdown:.2f}% | 夏普比率: {sharpe:.2f}")
        self.log(f"  总交易笔数: {len(trade_records)} 笔 | 严扣印花税及手续费: {total_fees:,.2f} 元")

        context["equity_df"] = equity_df
        context["holding_df"] = holding_df
        context["trade_records"] = trade_records
        context["stats"] = {
            "initial_capital": initial_capital,
            "final_equity": final_equity,
            "total_return": total_return,
            "bm_total_return": bm_total_return,
            "annual_return": annual_return,
            "max_drawdown": max_drawdown,
            "sharpe": sharpe,
            "total_trades": len(trade_records),
            "total_fees": total_fees
        }
        return context
