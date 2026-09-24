"""多因子打分与仓位合成器
"""

import numpy as np
import pandas as pd


def combine_factors(factor_dict: dict[str, pd.Series], weights: dict[str, float] = None) -> pd.Series:
    """对多个因子进行 Z-Score 标准化，并按权重合成一个总分 (Composite Alpha Score)。
    
    参数:
    - factor_dict: {因子名: 因子时间序列}
    - weights: {因子名: 权重}，若不提供则默认等权平均
    """
    df_factors = pd.DataFrame(factor_dict)
    
    # 1. 因子去极值与 Z-Score 标准化: (X - mean) / std，使得不同因子的量纲统一
    normalized_df = (df_factors - df_factors.mean()) / (df_factors.std() + 1e-9)
    # 截断极值 (Winsorization) 到 [-3, +3] 并填充缺失值
    normalized_df = normalized_df.clip(-3, 3).fillna(0.0)

    # 2. 确定权重
    if not weights:
        weights = {col: 1.0 / len(normalized_df.columns) for col in normalized_df.columns}
    
    # 过滤掉权重为 0 或 NaN 的因子
    clean_weights = {k: max(v, 0.0) for k, v in weights.items() if not pd.isna(v)}
    if not clean_weights or sum(clean_weights.values()) == 0:
        clean_weights = {col: 1.0 / len(normalized_df.columns) for col in normalized_df.columns}

    weight_series = pd.Series(clean_weights)
    weight_series = weight_series / weight_series.sum()  # 归一化

    # 3. 加权合成分数
    composite_score = normalized_df[weight_series.index].dot(weight_series)
    return composite_score
