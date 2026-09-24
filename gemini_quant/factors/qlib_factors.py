"""微软 Qlib Alpha158 核心工业因子集 (精选 30 个最具实战价值的高频特征)
涵盖: K线形态、短中长动量、价格波动率、线性回归斜率、趋势决定系数、量价相关性
"""

import numpy as np
import pandas as pd
from gemini_quant.factors.base import register_factor


# ----------------------------------------------------
# 1. K线多空博弈形态特征 (Candlestick Patterns)
# ----------------------------------------------------

@register_factor(name="qlib_kmid", category="K线形态", desc="实体强弱: (收盘-开盘)/开盘，衡量日内真实涨跌实体力度")
def qlib_kmid(df: pd.DataFrame) -> pd.Series:
    return (df["close"] - df["open"]) / (df["open"] + 1e-6)

@register_factor(name="qlib_klen", category="K线形态", desc="日内振幅: (最高-最低)/开盘，衡量日内总体波动空间")
def qlib_klen(df: pd.DataFrame) -> pd.Series:
    return (df["high"] - df["low"]) / (df["open"] + 1e-6)

@register_factor(name="qlib_kup", category="K线形态", desc="上影线长度: (最高-max(开,收))/开盘，衡量上方抛压阻力")
def qlib_kup(df: pd.DataFrame) -> pd.Series:
    higher = np.maximum(df["open"], df["close"])
    return (df["high"] - higher) / (df["open"] + 1e-6)

@register_factor(name="qlib_klow", category="K线形态", desc="下影线长度: (min(开,收)-最低)/开盘，衡量下方多头承接力")
def qlib_klow(df: pd.DataFrame) -> pd.Series:
    lower = np.minimum(df["open"], df["close"])
    return (lower - df["low"]) / (df["open"] + 1e-6)

@register_factor(name="qlib_ksft", category="K线形态", desc="重心偏移度: (2*收盘 - 最高 - 最低)/开盘，衡量收盘相对全天重心的位置")
def qlib_ksft(df: pd.DataFrame) -> pd.Series:
    return (df["close"] * 2 - df["high"] - df["low"]) / (df["open"] + 1e-6)


# ----------------------------------------------------
# 2. 经典多周期动量与变化率 (ROC / Momentum)
# ----------------------------------------------------

@register_factor(name="qlib_roc_5", category="动量变化", desc="5日价格变动率: 5天前收盘价 / 今日收盘价")
def qlib_roc_5(df: pd.DataFrame) -> pd.Series:
    return df["close"].shift(5) / (df["close"] + 1e-6)

@register_factor(name="qlib_roc_10", category="动量变化", desc="10日价格变动率: 10天前收盘价 / 今日收盘价")
def qlib_roc_10(df: pd.DataFrame) -> pd.Series:
    return df["close"].shift(10) / (df["close"] + 1e-6)

@register_factor(name="qlib_roc_20", category="动量变化", desc="20日价格变动率: 20天前收盘价 / 今日收盘价")
def qlib_roc_20(df: pd.DataFrame) -> pd.Series:
    return df["close"].shift(20) / (df["close"] + 1e-6)

@register_factor(name="qlib_roc_60", category="动量变化", desc="60日季度大变动率: 季度级别大趋势")
def qlib_roc_60(df: pd.DataFrame) -> pd.Series:
    return df["close"].shift(60) / (df["close"] + 1e-6)


# ----------------------------------------------------
# 3. 均线相对偏离度 (MA / Price Bias)
# ----------------------------------------------------

@register_factor(name="qlib_ma_5", category="均线偏离", desc="5日均线相对收盘价比: 衡量超短期均线支撑")
def qlib_ma_5(df: pd.DataFrame) -> pd.Series:
    return df["close"].rolling(5).mean() / (df["close"] + 1e-6)

@register_factor(name="qlib_ma_10", category="均线偏离", desc="10日均线相对收盘价比: 衡量半月均线位置")
def qlib_ma_10(df: pd.DataFrame) -> pd.Series:
    return df["close"].rolling(10).mean() / (df["close"] + 1e-6)

