"""微软 Qlib Alpha158 完整 158 因子全量工业实现
包含:
- 9 个 K 线多空博弈形态特征 (Candlestick Patterns)
- 4 个 价格基准比率特征 (Price Ratios: open, high, low, vwap / close)
- 29 个 跨周期时序特征 × 5个观察窗口 (5, 10, 20, 30, 60 日) = 145 个特征
共计 158 个全量因子，每个均带有详细大白话中文业务解释
"""

from typing import Callable
import numpy as np
import pandas as pd
from gemini_quant.factors.base import register_factor


def _get_vwap(df: pd.DataFrame) -> pd.Series:
    """提取或估算 VWAP 均价"""
    if "vwap" in df.columns:
        return df["vwap"]
    if "volume" in df.columns and (df["volume"] > 0).any():
        cum_vol = df["volume"].cumsum()
        cum_val = (df["close"] * df["volume"]).cumsum()
        return cum_val / (cum_vol + 1e-6)
    return (df["high"] + df["low"] + df["close"]) / 3.0


# ==============================================================================
# 1. 9 大 K线多空博弈形态 (Candlestick Patterns)
# ==============================================================================

@register_factor(name="qlib_kmid", category="Qlib形态", desc="实体强弱: (收盘-开盘)/开盘，衡量日内真实涨跌实体力度")
def qlib_kmid(df: pd.DataFrame) -> pd.Series:
    return (df["close"] - df["open"]) / (df["open"] + 1e-6)

@register_factor(name="qlib_klen", category="Qlib形态", desc="日内振幅: (最高-最低)/开盘，衡量日内总体波动空间")
def qlib_klen(df: pd.DataFrame) -> pd.Series:
    return (df["high"] - df["low"]) / (df["open"] + 1e-6)

@register_factor(name="qlib_kmid_2", category="Qlib形态", desc="实体振幅比: (收盘-开盘)/(最高-最低)，实体占整根K线波动范围的比重")
def qlib_kmid_2(df: pd.DataFrame) -> pd.Series:
    return (df["close"] - df["open"]) / (df["high"] - df["low"] + 1e-6)

@register_factor(name="qlib_kup", category="Qlib形态", desc="上影线比: (最高-max(开,收))/开盘，衡量上方抛压阻力")
def qlib_kup(df: pd.DataFrame) -> pd.Series:
    higher = np.maximum(df["open"], df["close"])
    return (df["high"] - higher) / (df["open"] + 1e-6)

@register_factor(name="qlib_kup_2", category="Qlib形态", desc="上影线振幅比: (最高-max(开,收))/(最高-最低)，上方阻力占全天波动的比重")
def qlib_kup_2(df: pd.DataFrame) -> pd.Series:
    higher = np.maximum(df["open"], df["close"])
    return (df["high"] - higher) / (df["high"] - df["low"] + 1e-6)

@register_factor(name="qlib_klow", category="Qlib形态", desc="下影线比: (min(开,收)-最低)/开盘，衡量下方多头承接力")
def qlib_klow(df: pd.DataFrame) -> pd.Series:
    lower = np.minimum(df["open"], df["close"])
    return (lower - df["low"]) / (df["open"] + 1e-6)

@register_factor(name="qlib_klow_2", category="Qlib形态", desc="下影线振幅比: (min(开,收)-最低)/(最高-最低)，探底回升支撑比重")
def qlib_klow_2(df: pd.DataFrame) -> pd.Series:
    lower = np.minimum(df["open"], df["close"])
    return (lower - df["low"]) / (df["high"] - df["low"] + 1e-6)

@register_factor(name="qlib_ksft", category="Qlib形态", desc="重心偏移: (2*收盘 - 最高 - 最低)/开盘，衡量收盘价相对全天中枢的偏离")
def qlib_ksft(df: pd.DataFrame) -> pd.Series:
    return (df["close"] * 2 - df["high"] - df["low"]) / (df["open"] + 1e-6)

