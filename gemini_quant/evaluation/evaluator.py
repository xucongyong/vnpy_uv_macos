"""因子质量评估与体检模块: 计算 IC, Rank IC, IC_IR 与胜率
"""

import numpy as np
import pandas as pd


def evaluate_factor_on_symbol(factor_series: pd.Series, close_series: pd.Series, forward_periods: int = 5) -> dict:
    """计算单个因子在某个标的上的预测能力指标。
    
    指标解析:
    - IC (Information Coefficient): 因子数值与未来N天收益率的 Pearson 相关系数 (-1 到 1)
    - Rank IC: 斯皮尔曼秩相关系数 (排序预测力，更抗极端值干扰)
    - Win Rate: 因子方向与未来涨跌一致的胜率比例
    """
    # 预测目标: 未来 N 天的收益率
    future_returns = close_series.pct_change(forward_periods).shift(-forward_periods)
    
    valid_data = pd.DataFrame({
        "factor": factor_series,
        "forward_ret": future_returns
    }).dropna()

    if len(valid_data) < 30:
        return {"ic": 0.0, "rank_ic": 0.0, "win_rate": 0.5, "n_samples": len(valid_data)}

    # 计算全局 IC 与 Rank IC
    ic = valid_data["factor"].corr(valid_data["forward_ret"], method="pearson")
    rank_ic = valid_data["factor"].corr(valid_data["forward_ret"], method="spearman")

    # 滚动切片计算 IC 的稳定性 (IC_IR)
    rolling_ic = valid_data["factor"].rolling(20).corr(valid_data["forward_ret"])
    ic_mean = rolling_ic.mean()
    ic_std = rolling_ic.std()
    ic_ir = (ic_mean / (ic_std + 1e-6)) * np.sqrt(252 / 20)  # 年化 IR

    # 简易胜率: 因子大于均值时未来涨，或因子小于均值时未来跌
    mean_val = valid_data["factor"].mean()
    win = ((valid_data["factor"] > mean_val) & (valid_data["forward_ret"] > 0)) | \
          ((valid_data["factor"] < mean_val) & (valid_data["forward_ret"] < 0))
    win_rate = win.mean()

    return {
        "ic": round(float(ic), 4),
        "rank_ic": round(float(rank_ic), 4),
        "ic_ir": round(float(ic_ir), 2),
        "win_rate": round(float(win_rate * 100), 2),
        "n_samples": len(valid_data)
    }
