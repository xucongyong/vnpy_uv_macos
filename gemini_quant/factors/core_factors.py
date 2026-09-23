"""精选经典因子库示例: 包含动量、反转、波动率、量价、经典 Alpha101
"""

import numpy as np
import pandas as pd
from gemini_quant.factors.base import register_factor


@register_factor(name="momentum_5d", category="momentum", desc="5日价格动量 (短期冲力)")
def factor_momentum_5d(df: pd.DataFrame) -> pd.Series:
    """5日收益率: 过去5天涨得越猛，数值越大"""
    return df["close"].pct_change(5)


@register_factor(name="momentum_20d", category="momentum", desc="20日中期动量 (月度趋势)")
def factor_momentum_20d(df: pd.DataFrame) -> pd.Series:
    """20日收益率: 捕捉中期走势"""
    return df["close"].pct_change(20)


@register_factor(name="reversion_rsi14", category="reversion", desc="RSI反转指标 (超买超卖)")
def factor_rsi14(df: pd.DataFrame) -> pd.Series:
    """经典 RSI: 数值越低代表超卖超跌，反弹动力越强 (取反作为买入因子)"""
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    # 50 - rsi: 越超跌越呈现正因子值
    return 50.0 - rsi


@register_factor(name="volatility_20d", category="volatility", desc="20日历史波动率 (低波动通常更稳定)")
def factor_volatility_20d(df: pd.DataFrame) -> pd.Series:
    """20日对数收益率标准差: 低波动取负值作为稳健因子"""
    ret = np.log(df["close"] / df["close"].shift(1))
    vol = ret.rolling(20).std()
    return -vol  # 负波动率: 越稳的股票得分越高


@register_factor(name="volume_ratio_5d", category="volume", desc="5日量比 (放量异动)")
def factor_volume_ratio(df: pd.DataFrame) -> pd.Series:
    """5日均量 / 20日均量: 捕捉资金放量介入信号"""
    ma_vol_5 = df["volume"].rolling(5).mean()
    ma_vol_20 = df["volume"].rolling(20).mean()
    return ma_vol_5 / (ma_vol_20 + 1e-9)


@register_factor(name="alpha_101_pos", category="alpha101", desc="收盘在当日K线中的相对强弱位置")
def factor_alpha101_pos(df: pd.DataFrame) -> pd.Series:
    """(close - low) / (high - low): 收盘越接近最高点，买方意愿越强"""
    return (df["close"] - df["low"]) / ((df["high"] - df["low"]) + 1e-4)