@register_factor(name="qlib_ksft_2", category="Qlib形态", desc="重心相对振幅偏离: (2*收盘 - 最高 - 最低)/(最高 - 最低)，衡量多空日内最后控盘强弱")
def qlib_ksft_2(df: pd.DataFrame) -> pd.Series:
    return (df["close"] * 2 - df["high"] - df["low"]) / (df["high"] - df["low"] + 1e-6)


# ==============================================================================
# 2. 4 大价格基准比率 (Price Ratios)
# ==============================================================================

@register_factor(name="qlib_open_0", category="Qlib基准比", desc="开盘收盘比: open / close，衡量开盘价格在今日最终定价中的位置")
def qlib_open_0(df: pd.DataFrame) -> pd.Series:
    return df["open"] / (df["close"] + 1e-6)

@register_factor(name="qlib_high_0", category="Qlib基准比", desc="最高收盘比: high / close，衡量收盘价离全天最高价的折价幅度")
def qlib_high_0(df: pd.DataFrame) -> pd.Series:
    return df["high"] / (df["close"] + 1e-6)

@register_factor(name="qlib_low_0", category="Qlib基准比", desc="最低收盘比: low / close，衡量收盘价离全天最低价的溢价幅度")
def qlib_low_0(df: pd.DataFrame) -> pd.Series:
    return df["low"] / (df["close"] + 1e-6)

@register_factor(name="qlib_vwap_0", category="Qlib基准比", desc="成交均价收盘比: vwap / close，衡量大资金筹码成本相对收盘价偏离")
def qlib_vwap_0(df: pd.DataFrame) -> pd.Series:
    vwap = _get_vwap(df)
    return vwap / (df["close"] + 1e-6)


# ==============================================================================
# 3. 29 个跨周期时序特征 × 5个窗口 (5, 10, 20, 30, 60) = 145 个特征
# ==============================================================================

WINDOWS = [5, 10, 20, 30, 60]

def _calc_rolling_slope_r2_resi(s: pd.Series, w: int):
    """高效向量化计算 w 天线性回归的斜率、R方和残差"""
    x = np.arange(w)
    x_bar = (w - 1) / 2.0
    sum_sq_x = np.sum((x - x_bar) ** 2)
    weights = (x - x_bar) / sum_sq_x

    slope = s.rolling(w).apply(lambda y: np.dot(weights, y), raw=True)
    mean_y = s.rolling(w).mean()
    resi = s - (mean_y + slope * x_bar)

    var_x = np.var(x, ddof=1)
    var_y = s.rolling(w).var()
    cov_xy = slope * sum_sq_x / (w - 1)
    rsqr = (cov_xy ** 2) / (var_x * var_y + 1e-12)
    return slope, rsqr, resi


# 动态批量注册函数工厂
def _make_roc_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["close"].shift(w) / (df["close"] + 1e-6)
    return factor

def _make_ma_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["close"].rolling(w).mean() / (df["close"] + 1e-6)
    return factor

def _make_std_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["close"].rolling(w).std() / (df["close"] + 1e-6)
    return factor

def _make_beta_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        slope, _, _ = _calc_rolling_slope_r2_resi(df["close"], w)
        return slope / (df["close"] + 1e-6)
    return factor

def _make_rsqr_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        _, rsqr, _ = _calc_rolling_slope_r2_resi(df["close"], w)
        return rsqr
    return factor

def _make_resi_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        _, _, resi = _calc_rolling_slope_r2_resi(df["close"], w)
        return resi / (df["close"] + 1e-6)
    return factor

def _make_max_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["high"].rolling(w).max() / (df["close"] + 1e-6)
    return factor

def _make_min_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["low"].rolling(w).min() / (df["close"] + 1e-6)
    return factor

def _make_qtlu_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["close"].rolling(w).quantile(0.8) / (df["close"] + 1e-6)
    return factor

def _make_qtld_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["close"].rolling(w).quantile(0.2) / (df["close"] + 1e-6)
    return factor

def _make_rank_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["close"].rolling(w).rank(pct=True)
    return factor

def _make_rsv_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        min_p = df["low"].rolling(w).min()
        max_p = df["high"].rolling(w).max()
        return (df["close"] - min_p) / (max_p - min_p + 1e-6)
    return factor

