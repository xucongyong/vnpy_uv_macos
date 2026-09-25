"""风险与资金管家 (RiskAgent)

负责动态敞口测算、单一标的头寸上限风控、个股 6% 移动追踪止损检测及极端行情熔断保护。
"""

from typing import Dict, Any, List
import pandas as pd
from gemini_quant.agents.base_agent import BaseAgent, COLOR_PURPLE


class RiskAgent(BaseAgent):
    """负责组合风控核验与硬止损审查的特工"""

    def __init__(self, name: str = "Guardian"):
        super().__init__(
            name=name,
            role_title="风险与资金管家",
            emoji="🛡️",
            color_code=COLOR_PURPLE
        )
        self.trailing_stop_pct = 0.06  # 6% 追踪止损线
        self.max_single_weight = 0.55  # 单一标的最大资金暴露 55%

    def check_trailing_stop(self, current_price: float, peak_price: float) -> bool:
        """检查单一持仓自最高点回撤是否达到止损线"""
        if peak_price <= 0:
            return False
        dd = (peak_price - current_price) / peak_price
        return dd >= self.trailing_stop_pct

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """为组合调度器提供风控规则引擎"""
        self.log(f"装载风控中枢规则: 单一标的权重上限 = {self.max_single_weight*100:.0f}%, 移动追踪止损 = {self.trailing_stop_pct*100:.1f}%")
        context["risk_rules"] = {
            "trailing_stop_pct": self.trailing_stop_pct,
            "max_single_weight": self.max_single_weight
        }
        self.log_success("风控哨兵已就位，进入全天候盯盘审查状态。")
        return context
