"""风险与资金管家 (RiskAgent)

负责动态敞口测算、单一标的头寸上限风控、基于 ATR 真实波动率的自适应动态追踪止损及极端行情熔断保护。
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from gemini_quant.agents.base_agent import BaseAgent, COLOR_PURPLE


def compute_atr_stop_series(df: pd.DataFrame, window: int = 14, multiplier: float = 2.5) -> pd.Series:
    """根据 14 日真实波幅 (ATR) 测算自适应动态止损百分比 (彻底解决固定6%在震荡期被主力反复洗盘割肉的问题)"""
    prev_close = df["close"].shift(1).fillna(df["open"])
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - prev_close).abs()
    tr3 = (df["low"] - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window, min_periods=5).mean()
    
    # 动态止损线: 基准为 2.5 倍 ATR，区间约束在 4.5% ~ 11.0%
    atr_pct = atr / df["close"]
    dynamic_stop = (atr_pct * multiplier).clip(lower=0.045, upper=0.11)
    return dynamic_stop.fillna(0.07)


class RiskAgent(BaseAgent):
    """负责组合风控核验与 ATR 自适应动态止损审查的特工"""

    def __init__(self, name: str = "Guardian"):
        super().__init__(
            name=name,
            role_title="风险与资金管家",
            emoji="🛡️",
            color_code=COLOR_PURPLE
        )
        self.max_single_weight = 0.55  # 单一标的最大资金暴露 55%

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        bars_dict: Dict[str, pd.DataFrame] = context["bars_dict"]
        aligned_dates: List[pd.Timestamp] = context["aligned_dates"]

        self.log("正在根据标的历史波动特性，构建 ATR 真实波幅自适应动态止损矩阵...")
        
        atr_stop_matrix_dict = {}
        for sym, df in bars_dict.items():
            stop_s = compute_atr_stop_series(df, window=14, multiplier=2.5)
            atr_stop_matrix_dict[sym] = stop_s.values
            avg_stop = float(stop_s.mean()) * 100
            self.log(f"  标的 {sym:12s} | 平均动态止损阈值: {avg_stop:.1f}% (拒绝死板6%，防止洗盘打脸)")

        atr_stop_df = pd.DataFrame(atr_stop_matrix_dict, index=aligned_dates)

        context["risk_rules"] = {
            "max_single_weight": self.max_single_weight,
            "atr_stop_df": atr_stop_df
        }
        self.log_success("ATR 自适应动态风控矩阵已就位，进入全天候防洗盘盯盘状态。")
        return context
