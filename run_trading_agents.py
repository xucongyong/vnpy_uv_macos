#!/usr/bin/env python3
"""TradingAgents 多智能体并行协同调度中枢

负责协调 5 大专业智能体 (数据特工/因子特工/组合特工/风控特工/大屏秘书)，
执行跨市场多资产横截面轮动与严格扣费回测大考。
"""

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from gemini_quant.agents.data_agent import DataAgent
from gemini_quant.agents.alpha_agent import AlphaAgent
from gemini_quant.agents.risk_agent import RiskAgent
from gemini_quant.agents.portfolio_agent import PortfolioAgent
from gemini_quant.agents.reporter_agent import ReporterAgent
from gemini_quant.agents.base_agent import COLOR_BOLD, COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, COLOR_RESET


def print_banner():
    banner = f"""{COLOR_CYAN}{COLOR_BOLD}
========================================================================================
🏛️   T R A D I N G   A G E N T S   ·   量 化 对 冲 基 金 多 智 能 体 联合作战作战室
========================================================================================
[1] 🕵️‍♂️ 数据清洗特工 · Scout         | 负责跨市场异构数据清洗、交易日历对齐与去噪
[2] 🔬 因子挖掘体检官 · Miner        | 负责 285 因子全量特征工程与每日横截面相对强弱打分
[3] 🛡️ 风险与资金管家 · Guardian     | 负责动态 VaR 测算、单标的头寸上限与 6% 移动硬止损审查
[4] ⚖️ 组合轮动特工 · Quartermaster  | 负责资金动态分配、Top-K 资产周期轮动与跨市场严扣费回测
[5] 📊 大屏汇报秘书 · Secretary      | 负责汇总各特工决策账本，渲染交互式 Plotly 多资产大屏
========================================================================================{COLOR_RESET}
"""
    print(banner)


def main():
    parser = argparse.ArgumentParser(description="TradingAgents 多智能体协同作战中枢")
    parser.add_argument("--symbols", default="AAPL.NASDAQ,00700.SEHK,000001.SZSE,AMAT.NASDAQ,INTC.NASDAQ",
                        help="跨市场标的池(逗号分隔)")
    parser.add_argument("--days", type=int, default=750, help="回测历史天数")
    parser.add_argument("--top_k", type=int, default=2, help="每次轮动持仓前K名标的")
    parser.add_argument("--rebalance_days", type=int, default=5, help="调仓周期(天)")
    parser.add_argument("--capital", type=float, default=1_000_000.0, help="初始本金(元)")
    parser.add_argument("--output", default="multi_agent_portfolio_report.html", help="输出HTML报表路径")
    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]

    print_banner()

    context = {
        "symbols": symbols,
        "days": args.days,
        "top_k": args.top_k,
        "rebalance_days": args.rebalance_days,
        "initial_capital": args.capital,
        "output_html": args.output
    }

    # 1. 初始化 5 大专业智能体
    data_agent = DataAgent(name="Scout")
    alpha_agent = AlphaAgent(name="Miner")
    risk_agent = RiskAgent(name="Guardian")
    portfolio_agent = PortfolioAgent(name="Quartermaster")
    reporter_agent = ReporterAgent(name="Secretary")

    start_time = time.time()

    # 2. 依次调度智能体作业 (流水线协作)
    print(f"\n{COLOR_BOLD}>>> [阶段 1/5] 激活数据特工，调度数据清洗与对齐...{COLOR_RESET}")
    context = data_agent.run(context)

    print(f"\n{COLOR_BOLD}>>> [阶段 2/5] 激活因子挖掘体检官，执行 285 因子横截面打分...{COLOR_RESET}")
    context = alpha_agent.run(context)

    print(f"\n{COLOR_BOLD}>>> [阶段 3/5] 激活风险与资金管家，布设风控警戒线...{COLOR_RESET}")
    context = risk_agent.run(context)

    print(f"\n{COLOR_BOLD}>>> [阶段 4/5] 激活组合轮动特工，执行跨市场轮动回测与印花税扣减...{COLOR_RESET}")
    context = portfolio_agent.run(context)

    print(f"\n{COLOR_BOLD}>>> [阶段 5/5] 激活大屏秘书，汇总团队成果并生成交互大屏...{COLOR_RESET}")
    context = reporter_agent.run(context)

    elapsed = time.time() - start_time
    stats = context["stats"]

    # 3. 打印团队最终战报
    print(f"\n{COLOR_GREEN}{COLOR_BOLD}" + "="*88)
    print(f"🎉 团队联合作战大功告成！总耗时: {elapsed:.2f} 秒")
    print("="*88 + f"{COLOR_RESET}")
    print(f"  💰 初始资金: {stats['initial_capital']:,.0f} 元 ➔ 最终净资产: {stats['final_equity']:,.0f} 元")
    print(f"  📈 策略总收益率: {stats['total_return']:+.2f}%  vs  基准收益率: {stats['bm_total_return']:+.2f}%")
    print(f"  🌟 年化复合收益率: {stats['annual_return']:+.2f}% | 夏普比率: {stats['sharpe']:.2f}")
    print(f"  🛡️ 最大资产回撤: {stats['max_drawdown']:.2f}% | 交易总笔数: {stats['total_trades']} 笔")
    print(f"  💸 严格扣除交易税费与滑点: -{stats['total_fees']:,.2f} 元")
    print(f"  📊 交互大屏已就绪: {args.output}")
    print("="*88 + "\n")


if __name__ == "__main__":
    main()
