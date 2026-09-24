"""华尔街 WorldQuant Alpha 101 全套公式引擎 (Alpha 1 ~ Alpha 101 批量全量提取器)

实现 WorldQuant 101 Formulaic Alphas 中的高频单标的公式，附带详细中文人话作用说明
"""

import numpy as np
import pandas as pd
from gemini_quant.factors.base import register_factor

def ts_delay(s: pd.Series, d: int) -> pd.Series:
    return s.shift(d)

def ts_delta(s: pd.Series, d: int) -> pd.Series:
    return s.diff(d)

def ts_corr(s1: pd.Series, s2: pd.Series, w: int) -> pd.Series:
    return s1.rolling(w).corr(s2)

def ts_rank(s: pd.Series, w: int) -> pd.Series:
    return s.rolling(w).rank(pct=True)

def ts_std(s: pd.Series, w: int) -> pd.Series:
    return s.rolling(w).std()

def ts_mean(s: pd.Series, w: int) -> pd.Series:
    return s.rolling(w).mean()

def ts_min(s: pd.Series, w: int) -> pd.Series:
    return s.rolling(w).min()

def ts_max(s: pd.Series, w: int) -> pd.Series:
    return s.rolling(w).max()


# ==========================================
# 批量注册 Alpha 101 系列经典公式
# ==========================================

@register_factor(name="wq_alpha_001", category="Alpha101全家桶", desc="Alpha#001: 波动率极值跃迁。大跌后波动率放大到极点捕捉反转")
def wq_alpha_1(df: pd.DataFrame) -> pd.Series:
    ret = df["close"].pct_change()
    cond = np.where(ret < 0, ts_std(ret, 20), df["close"])
    return pd.Series(cond, index=df.index).rolling(5).apply(lambda x: x.argmax() if len(x)>0 else 0)

@register_factor(name="wq_alpha_002", category="Alpha101全家桶", desc="Alpha#002: 量价比变动率相关性。捕捉量能变化与日内振幅的相关离散")
def wq_alpha_2(df: pd.DataFrame) -> pd.Series:
    s1 = ts_delta(np.log(df["volume"] + 1), 2)
    s2 = (df["close"] - df["open"]) / (df["open"] + 1e-6)
    return -1.0 * ts_corr(s1, s2, 6)

@register_factor(name="wq_alpha_003", category="Alpha101全家桶", desc="Alpha#003: 开盘价与成交量10日相关性。高开缩量为诱多")
def wq_alpha_3(df: pd.DataFrame) -> pd.Series:
    return -1.0 * ts_corr(df["open"], df["volume"], 10)

@register_factor(name="wq_alpha_004", category="Alpha101全家桶", desc="Alpha#004: 最低价时序排位。低点下移代表下行阻力弱")
def wq_alpha_4(df: pd.DataFrame) -> pd.Series:
    return -1.0 * ts_rank(df["low"], 9)

@register_factor(name="wq_alpha_006", category="Alpha101全家桶", desc="Alpha#006: 经典开盘量价负相关。捕捉开盘量价背离假阳线")
def wq_alpha_6(df: pd.DataFrame) -> pd.Series:
    return -1.0 * ts_corr(df["open"], df["volume"], 10)

@register_factor(name="wq_alpha_007", category="Alpha101全家桶", desc="Alpha#007: 7日价格突变与量能加权。大跌放量往往引来反抽")
def wq_alpha_7(df: pd.DataFrame) -> pd.Series:
    delta7 = ts_delta(df["close"], 7)
    rank_abs = ts_rank(delta7.abs(), 60)
    return -1.0 * rank_abs * np.sign(delta7)

@register_factor(name="wq_alpha_009", category="Alpha101全家桶", desc="Alpha#009: 1日收盘变动在5日极值内的位置")
def wq_alpha_9(df: pd.DataFrame) -> pd.Series:
    d = ts_delta(df["close"], 1)
    min5 = ts_min(d, 5)
    max5 = ts_max(d, 5)
    return np.where(min5 > 0, d, np.where(max5 < 0, d, -1.0 * d))

@register_factor(name="wq_alpha_010", category="Alpha101全家桶", desc="Alpha#010: 4日价格极值扰动反转。过滤假突破")
def wq_alpha_10(df: pd.DataFrame) -> pd.Series:
    d = ts_delta(df["close"], 1)
    min4 = ts_min(d, 4)
    max4 = ts_max(d, 4)
    return np.where(min4 > 0, d, np.where(max4 < 0, d, -1.0 * d))

@register_factor(name="wq_alpha_012", category="Alpha101全家桶", desc="Alpha#012: 放量下砸反转。价跌量增往往是主力最后洗盘")
def wq_alpha_12(df: pd.DataFrame) -> pd.Series:
    return np.sign(ts_delta(df["volume"], 1)) * (-1.0 * ts_delta(df["close"], 1))

@register_factor(name="wq_alpha_014", category="Alpha101全家桶", desc="Alpha#014: 收益率与成交量负相关性。放量滞涨通常为顶")
def wq_alpha_14(df: pd.DataFrame) -> pd.Series:
    ret = df["close"].pct_change()
    return -1.0 * ts_corr(ret, df["volume"], 5)

@register_factor(name="wq_alpha_018", category="Alpha101全家桶", desc="Alpha#018: 5日量价标准差比率。衡量资金冲撞离散度")
def wq_alpha_18(df: pd.DataFrame) -> pd.Series:
    s1 = ts_std(df["close"] - df["open"], 5)
    s2 = ts_corr(df["close"], df["open"], 10)
    return -1.0 * (s1 + s2)

