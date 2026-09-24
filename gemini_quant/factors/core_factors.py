"""微软 Qlib 风格与 WorldQuant 经典高级因子库 (30个神仙兵团)
适合 12 岁菜鸟看的超接地气分类:
1. 🚀 冲锋队 (短中长期动量，谁涨买谁)
2. 🪂 抄底反弹队 (跌过头了，皮球落地反弹)
3. 🕵️ 抓庄侦察兵 (主力资金、换手率放量异动)
4. 🦺 避险防暴队 (波动率、暴风雨前的平静)
5. 🎯 华尔街数学狙击手 (Alpha101 公式化因子)
"""

import numpy as np
import pandas as pd
from gemini_quant.factors.base import register_factor

# ==========================================
# 1. 🚀 冲锋队 (动量 / 趋势 / 均线)
# ==========================================

@register_factor(name="mom_3d", category="冲锋队", desc="3天超短线冲力 (短线爆发)")
def factor_mom_3d(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(3)

@register_factor(name="mom_5d", category="冲锋队", desc="5天短期冲力 (1周涨幅)")
def factor_mom_5d(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(5)

@register_factor(name="mom_10d", category="冲锋队", desc="10天两周冲力 (半月波段)")
def factor_mom_10d(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(10)

@register_factor(name="mom_20d", category="冲锋队", desc="20日月度大趋势 (月线牛熊)")
def factor_mom_20d(df: pd.DataFrame) -> pd.Series:
    return df["close"].pct_change(20)

@register_factor(name="trend_macd_diff", category="冲锋队", desc="MACD柱子 (快慢均线离散加速)")
def factor_macd_diff(df: pd.DataFrame) -> pd.Series:
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    return (dif - dea) / (df["close"] + 1e-6)

@register_factor(name="trend_ma_bias20", category="冲锋队", desc="20日均线乖离 (偏离生命线有多远)")
def factor_ma_bias20(df: pd.DataFrame) -> pd.Series:
    ma20 = df["close"].rolling(20).mean()
    return (df["close"] - ma20) / (ma20 + 1e-6)


# ==========================================
# 2. 🪂 抄底反弹队 (超跌反转 / 均值回归)
# ==========================================

@register_factor(name="rev_rsi6", category="抄底队", desc="6日超短线RSI (短线见底抓反弹)")
def factor_rsi6(df: pd.DataFrame) -> pd.Series:
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(6).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(6).mean()
    rsi = 100 - (100 / (1 + gain / (loss + 1e-9)))
    return 50.0 - rsi  # 越超跌越是正分

@register_factor(name="rev_rsi14", category="抄底队", desc="14日标准RSI (经典波段抄底)")
def factor_rsi14(df: pd.DataFrame) -> pd.Series:
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / (loss + 1e-9)))
    return 50.0 - rsi

@register_factor(name="rev_kdj_k", category="抄底队", desc="KDJ摆动超跌指标 (捕捉日内拐点)")
def factor_kdj_k(df: pd.DataFrame) -> pd.Series:
    low9 = df["low"].rolling(9).min()
    high9 = df["high"].rolling(9).max()
    rsv = (df["close"] - low9) / ((high9 - low9) + 1e-6) * 100
    k = rsv.ewm(com=2).mean()
    return 50.0 - k

@register_factor(name="rev_boll_pctb", category="抄底队", desc="布林下轨破位 (%B低于0说明严重跌过头)")
def factor_boll_pctb(df: pd.DataFrame) -> pd.Series:
    ma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    lower = ma20 - 2 * std20
    upper = ma20 + 2 * std20
    pct_b = (df["close"] - lower) / ((upper - lower) + 1e-6)
    return 0.5 - pct_b

@register_factor(name="rev_wr14", category="抄底队", desc="威廉超卖指标 (WR14跌透反弹)")
def factor_wr14(df: pd.DataFrame) -> pd.Series:
    high14 = df["high"].rolling(14).max()
    low14 = df["low"].rolling(14).min()
    wr = (high14 - df["close"]) / ((high14 - low14) + 1e-6) * 100
    return wr - 50.0  # wr越高越超跌


# ==========================================
# 3. 🕵️ 抓庄侦察兵 (量价资金 / 主力动向)
# ==========================================

@register_factor(name="vol_ratio_5d", category="抓庄队", desc="5天量比 (今天成交量是平时的几倍)")
def factor_vol_ratio(df: pd.DataFrame) -> pd.Series:
    ma_vol = df["volume"].rolling(20).mean()
    return df["volume"] / (ma_vol + 1e-9)

@register_factor(name="vol_obv_slope", category="抓庄队", desc="OBV能量潮5天斜率 (资金悄悄净买入)")
def factor_obv_slope(df: pd.DataFrame) -> pd.Series:
    direction = np.where(df["close"] > df["close"].shift(1), 1, np.where(df["close"] < df["close"].shift(1), -1, 0))
    obv = (direction * df["volume"]).cumsum()
    return obv.pct_change(5)

@register_factor(name="vol_price_diverge", category="抓庄队", desc="量价背离 (缩量新高通常是假突破)")
def factor_vol_price_diverge(df: pd.DataFrame) -> pd.Series:
    p_chg = df["close"].pct_change(5)
    v_chg = df["volume"].pct_change(5)
    return - (p_chg * v_chg)

@register_factor(name="vol_turnover_accel", category="抓庄队", desc="成交量加速膨胀 (突然爆巨量)")
def factor_turnover_accel(df: pd.DataFrame) -> pd.Series:
    v5 = df["volume"].rolling(5).mean()
    v10 = df["volume"].rolling(10).mean()
    return (v5 - v10) / (v10 + 1e-9)


# ==========================================
# 4. 🦺 避险防暴队 (波动率 / 变盘挤压)
# ==========================================

@register_factor(name="volat_atr_norm", category="防暴队", desc="归一化ATR波动率 (越稳越安全)")
def factor_atr(df: pd.DataFrame) -> pd.Series:
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    return - (atr / (df["close"] + 1e-6))

@register_factor(name="volat_squeeze", category="防暴队", desc="布林带极度挤压 (暴风雨前的平静，随时变盘)")
def factor_squeeze(df: pd.DataFrame) -> pd.Series:
    ma20 = df["close"].rolling(20).mean()
    std20 = df["close"].rolling(20).std()
    width = (4 * std20) / (ma20 + 1e-6)
    return - width.rolling(60).rank(pct=True)

@register_factor(name="volat_std_ratio", category="防暴队", desc="短期波动比长期波动 (突然异常骚动)")
def factor_volat_std_ratio(df: pd.DataFrame) -> pd.Series:
    std5 = df["close"].pct_change().rolling(5).std()
    std20 = df["close"].pct_change().rolling(20).std()
    return std5 / (std20 + 1e-6)


# ==========================================
# 5. 🎯 华尔街数学狙击手 (WorldQuant Alpha 101)
# ==========================================

@register_factor(name="alpha_101_006", category="狙击手", desc="Alpha#006: 开盘价与成交量负相关 (假阳线诱多)")
def factor_alpha_006(df: pd.DataFrame) -> pd.Series:
    return -1.0 * df["open"].rolling(10).corr(df["volume"])

@register_factor(name="alpha_101_pos", category="狙击手", desc="Alpha#101: 收盘在全天最高最低的什么位置")
def factor_alpha_101(df: pd.DataFrame) -> pd.Series:
    return (df["close"] - df["low"]) / ((df["high"] - df["low"]) + 1e-4)

@register_factor(name="alpha_101_012", category="狙击手", desc="Alpha#012: 价跌量增短线反转")
def factor_alpha_012(df: pd.DataFrame) -> pd.Series:
    vol_diff = np.sign(df["volume"].diff(1))
    price_diff = -1.0 * df["close"].diff(1)
    return vol_diff * price_diff

@register_factor(name="alpha_101_054", category="狙击手", desc="Alpha#054: 开高低收多空争夺力度")
def factor_alpha_054(df: pd.DataFrame) -> pd.Series:
    inner = (df["low"] - df["close"]) * (df["open"] ** 5)
    outer = (df["low"] - df["high"]) * (df["close"] ** 5)
    return -1.0 * (inner / (outer + 1e-6))
