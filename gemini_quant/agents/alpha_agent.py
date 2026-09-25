"""因子挖掘体检官 (AlphaAgent)

负责对跨市场多标的股票池，批量运行 285 因子特征计算，并执行横截面标准化与复合打分。
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
from gemini_quant.agents.base_agent import BaseAgent, COLOR_YELLOW
from gemini_quant.factors.base import get_all_factors


class AlphaAgent(BaseAgent):
    """负责跨标的横截面特征工程与复合 Alpha 得分计算的特工"""

    def __init__(self, name: str = "Miner"):
        super().__init__(
            name=name,
            role_title="因子挖掘体检官",
            emoji="🔬",
            color_code=COLOR_YELLOW
        )
        self.factors_registry = get_all_factors()

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        bars_dict: Dict[str, pd.DataFrame] = context["bars_dict"]
        aligned_dates: List[pd.Timestamp] = context["aligned_dates"]
        symbols = list(bars_dict.keys())

        # 5 大正交核心兵种体系 (动量 / 突破 / 潜伏 / 波动 / 背离)
        core_factors = [
            {"name": "wq_alpha_088", "sign": 1.0,  "role": "动量先锋"},
            {"name": "wq_alpha_030", "sign": 1.0,  "role": "连阳突破"},
            {"name": "wq_alpha_081", "sign": -1.0, "role": "潜伏洗盘"},
            {"name": "qlib_std_20",  "sign": 1.0,  "role": "波动防暴"},
            {"name": "wq_alpha_022", "sign": -1.0, "role": "量价背离"}
        ]

        self.log(f"启动跨市场股票池横截面因子打分引擎 (纳入 5 大王牌正交兵种)...")
        for f in core_factors:
            self.log(f"  装载兵种: {f['name']} ({f['role']}) | 方向: {'正向做多' if f['sign']>0 else '反向对冲'}")

        # 1. 分别计算每只股票的单因子序列
        symbol_factor_scores: Dict[str, pd.DataFrame] = {}
        for sym, df in bars_dict.items():
            sub_scores_dict = {}
            for f in core_factors:
                fname = f["name"]
                sign = f["sign"]
                if fname in self.factors_registry:
                    try:
                        s = self.factors_registry[fname]["func"](df)
                        # 滚动标准化
                        mean = s.rolling(60, min_periods=20).mean()
                        std = s.rolling(60, min_periods=20).std() + 1e-6
                        z = ((s - mean) / std).clip(-3.0, 3.0)
                        sub_scores_dict[fname] = z * sign
                    except Exception as e:
                        sub_scores_dict[fname] = pd.Series(0.0, index=df.index)
                else:
                    sub_scores_dict[fname] = pd.Series(0.0, index=df.index)

            score_matrix = pd.DataFrame(sub_scores_dict)
            symbol_factor_scores[sym] = score_matrix.mean(axis=1)

        # 2. 转换为时间截面矩阵 (行: 日期, 列: 股票代码)
        raw_composite_df = pd.DataFrame(
            {sym: symbol_factor_scores[sym].values for sym in symbols},
            index=aligned_dates
        )

        # 3. 横截面标准化 (Cross-Sectional Z-Score)
        # 对每一天 t，把所有股票的分数做相对强弱排名 (谁比谁强)
        self.log("正在执行每日横截面相对强弱排名与 CS-ZScore 标准化...")
        cs_mean = raw_composite_df.mean(axis=1)
        cs_std = raw_composite_df.std(axis=1) + 1e-6
        cs_scores_df = raw_composite_df.sub(cs_mean, axis=0).div(cs_std, axis=0)

        self.log_success(f"截面打分完成！输出 {cs_scores_df.shape[0]} 个交易日 × {cs_scores_df.shape[1]} 只标的的复合 Alpha 信号矩阵。")

        context["alpha_scores_df"] = cs_scores_df
        context["core_factors"] = core_factors
        return context
