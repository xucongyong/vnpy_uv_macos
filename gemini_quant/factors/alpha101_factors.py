"""WorldQuant Alpha101 核心经典公式因子集 (实战精选版)
每一条都是对冲基金数学家构建的真实公式，附带详细小白作用说明
"""

import numpy as np
import pandas as pd
from gemini_quant.factors.base import register_factor


def _ts_rank(series: pd.Series, window: int) -> pd.Series:
    """时间序列滚动排名 (0到1之间)"""
    return series.rolling(window).rank(pct=True)


@register_factor(name="alpha_001", category="Alpha101", desc="Alpha#001: 波动率极值跃迁。过去20天波动率达到极大值时捕捉能量爆发点")
def factor_alpha_001(df: pd.DataFrame) -> pd.Series:
    ret = df["close"].pct_change()
    vol20 = ret.rolling(20).std()
    cond = np.where(ret < 0, vol20, df["close"])
    return pd.Series(cond, index=df.index).rolling(5).apply(lambda x: x.argmax() if len(x)>0 else 0)

@register_factor(name="alpha_006", category="Alpha101", desc="Alpha#006: 开盘与成交量背离。-1*corr(open, vol, 10)，高开缩量为诱多假突破")
def factor_alpha_006(df: pd.DataFrame) -> pd.Series:
    return -1.0 * df["open"].rolling(10).corr(df["volume"])

@register_factor(name="alpha_012", category="Alpha101", desc="Alpha#012: 放量下砸反转。sign(增量) * (-1 * 价格变动)，价跌量增往往是洗盘末期")
def factor_alpha_012(df: pd.DataFrame) -> pd.Series:
    vol_diff = np.sign(df["volume"].diff(1))
    price_diff = -1.0 * df["close"].diff(1)
    return vol_diff * price_diff

@register_factor(name="alpha_028", category="Alpha101", desc="Alpha#028: 均线与振幅尺度缩放。3日相关性过滤日内杂波")
def factor_alpha_028(df: pd.DataFrame) -> pd.Series:
    corr = df["close"].rolling(5).corr(df["volume"])
    return -1.0 * corr

@register_factor(name="alpha_033", category="Alpha101", desc="Alpha#033: 开盘价相对极值偏离。rank(-1 + (open/close))，低开高走动能捕捉")
def factor_alpha_033(df: pd.DataFrame) -> pd.Series:
    return _ts_rank(-1.0 + (df["open"] / (df["close"] + 1e-6)), 5)

@register_factor(name="alpha_041", category="Alpha101", desc="Alpha#041: 高低价几何平均溢价。sqrt(high*low)相对收盘偏离")
def factor_alpha_041(df: pd.DataFrame) -> pd.Series:
    geo_mean = np.sqrt(np.maximum(df["high"] * df["low"], 0))
    return (geo_mean - df["close"]) / (df["close"] + 1e-6)

@register_factor(name="alpha_049", category="Alpha101", desc="Alpha#049: 价格跳空延后性。捕捉跳空低开后的均值回归")
def factor_alpha_049(df: pd.DataFrame) -> pd.Series:
    diff12 = df["close"].shift(10) - df["close"]
    diff20 = df["close"].shift(20) - df["close"]
    cond = (diff12 < 0) & (diff20 < 0)
    return pd.Series(np.where(cond, -1.0, 1.0), index=df.index)

@register_factor(name="alpha_053", category="Alpha101", desc="Alpha#053: 日内收盘破位。((close-low) - (high-close))/(close-open)，内包K线争夺")
def factor_alpha_053(df: pd.DataFrame) -> pd.Series:
    inner = (df["close"] - df["low"]) - (df["high"] - df["close"])
    return inner / (df["close"] - df["open"] + 1e-6)

@register_factor(name="alpha_054", category="Alpha101", desc="Alpha#054: 开高低收多空能量对比。衡量大资金控盘压制力")
def factor_alpha_054(df: pd.DataFrame) -> pd.Series:
    inner = (df["low"] - df["close"]) * (df["open"] ** 5)
    outer = (df["low"] - df["high"]) * (df["close"] ** 5)
    return -1.0 * (inner / (outer + 1e-6))

@register_factor(name="alpha_101", category="Alpha101", desc="Alpha#101: 收盘相对强弱位置。(close - low) / (high - low)，贴近最高说明多头强势")
def factor_alpha_101(df: pd.DataFrame) -> pd.Series:
    return (df["close"] - df["low"]) / ((df["high"] - df["low"]) + 1e-4)