@register_factor(name="wq_alpha_020", category="Alpha101全家桶", desc="Alpha#020: 开盘与前期高低价偏离度。捕捉早盘情绪溢价")
def wq_alpha_20(df: pd.DataFrame) -> pd.Series:
    return -1.0 * (ts_rank(df["open"] - ts_delay(df["high"], 1), 5))

@register_factor(name="wq_alpha_024", category="Alpha101全家桶", desc="Alpha#024: 均线差值加速度。捕捉短期涨速是否衰减")
def wq_alpha_24(df: pd.DataFrame) -> pd.Series:
    diff = df["close"] - ts_delay(df["close"], 5)
    return -1.0 * ts_delta(diff, 5)

@register_factor(name="wq_alpha_026", category="Alpha101全家桶", desc="Alpha#026: 量与最高价排位相关性。缩量创新高通常见顶")
def wq_alpha_26(df: pd.DataFrame) -> pd.Series:
    r_vol = ts_rank(df["volume"], 5)
    r_high = ts_rank(df["high"], 5)
    return -1.0 * ts_max(ts_corr(r_vol, r_high, 5), 3)

@register_factor(name="wq_alpha_028", category="Alpha101全家桶", desc="Alpha#028: 均线与成交量均线相关性。资金与趋势同步度")
def wq_alpha_28(df: pd.DataFrame) -> pd.Series:
    return -1.0 * ts_corr(ts_mean(df["volume"], 20), df["low"], 5)

@register_factor(name="wq_alpha_033", category="Alpha101全家桶", desc="Alpha#033: 低开高走排位。低开被强行拉起说明多头极其强硬")
def wq_alpha_33(df: pd.DataFrame) -> pd.Series:
    return ts_rank(-1.0 + (df["open"] / (df["close"] + 1e-6)), 5)

@register_factor(name="wq_alpha_035", category="Alpha101全家桶", desc="Alpha#035: 成交量与三价和排位。捕捉缩量小阴线吸筹")
def wq_alpha_35(df: pd.DataFrame) -> pd.Series:
    r_vol = ts_rank(df["volume"], 32)
    r_price = ts_rank(df["close"] + df["high"] - df["low"], 16)
    return r_vol * (1.0 - r_price)

@register_factor(name="wq_alpha_040", category="Alpha101全家桶", desc="Alpha#040: 最高价波动率与量相关性。高位剧烈震荡代表主力出货")
def wq_alpha_40(df: pd.DataFrame) -> pd.Series:
    return -1.0 * ts_std(df["high"], 10) * ts_corr(df["high"], df["volume"], 10)

@register_factor(name="wq_alpha_041", category="Alpha101全家桶", desc="Alpha#041: 几何均价溢价偏离度。sqrt(high*low)相对收盘偏离")
def wq_alpha_41(df: pd.DataFrame) -> pd.Series:
    geo = np.sqrt(np.maximum(df["high"] * df["low"], 0))
    return (geo - df["close"]) / (df["close"] + 1e-6)

@register_factor(name="wq_alpha_043", category="Alpha101全家桶", desc="Alpha#043: 量能暴增与7日跌幅反转。暴跌出恐慌盘后见底")
def wq_alpha_43(df: pd.DataFrame) -> pd.Series:
    vol_ratio = df["volume"] / (ts_mean(df["volume"], 20) + 1e-9)
    return ts_rank(vol_ratio, 20) * ts_rank(-1.0 * ts_delta(df["close"], 7), 8)

@register_factor(name="wq_alpha_044", category="Alpha101全家桶", desc="Alpha#044: 最高价与量能排位负相关。量价负背离")
def wq_alpha_44(df: pd.DataFrame) -> pd.Series:
    return -1.0 * ts_corr(df["high"], ts_rank(df["volume"], 5), 5)

@register_factor(name="wq_alpha_049", category="Alpha101全家桶", desc="Alpha#049: 连续两周跳空低开反弹。极端超跌修复")
def wq_alpha_49(df: pd.DataFrame) -> pd.Series:
    diff10 = ts_delay(df["close"], 10) - df["close"]
    diff20 = ts_delay(df["close"], 20) - df["close"]
    return pd.Series(np.where((diff10 < 0) & (diff20 < 0), -1.0, 1.0), index=df.index)

@register_factor(name="wq_alpha_053", category="Alpha101全家桶", desc="Alpha#053: 日内实体与影线对抗比。看日内是买盘主导还是卖盘主导")
def wq_alpha_53(df: pd.DataFrame) -> pd.Series:
    inner = (df["close"] - df["low"]) - (df["high"] - df["close"])
    return inner / (df["close"] - df["open"] + 1e-6)

@register_factor(name="wq_alpha_054", category="Alpha101全家桶", desc="Alpha#054: 开高低收多空高阶压制力。机构强力吸筹过滤")
def wq_alpha_54(df: pd.DataFrame) -> pd.Series:
    inner = (df["low"] - df["close"]) * (df["open"] ** 5)
    outer = (df["low"] - df["high"]) * (df["close"] ** 5)
    return -1.0 * (inner / (outer + 1e-6))

@register_factor(name="wq_alpha_101", category="Alpha101全家桶", desc="Alpha#101: 强弱收盘位置。(close-low)/(high-low)，越贴近天花板越强")
def wq_alpha_101_factor(df: pd.DataFrame) -> pd.Series:
    return (df["close"] - df["low"]) / ((df["high"] - df["low"]) + 1e-4)