@register_factor(name="qlib_ma_20", category="均线偏离", desc="20日生命线相对收盘价比: 衡量月线偏离")
def qlib_ma_20(df: pd.DataFrame) -> pd.Series:
    return df["close"].rolling(20).mean() / (df["close"] + 1e-6)

@register_factor(name="qlib_ma_60", category="均线偏离", desc="60日季度均线相对收盘价比: 衡量大趋势偏离")
def qlib_ma_60(df: pd.DataFrame) -> pd.Series:
    return df["close"].rolling(60).mean() / (df["close"] + 1e-6)


# ----------------------------------------------------
# 4. 波动率与价格标准差 (Volatility & Risk)
# ----------------------------------------------------

@register_factor(name="qlib_std_5", category="波动风险", desc="5日短期波动率相对收盘比: 捕捉短线剧烈异动")
def qlib_std_5(df: pd.DataFrame) -> pd.Series:
    return df["close"].rolling(5).std() / (df["close"] + 1e-6)

@register_factor(name="qlib_std_20", category="波动风险", desc="20日中期波动率相对收盘比: 衡量常规风险水平")
def qlib_std_20(df: pd.DataFrame) -> pd.Series:
    return df["close"].rolling(20).std() / (df["close"] + 1e-6)

@register_factor(name="qlib_std_60", category="波动风险", desc="60日长期波动率相对收盘比: 衡量季度稳定性")
def qlib_std_60(df: pd.DataFrame) -> pd.Series:
    return df["close"].rolling(60).std() / (df["close"] + 1e-6)


# ----------------------------------------------------
# 5. 趋势斜率与决定系数 (Slope & R-Square)
# ----------------------------------------------------

def _rolling_slope(series: pd.Series, window: int) -> pd.Series:
    x = np.arange(window)
    x_mean = x.mean()
    x_var = ((x - x_mean)**2).sum()
    def calc_slope(y):
        if len(y) < window or np.isnan(y).any():
            return np.nan
        y_mean = y.mean()
        cov = ((x - x_mean) * (y - y_mean)).sum()
        return cov / x_var
    return series.rolling(window).apply(calc_slope, raw=True)

@register_factor(name="qlib_beta_5", category="趋势斜率", desc="5日价格线性回归斜率: 衡量短期拉升角度")
def qlib_beta_5(df: pd.DataFrame) -> pd.Series:
    return _rolling_slope(df["close"], 5) / (df["close"] + 1e-6)

@register_factor(name="qlib_beta_20", category="趋势斜率", desc="20日价格线性回归斜率: 衡量中期上升通道角度")
def qlib_beta_20(df: pd.DataFrame) -> pd.Series:
    return _rolling_slope(df["close"], 20) / (df["close"] + 1e-6)


# ----------------------------------------------------
# 6. 成交量比率与异动特征 (Volume Dynamics)
# ----------------------------------------------------

@register_factor(name="qlib_vma_5", category="量能异动", desc="5日均量相对当前成交量: 衡量短线成交活跃度")
def qlib_vma_5(df: pd.DataFrame) -> pd.Series:
    return df["volume"].rolling(5).mean() / (df["volume"] + 1e-9)

@register_factor(name="qlib_vma_20", category="量能异动", desc="20日均量相对当前成交量: 衡量中线换手水平")
def qlib_vma_20(df: pd.DataFrame) -> pd.Series:
    return df["volume"].rolling(20).mean() / (df["volume"] + 1e-9)

@register_factor(name="qlib_vstd_5", category="量能异动", desc="5日成交量波动离散度: 成交量忽大忽小通常预示变盘")
def qlib_vstd_5(df: pd.DataFrame) -> pd.Series:
    return df["volume"].rolling(5).std() / (df["volume"] + 1e-9)

@register_factor(name="qlib_vstd_20", category="量能异动", desc="20日成交量波动离散度: 衡量中期资金博弈剧烈度")
def qlib_vstd_20(df: pd.DataFrame) -> pd.Series:
    return df["volume"].rolling(20).std() / (df["volume"] + 1e-9)
