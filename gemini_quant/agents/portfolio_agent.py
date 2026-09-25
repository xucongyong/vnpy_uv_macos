"""组合轮动特工 (PortfolioAgent) - 带换手迟滞缓冲带与 ATR 自适应风控

负责资产池动态资金分配、基于 15% 迟滞缓冲带的防过度交易优胜劣汰、
ATR 动态止损防御及跨市场交易费率精准扣减。
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
    """负责跨市场多资产横截面调仓与迟滞缓冲资金轮动的特工"""

    def __init__(self, name: str = "Quartermaster"):
        super().__init__(
            name=name,
            role_title="组合轮动特工",
            emoji="⚖️",
            color_code=COLOR_GREEN
        )
        self.hysteresis_threshold = 0.15  # 15% 护城河缓冲带: 新标的分数必须显著超越持仓老标的 15% 才准换仓

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        bars_dict: Dict[str, pd.DataFrame] = context["bars_dict"]
        aligned_dates: List[pd.Timestamp] = context["aligned_dates"]
        alpha_scores_df: pd.DataFrame = context["alpha_scores_df"]
        atr_stop_df: pd.DataFrame = context.get("risk_rules", {}).get("atr_stop_df")
        top_k: int = context.get("top_k", 2)
        rebalance_days: int = context.get("rebalance_days", 5)
        initial_capital: float = context.get("initial_capital", 1_000_000.0)

        symbols = list(bars_dict.keys())
        self.log(f"启动【低换手·高胜率】组合轮动回测 (初始本金: {initial_capital:,.0f} 元, 设立 {self.hysteresis_threshold*100:.0f}% 防折腾护城河)...")

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

            # 1. 每日盘中 ATR 自适应动态硬止损 (根据标的自身真实波幅动态调节，防恶意洗盘)
            for sym in symbols:
                if holdings[sym] > 0:
                    px = today_prices[sym]
                    if px > peak_prices[sym]:
                        peak_prices[sym] = px
                    
                    # 读取该标的在当天的专属动态 ATR 止损线
                    if atr_stop_df is not None and sym in atr_stop_df.columns:
                        current_stop_pct = atr_stop_df.iloc[i][sym]
                    else:
                        current_stop_pct = 0.07

                    dd = (peak_prices[sym] - px) / peak_prices[sym]
                    if dd >= current_stop_pct:
                        # 触发 ATR 动态止损，坚决清仓保命
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
                            "action": "🚨 ATR自适应止损",
                            "price": px,
                            "shares": shares,
                            "fee": fee,
                            "reason": f"回撤 {dd*100:.1f}% 触碰动态止损阈值 ({current_stop_pct*100:.1f}%)"
                        })
                        self.log_warning(f"[{current_date.strftime('%Y-%m-%d')}] {sym} 触碰专属动态止损线 {current_stop_pct*100:.1f}%，立即清仓！")

            # 2. 定期周期轮动 (带 15% 迟滞缓冲带，消除频繁摩擦)
            if i % rebalance_days == 0 and i > 60:
                scores = alpha_scores_df.iloc[i - 1].dropna()
                if len(scores) >= top_k:
                    # 当前持有的股票集合
                    held_symbols = [s for s in symbols if holdings[s] > 0]
                    
                    # 确定最新入选名单 (带迟滞缓冲带机制)
                    score_range = max(scores.max() - scores.min(), 0.1)
                    buffer_points = self.hysteresis_threshold * score_range

                    # 先找初始全局 Top-K 候选
                    all_sorted = list(scores.nlargest(len(symbols)).index)
                    candidate_pool = list(all_sorted[:top_k])

                    # 缓冲带审查: 如果持仓老股票不在 candidate_pool 里，但其分数并没有落后第 top_k 名超过 buffer_points，继续保护！
                    final_selected = []
                    # 先让表现依旧优异的老标的优先保级
                    for h_sym in held_symbols:
                        # 如果老标的依然排在稳健区间 (例如排在前 top_k+1)，且分数落后不严重
                        if h_sym in all_sorted:
                            rank = all_sorted.index(h_sym)
                            if rank <= top_k:  # 本身就在前列
                                final_selected.append(h_sym)
                            elif rank == top_k:  # 刚好在边界，比较分差
                                boundary_score = scores[candidate_pool[-1]]
                                if (boundary_score - scores[h_sym]) < buffer_points:
                                    final_selected.append(h_sym)

                    # 用最高分的新候选填满剩余名额
                    for cand in all_sorted:
                        if cand not in final_selected:
                            final_selected.append(cand)
                        if len(final_selected) >= top_k:
                            break

                    # ① 卖出真正破位、被彻底剔除的老持仓
                    for sym in symbols:
                        if holdings[sym] > 0 and sym not in final_selected:
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
                                "reason": "因子得分显著跌出梯队，换马淘汰"
                            })

                    # ② 动态分配资金到目标选拔标的
                    current_portfolio_val = cash + sum(holdings[s] * today_prices[s] for s in symbols)
                    target_val_per_stock = current_portfolio_val / float(top_k)

                    # 只有当持仓偏差超过目标权重的 12% 时才执行调仓补齐，避免微量调仓交手续费
                    for sym in final_selected:
                        px = today_prices[sym]
                        current_stock_val = holdings[sym] * px
                        delta_val = target_val_per_stock - current_stock_val

                        if delta_val > (target_val_per_stock * 0.12) and cash > 10000:
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
                                    "reason": f"突破15%护城河，强势入选Top-{top_k}"
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

        self.log_success(f"低换手组合回测圆满结束！")
        self.log(f"  策略总收益率: {total_return:+.2f}%  vs  基准收益率: {bm_total_return:+.2f}%")
        self.log(f"  年化复合收益率: {annual_return:+.2f}% | 最大回撤: {max_drawdown:.2f}% | 夏普比率: {sharpe:.2f}")
        self.log(f"  总交易笔数: {len(trade_records)} 笔 | 严扣印花税及手续费: {total_fees:,.2f} 元 (大幅压降!)")

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