def _make_imax_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["high"].rolling(w).apply(lambda y: np.argmax(y) / w, raw=True)
    return factor

def _make_imin_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["low"].rolling(w).apply(lambda y: np.argmin(y) / w, raw=True)
    return factor

def _make_imxd_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        imax = df["high"].rolling(w).apply(lambda y: np.argmax(y) / w, raw=True)
        imin = df["low"].rolling(w).apply(lambda y: np.argmin(y) / w, raw=True)
        return imax - imin
    return factor

def _make_corr_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        vol_log = np.log(df["volume"] + 1)
        return df["close"].rolling(w).corr(vol_log)
    return factor

def _make_cord_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        ret = df["close"] / (df["close"].shift(1) + 1e-6)
        vol_chg = np.log(df["volume"] / (df["volume"].shift(1) + 1e-6) + 1)
        return ret.rolling(w).corr(vol_chg)
    return factor

def _make_cntp_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return (df["close"] > df["close"].shift(1)).astype(float).rolling(w).mean()
    return factor

def _make_cntn_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return (df["close"] < df["close"].shift(1)).astype(float).rolling(w).mean()
    return factor

def _make_cntd_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        cntp = (df["close"] > df["close"].shift(1)).astype(float).rolling(w).mean()
        cntn = (df["close"] < df["close"].shift(1)).astype(float).rolling(w).mean()
        return cntp - cntn
    return factor

def _make_sump_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        diff = df["close"] - df["close"].shift(1)
        pos = np.maximum(diff, 0)
        return pos.rolling(w).sum() / (diff.abs().rolling(w).sum() + 1e-6)
    return factor

def _make_sumn_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        diff = df["close"] - df["close"].shift(1)
        neg = np.maximum(-diff, 0)
        return neg.rolling(w).sum() / (diff.abs().rolling(w).sum() + 1e-6)
    return factor

def _make_sumd_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        diff = df["close"] - df["close"].shift(1)
        pos = np.maximum(diff, 0)
        neg = np.maximum(-diff, 0)
        total = diff.abs().rolling(w).sum() + 1e-6
        return (pos.rolling(w).sum() - neg.rolling(w).sum()) / total
    return factor

def _make_vma_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["volume"].rolling(w).mean() / (df["volume"] + 1e-6)
    return factor

def _make_vstd_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        return df["volume"].rolling(w).std() / (df["volume"] + 1e-6)
    return factor

def _make_wvma_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        abs_ret = (df["close"] / (df["close"].shift(1) + 1e-6) - 1).abs()
        wv = abs_ret * df["volume"]
        return wv.rolling(w).std() / (wv.rolling(w).mean() + 1e-6)
    return factor

def _make_vsump_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        vdiff = df["volume"] - df["volume"].shift(1)
        pos = np.maximum(vdiff, 0)
        return pos.rolling(w).sum() / (vdiff.abs().rolling(w).sum() + 1e-6)
    return factor

def _make_vsumn_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        vdiff = df["volume"] - df["volume"].shift(1)
        neg = np.maximum(-vdiff, 0)
        return neg.rolling(w).sum() / (vdiff.abs().rolling(w).sum() + 1e-6)
    return factor

def _make_vsumd_factor(w: int):
    def factor(df: pd.DataFrame) -> pd.Series:
        vdiff = df["volume"] - df["volume"].shift(1)
        pos = np.maximum(vdiff, 0)
        neg = np.maximum(-vdiff, 0)
        total = vdiff.abs().rolling(w).sum() + 1e-6
        return (pos.rolling(w).sum() - neg.rolling(w).sum()) / total
    return factor


# 批量注册 29 种特征 × 5 个周期 = 145 个因子
FEATURE_META = [
    ("roc", "Qlib动量", "{w}日变动率: {w}天前收盘价相对当前收盘价变动", _make_roc_factor),
    ("ma", "Qlib趋势", "{w}日均线偏离: {w}日收盘均价与今日收盘价比值", _make_ma_factor),
    ("std", "Qlib波动", "{w}日波动率: {w}日收盘价波动标准差比值", _make_std_factor),
    ("beta", "Qlib趋势斜率", "{w}日时序趋势斜率: 回归斜率反映短期上涨或下跌速度", _make_beta_factor),
    ("rsqr", "Qlib趋势确定度", "{w}日回归确定系数(R方): 趋势规律越强R方越接近1", _make_rsqr_factor),
    ("resi", "Qlib残差偏离", "{w}日回归残差比: 当前价格相对线性回归中枢的偏离", _make_resi_factor),
    ("max", "Qlib阻力位", "{w}日最高价突破度: {w}日内最高价/今日收盘价", _make_max_factor),
    ("min", "Qlib支撑位", "{w}日最低价支撑度: {w}日内最低价/今日收盘价", _make_min_factor),
    ("qtlu", "Qlib分位", "{w}日80%高分位偏离: 衡量股价是否处于顶部活跃区间", _make_qtlu_factor),
    ("qtld", "Qlib分位", "{w}日20%低分位偏离: 衡量股价是否处于底部超跌区间", _make_qtld_factor),
    ("rank", "Qlib时序排位", "{w}日收盘时序分位: 今日价格在过去{w}天里的百分比位置", _make_rank_factor),
    ("rsv", "Qlib相对强弱", "{w}日RSV极值比: 经典KD指标RSV未成熟随机值", _make_rsv_factor),
    ("imax", "Qlib极值时点", "{w}日最高价出现时点: 最高价越近表明多头正猛", _make_imax_factor),
    ("imin", "Qlib极值时点", "{w}日最低价出现时点: 最低价越近表明空头正猛", _make_imin_factor),
    ("imxd", "Qlib顶底时差", "{w}日最高点与最低点出现时差: 衡量多空交锋节奏", _make_imxd_factor),
    ("corr", "Qlib量价相关", "{w}日收盘价与对数成交量相关系数: 经典量价同步度", _make_corr_factor),
    ("cord", "Qlib量价变动", "{w}日收益率与成交量变动率相关系数: 价格暴涨是否放量", _make_cord_factor),
    ("cntp", "Qlib涨跌天数", "{w}日上涨天数占比: 过去{w}天里收红盘的概率", _make_cntp_factor),
    ("cntn", "Qlib涨跌天数", "{w}日下跌天数占比: 过去{w}天里收绿盘的概率", _make_cntn_factor),
    ("cntd", "Qlib涨跌净差", "{w}日多空红绿天数净胜率: 多头持续性指示器", _make_cntd_factor),
    ("sump", "Qlib多空动能", "{w}日阳线涨幅占总波幅比例: 类似于RSI的多头动量", _make_sump_factor),
    ("sumn", "Qlib多空动能", "{w}日阴线跌幅占总波幅比例: 类似于RSI的空头动量", _make_sumn_factor),
    ("sumd", "Qlib多空净差", "{w}日多空实体波幅净强弱: 真实资金控盘推力", _make_sumd_factor),
    ("vma", "Qlib成交量", "{w}日成交量均线比: 过去均量与今日成交量比值(量比反转)", _make_vma_factor),
    ("vstd", "Qlib量能变异", "{w}日成交量波动离散度: 资金进出异动频率", _make_vstd_factor),
    ("wvma", "Qlib量价加权波动", "{w}日价格波幅加权成交量的变异系数: 衡量异动大单冲击", _make_wvma_factor),
    ("vsump", "Qlib量能流向", "{w}日放量天成交量占比: 资金是否在放量吸筹", _make_vsump_factor),
    ("vsumn", "Qlib量能流向", "{w}日缩量天成交量占比: 市场是否在缩量阴跌", _make_vsumn_factor),
    ("vsumd", "Qlib净量放大", "{w}日放量与缩量净强弱差: 资金净流入强度", _make_vsumd_factor),
]

for base_name, category, desc_tmpl, maker in FEATURE_META:
    for w in WINDOWS:
        fname = f"qlib_{base_name}_{w}"
        fdesc = desc_tmpl.format(w=w)
        func = maker(w)
        register_factor(name=fname, category=category, desc=fdesc)(func)
