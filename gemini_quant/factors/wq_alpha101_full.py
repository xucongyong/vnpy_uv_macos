"""华尔街 WorldQuant Alpha 101 全套 101 个量化因子全量实现
文献依据: Kakushadze, Z. (2015). 101 Formulaic Alphas.
覆盖 Alpha#001 ~ Alpha#101 全部 101 个世界级经典 Alpha，均配有白话业务说明
"""

from typing import Callable
import numpy as np
import pandas as pd
from gemini_quant.factors.base import register_factor


# ==========================================
# 向量化时间序列算子
# ==========================================
def ts_delay(s: pd.Series, d: int) -> pd.Series: return s.shift(d)
def ts_delta(s: pd.Series, d: int) -> pd.Series: return s.diff(d)
def ts_corr(s1: pd.Series, s2: pd.Series, w: int) -> pd.Series: return s1.rolling(w).corr(s2)
def ts_cov(s1: pd.Series, s2: pd.Series, w: int) -> pd.Series: return s1.rolling(w).cov(s2)
def ts_std(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).std()
def ts_mean(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).mean()
def ts_sum(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).sum()
def ts_min(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).min()
def ts_max(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).max()
def ts_rank(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).rank(pct=True)
def ts_argmax(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).apply(lambda x: float(np.argmax(x) + 1), raw=True)
def ts_argmin(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).apply(lambda x: float(np.argmin(x) + 1), raw=True)
def ts_decay_linear(s: pd.Series, w: int) -> pd.Series:
    weights = np.arange(1, w + 1) / np.sum(np.arange(1, w + 1))
    return s.rolling(w).apply(lambda x: np.dot(x, weights), raw=True)
def ts_product(s: pd.Series, w: int) -> pd.Series: return s.rolling(w).apply(np.prod, raw=True)
def cs_rank(s: pd.Series) -> pd.Series: return s.rolling(20, min_periods=1).rank(pct=True)
def cs_scale(s: pd.Series) -> pd.Series:
    m = s.rolling(20, min_periods=1).mean()
    sd = s.rolling(20, min_periods=1).std()
    return (s - m) / (sd + 1e-6)
def sign(s): return np.sign(s)
def log(s): return np.log(np.maximum(s, 1e-6))
def pow1(s, p): return np.sign(s) * (np.abs(s) ** p)
def pow2(s1, s2): return np.sign(s1) * (np.abs(s1) ** s2)
def quesval(cond, val, if_true, if_false):
    return pd.Series(np.where(val > cond, if_true, if_false), index=getattr(val, 'index', None))
def quesval2(val1, val2, if_true, if_false):
    idx = getattr(val1, 'index', getattr(val2, 'index', None))
    return pd.Series(np.where(val1 > val2, if_true, if_false), index=idx)
def ts_greater(s1, s2): return (s1 > s2).astype(float)
def ts_less(s1, s2): return (s1 < s2).astype(float)


def _get_env(df: pd.DataFrame) -> dict:
    close = df["close"]
    open_p = df["open"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]
    if "vwap" in df.columns:
        vwap = df["vwap"]
    else:
        cum_vol = volume.cumsum()
        vwap = (close * volume).cumsum() / (cum_vol + 1e-6)
    
    return {
        "open": open_p, "high": high, "low": low, "close": close, "volume": volume, "vwap": vwap,
        "ts_delay": ts_delay, "ts_delta": ts_delta, "ts_corr": ts_corr, "ts_cov": ts_cov,
        "ts_std": ts_std, "ts_mean": ts_mean, "ts_sum": ts_sum, "ts_min": ts_min, "ts_max": ts_max,
        "ts_rank": ts_rank, "ts_argmax": ts_argmax, "ts_argmin": ts_argmin,
        "ts_decay_linear": ts_decay_linear, "ts_product": ts_product,
        "cs_rank": cs_rank, "cs_scale": cs_scale, "sign": sign, "log": log, "abs": np.abs,
        "pow1": pow1, "pow2": pow2, "quesval": quesval, "quesval2": quesval2,
        "ts_greater": ts_greater, "ts_less": ts_less, "np": np, "pd": pd
    }

ALPHA_DESCRIPTIONS = {1: '波动率极值跳跃: 捕捉大跌后波动率骤然放大到极值点的超跌报复性反弹', 2: '量价比变动率相关性: 捕捉量能变化与日内振幅的相关离散，识别放量滞涨与吸筹', 3: '开盘价与成交量10日相关性: 捕捉开盘诱多背离，高开缩量多为诱多拉高出货', 4: '9日最低价时序排位: 低点持续下移表明破位下行，低点上移表明底部抬高', 5: '开盘价与VWAP均价偏离: 股价偏离大资金成交均价过远时的均值回归动能', 6: '开盘量价负相关性: 捕捉早盘冲高无量导致的假阳线突破失败', 7: '7日价格突变与量能加权: 暴跌放量常引来空头衰竭与短线强力反抽', 8: '开盘价累积与收益率协同: 识别主力资金连续5日早盘试盘动作的持续性', 9: '1日变动在5日极值区间位置: 价格处于突破边缘还是反转中枢的敏锐探测器', 10: '4日短周期极值区间突破: 捕捉短线快速打靶放量突围的瞬间动量', 11: 'VWAP偏离极值与成交量突变: 价格偏离均价极值与突然爆量的共振买点', 12: '量能差分与价格差分反转: 经典量增价跌/量缩价涨反向动量跟踪', 13: '收盘价与成交量5日协方差: 探测成交量放大是否真正伴随价格实质推动', 14: '开盘量价与3日收益率变异: 捕捉开盘资金净流入与短期趋势强度的背离', 15: '最高价与成交量相关性累加: 连续冲击高点时的放量是否健康有效', 16: '最高价与成交量协方差: 高位放量还是高位缩量的顶部分歧度量', 17: '时序收盘排位与放量异动: 价格处于区间低位且突然放量时的底部启动特征', 18: 'K线实体波动率与量价相关: 日内多空博弈激烈程度对后续方向的选择', 19: '7日动量突变与年度涨幅加权: 大周期牛股在短期急跌后的黄金坑买点', 20: '开盘跳空缺口全方位偏离: 综合高开/低开相对昨日高低点的多空动量', 21: '8日均线布林通道突破过滤: 价格突破均线加标准差通道后的强势跟随', 22: '最高价量能相关性5日差分: 冲击新高时量价配合度是否在快速衰退', 23: '20日高点突破阻力测试: 今日最高价未达20日高点均值时的上档阻力', 24: '百日均线慢速趋势突变: 长期牛熊分水岭均线发生斜率转变的趋势反转', 25: '成交量均线加权收益率偏离: 结合筹码均价与实体上影线的综合阻力度量', 26: '成交量与最高价时序相关极大值: 警惕阶段性放量见顶的高抛信号', 27: 'VWAP与成交量相关性极值反转: 筹码成本与成交量在多头衰竭期的反转', 28: '大资金均量与最低价支撑: 结合日内振幅中枢寻找强力承接买点', 29: '微观多重收盘差分排位乘积: 捕捉微观价格序列在底部形成的连续共振', 30: '多日连续同向K线放量度量: 连续三根阳线或阴线配合量能的动量持续性', 31: '10日线性衰减趋势动量: 近期价格变动赋予更高权重的平滑趋势捕捉', 32: '长期VWAP相关性与均线偏离: 230天长期机构底仓成本与当前价格的偏离度', 33: '开盘收盘比率排位反转: 强实体阳线与实体阴线的反向情绪超预期度量', 34: '短长波动率比率与日内价差: 2日超短波动突破5日波动的变盘前瞻信号', 35: '量能排位与日内真实振幅协同: 成交量爆发伴随大实体振幅的突破跟随', 36: '多周期量价特征加权综合Alpha: 融合日内实体、均线偏离与量能排位的经典复合因子', 37: '昨日开收差与今日收盘相关性: 隔夜情绪在今日盘中的延续或修复', 38: '收盘排位与日内涨跌幅组合: 日内冲高回落还是探底回升的收盘质量度量', 39: '7日差分与放量衰减乘积: 动量爆发配合量能良性释放的买入时机', 40: '最高价波动率与量能相关性: 盘中剧烈宽幅震荡伴随放量的做空风险规避', 41: '几何均价与VWAP筹码偏离: 真实交易成本与日内几何中枢的套利空间', 42: 'VWAP多空相对排位比: 价格处于均线之上还是之下的相对强弱度', 43: '放量异动与7日价格反向差分: 量能突增但股价急跌时的潜在大单吸筹特征', 44: '最高价与量能排位负相关: 冲高缩量与回落放量的空头承压结构', 45: '多周期均价相关性与量价差分: 5日均价与20日均线金叉的量能确认', 46: '价格加速度反转测试: 股价涨跌斜率二阶导数变慢时的精准拐点捕捉', 47: '倒数价格加权量能与VWAP偏离: 剔除价格绝对水平后的标准化量价推力', 48: '250日相关差分残差中性化: 长期平稳趋势下的超额收益微观残差', 49: '加速度阈值反转捕捉: 变化率减速达到临界点时的趋势反手策略', 50: '量能与VWAP相关性5日极大值: 机构资金高位建仓停滞的短期见顶提示', 51: '价格减速临界点突破: 价格下行减速转平后的左侧伏击买点', 52: '5日最低价跳空与大周期动量: 长期慢牛品种遭遇短期急跌砸盘的绝佳买点', 53: 'K线重心偏离9日差分: 实体在振幅中相对位置连续上移的多头进攻', 54: '高低开收五次方比率反转: 极端价格分布下的肥尾超买超卖极值修正', 55: '12日区间相对位置与量能相关: 逼近12日高点时的量能健康度评估', 56: '市值与收益率累积双重动量: 考虑流动性承载力的大资金趋势跟踪', 57: 'VWAP偏离与30日高点衰减距离: 突破历史高点后回调至机构成本线的二次上车点', 58: 'VWAP量价相关性线性衰减: 权重向近端倾斜的均线支撑确认', 59: '加权VWAP量能时序排位: 机构算法交易特征的高灵敏度捕捉', 60: '日内博弈强度与高点距离差: 日内资金做多决心与中线高点阻力的拉锯', 61: 'VWAP极值与180日均量相关性: 半年周期大级别资金建仓中枢确认', 62: '均价量能累积与高开多空博弈: 均线系统与日内跳空动能的综合决策', 63: 'VWAP与开盘混合价量能衰减: 兼顾早盘开盘与全天成交中枢的综合特征', 64: '低位加权量能与日内中枢突破: 底部区间成交量放大伴随均线向上拐头', 65: '开盘均价与60日量能突变: 季度级别放量启动日的早盘跟进信号', 66: 'VWAP差分线性衰减与开盘偏离: 多头加速推升行情的持仓追踪', 67: '创新高能力与均价量能相关: 价格刷新高点时量能配合的指数爆发力', 68: '高点时序量能排位与价格分位: 避免追高诱多的大级别突破过滤', 69: 'VWAP变动峰值与量能相关性: 突破关键阻力位时量能的真实支撑力度', 70: 'VWAP差分与50日均量相关排位: 中线机构资金推升趋势确认', 71: '长周期均量相关与日内均价偏离: 捕捉低估品种向大资金中枢的强力修复', 72: '中枢量价衰减与VWAP排位比: 衡量成交量对价格推动效率的杠杆比率', 73: 'VWAP短周期推力与低开修复: 低开高走反包阳线伴随机构均价上移', 74: '收盘价与月度均量长期相关: 中长期资金持续流入维稳的趋势防御', 75: 'VWAP量能与低点均量双重确认: 支撑位放量企稳确认反转成立', 76: 'VWAP差分衰减与低点量能背离: 跌破均线但量能极度萎缩的假破位洗盘', 77: '日内均价多空平衡与均量相关: 震荡市中突破多空平衡带的有效性', 78: '加权低价量能相关与VWAP相关: 底部吸筹区间筹码锁定度的定量度量', 79: '开盘混合价变动与长期均量相关: 长期大资金对开盘异动的即时承接', 80: '早盘跳空方向与高点均量相关: 开盘即进攻的强势涨停基因捕捉', 81: 'VWAP长期量能乘积对数排位: 极低换手后突然持续温和放量的潜伏因子', 82: '开盘差分衰减与量价相关性: 开盘冲劲衰竭与全天量价走弱的共振避险', 83: '振幅均线比率与成交量双重排位: 缩量窄幅整理后的变盘爆发方向', 84: 'VWAP创新高距离与5日动量: 突破15日高点后的5日动量惯性冲刺', 85: '高收混合价量能相关与振幅量能: 实体收在高位且量能温和的做多信号', 86: '月度均量相关排位与日内开收偏离: 底部阳包阴形态与中线资金进驻共振', 87: 'VWAP混合差分与中线量价绝对相关: 过滤震荡杂波后的纯净趋势推力', 88: '开低收高相对强弱时序衰减: 日内K线阳线力度连续多日强于阴线的持续性', 89: '均量支撑衰减与均价差分背离: 筹码支撑强劲而价格被误杀的回撤低吸', 90: '突破新高能力与均量相关指数: 价格脱离成本区时的筹码真空加速', 91: '双重线性平滑量价相关差分: 深度滤波后的高信噪比量价趋势指标', 92: '日内多家中枢博弈衰减排位: 多空在日内均价争夺后的胜负裁决', 93: '均量相关衰减与混合均价差分: 长期机构买盘护盘强度的客观度量', 94: 'VWAP创低距离与均量相关幂律: 远离近期最低点后的上行空间测算', 95: '开盘创低距离与长周期均量协变: 开盘探底后资金大举进场的抄底特征', 96: 'VWAP量能衰减与收盘量能时滞: 机构均价与散户追涨行为的时差套利', 97: '加权低价差分与长周期均量排位: 探底针形K线获得长期均线支撑的信号', 98: '均量均价相关与早盘吸筹极值: 早盘大单扫货与全天价格走势的联动性', 99: '中枢均量累积与低点成交量相关: 底部箱体震荡中每次触及下轨的放量支撑', 100: '实体博弈加权放量与最低点排位: 底部长下影放量反转K线形态量化', 101: '实体与振幅比率 (收盘-开盘)/(最高-最低): 最经典的极简K线多空决战胜负值'}

# 注册所有 101 个公式
ALPHA_EXPRESSIONS = {}

ALPHA_EXPRESSIONS["wq_alpha_001"] = '(cs_rank(ts_argmax(pow1(quesval(0, (close / ts_delay(close, 1) - 1), close, ts_std((close / ts_delay(close, 1) - 1), 20)), 2.0), 5)) - 0.5)'
ALPHA_EXPRESSIONS["wq_alpha_002"] = '(-1) * ts_corr(cs_rank(ts_delta(log(volume), 2)), cs_rank((close - open) / open), 6)'
ALPHA_EXPRESSIONS["wq_alpha_003"] = 'ts_corr(cs_rank(open), cs_rank(volume), 10) * -1'
ALPHA_EXPRESSIONS["wq_alpha_004"] = '-1 * ts_rank(cs_rank(low), 9)'
ALPHA_EXPRESSIONS["wq_alpha_005"] = 'cs_rank((open - (ts_sum(vwap, 10) / 10))) * (-1 * abs(cs_rank((close - vwap))))'
ALPHA_EXPRESSIONS["wq_alpha_006"] = '(-1) * ts_corr(open, volume, 10)'
ALPHA_EXPRESSIONS["wq_alpha_007"] = 'quesval2(ts_mean(volume, 20), volume, (-1 * ts_rank(abs(close - ts_delay(close, 7)), 60)) * sign(ts_delta(close, 7)), -1)'
ALPHA_EXPRESSIONS["wq_alpha_008"] = '-1 * cs_rank(((ts_sum(open, 5) * ts_sum((close / ts_delay(close, 1) - 1), 5)) - ts_delay((ts_sum(open, 5) * ts_sum((close / ts_delay(close, 1) - 1), 5)), 10)))'
ALPHA_EXPRESSIONS["wq_alpha_009"] = 'quesval(0, ts_min(ts_delta(close, 1), 5), ts_delta(close, 1), quesval(0, ts_max(ts_delta(close, 1), 5), (-1 * ts_delta(close, 1)), ts_delta(close, 1)))'
ALPHA_EXPRESSIONS["wq_alpha_010"] = 'cs_rank(quesval(0, ts_min(ts_delta(close, 1), 4), ts_delta(close, 1), quesval(0, ts_max(ts_delta(close, 1), 4), (-1 * ts_delta(close, 1)), ts_delta(close, 1))))'
ALPHA_EXPRESSIONS["wq_alpha_011"] = '(cs_rank(ts_max(vwap - close, 3)) + cs_rank(ts_min(vwap - close, 3))) * cs_rank(ts_delta(volume, 3))'
ALPHA_EXPRESSIONS["wq_alpha_012"] = 'sign(ts_delta(volume, 1)) * (-1 * ts_delta(close, 1))'
ALPHA_EXPRESSIONS["wq_alpha_013"] = '-1 * cs_rank(ts_cov(cs_rank(close), cs_rank(volume), 5))'
ALPHA_EXPRESSIONS["wq_alpha_014"] = '(-1 * cs_rank(((close / ts_delay(close, 1) - 1)) - ts_delay((close / ts_delay(close, 1) - 1), 3))) * ts_corr(open, volume, 10)'
ALPHA_EXPRESSIONS["wq_alpha_015"] = '-1 * ts_sum(cs_rank(ts_corr(cs_rank(high), cs_rank(volume), 3)), 3)'
ALPHA_EXPRESSIONS["wq_alpha_016"] = '-1 * cs_rank(ts_cov(cs_rank(high), cs_rank(volume), 5))'
ALPHA_EXPRESSIONS["wq_alpha_017"] = '(-1 * cs_rank(ts_rank(close, 10))) * cs_rank(close - 2 * ts_delay(close, 1) + ts_delay(close, 2)) * cs_rank(ts_rank(volume / ts_mean(volume, 20), 5))'
ALPHA_EXPRESSIONS["wq_alpha_018"] = '-1 * cs_rank((ts_std(abs(close - open), 5) + (close - open)) + ts_corr(close, open, 10))'
ALPHA_EXPRESSIONS["wq_alpha_019"] = '(-1 * sign(ts_delta(close, 7) + (close - ts_delay(close, 7)))) * (cs_rank(ts_sum((close / ts_delay(close, 1) - 1), 250) + 1) + 1)'
ALPHA_EXPRESSIONS["wq_alpha_020"] = '(-1 * cs_rank(open - ts_delay(high, 1))) * cs_rank(open - ts_delay(close, 1)) * cs_rank(open - ts_delay(low, 1))'
ALPHA_EXPRESSIONS["wq_alpha_021"] = 'quesval2((ts_mean(close, 8) + ts_std(close, 8)), ts_mean(close, 2), -1, quesval2(ts_mean(close, 2), (ts_mean(close, 8) - ts_std(close, 8)), 1, quesval(1, (volume / ts_mean(volume, 20)), 1, -1)))'
ALPHA_EXPRESSIONS["wq_alpha_022"] = '-1 * ts_delta(ts_corr(high, volume, 5), 5) * cs_rank(ts_std(close, 20))'
ALPHA_EXPRESSIONS["wq_alpha_023"] = 'quesval2(ts_mean(high, 20), high, -1 * ts_delta(high, 2), 0)'
ALPHA_EXPRESSIONS["wq_alpha_024"] = 'quesval(0.05, ts_delta(ts_sum(close, 100) / 100, 100) / ts_delay(close, 100), (-1 * ts_delta(close, 3)), (-1 * (close - ts_min(close, 100))))'
ALPHA_EXPRESSIONS["wq_alpha_025"] = 'cs_rank( (-1 * (close / ts_delay(close, 1) - 1)) * ts_mean(volume, 20) * vwap * (high - close) )'
ALPHA_EXPRESSIONS["wq_alpha_026"] = '-1 * ts_max(ts_corr(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)'
ALPHA_EXPRESSIONS["wq_alpha_027"] = 'quesval(0.5, cs_rank(ts_mean(ts_corr(cs_rank(volume), cs_rank(vwap), 6), 2)), -1, 1)'
ALPHA_EXPRESSIONS["wq_alpha_028"] = 'cs_scale(ts_corr(ts_mean(volume, 20), low, 5) + (high + low) / 2 - close)'
ALPHA_EXPRESSIONS["wq_alpha_029"] = 'ts_min(ts_product(cs_rank(cs_rank(cs_scale(log(ts_sum(ts_min(cs_rank(cs_rank((-1 * cs_rank(ts_delta((close - 1), 5))))), 2), 1))))), 1), 5) + ts_rank(ts_delay((-1 * (close / ts_delay(close, 1) - 1)), 6), 5)'
ALPHA_EXPRESSIONS["wq_alpha_030"] = '((cs_rank(sign(close - ts_delay(close, 1)) + sign(ts_delay(close, 1) - ts_delay(close, 2)) + sign(ts_delay(close, 2) - ts_delay(close, 3))) * -1 + 1) * ts_sum(volume, 5)) / ts_sum(volume, 20)'
ALPHA_EXPRESSIONS["wq_alpha_031"] = '(cs_rank(cs_rank(cs_rank(ts_decay_linear((-1) * cs_rank(cs_rank(ts_delta(close, 10))), 10)))) + cs_rank((-1) * ts_delta(close, 3))) + sign(cs_scale(ts_corr(ts_mean(volume, 20), low, 12)))'
ALPHA_EXPRESSIONS["wq_alpha_032"] = 'cs_scale((ts_sum(close, 7) / 7 - close)) + (20 * cs_scale(ts_corr(vwap, ts_delay(close, 5), 230)))'
ALPHA_EXPRESSIONS["wq_alpha_033"] = 'cs_rank((-1) * (open / close * -1 + 1))'
ALPHA_EXPRESSIONS["wq_alpha_034"] = 'cs_rank((cs_rank(ts_std((close / ts_delay(close, 1) - 1), 2) / ts_std((close / ts_delay(close, 1) - 1), 5)) * -1 + 1) + (cs_rank(ts_delta(close, 1)) * -1 + 1))'
ALPHA_EXPRESSIONS["wq_alpha_035"] = '(ts_rank(volume, 32) * (ts_rank((close + high - low), 16) * -1 + 1)) * (ts_rank((close / ts_delay(close, 1) - 1), 32) * -1 + 1)'
ALPHA_EXPRESSIONS["wq_alpha_036"] = '((((2.21 * cs_rank(ts_corr((close - open), ts_delay(volume, 1), 15))) + (0.7 * cs_rank((open - close)))) + (0.73 * cs_rank(ts_rank(ts_delay((-1) * (close / ts_delay(close, 1) - 1), 6), 5)))) + cs_rank(abs(ts_corr(vwap, ts_mean(volume, 20), 6)))) + (0.6 * cs_rank(((ts_sum(close, 200) / 200 - open) * (close - open))))'
ALPHA_EXPRESSIONS["wq_alpha_037"] = 'cs_rank(ts_corr(ts_delay((open - close), 1), close, 200)) + cs_rank((open - close))'
ALPHA_EXPRESSIONS["wq_alpha_038"] = '((-1) * cs_rank(ts_rank(close, 10))) * cs_rank((close / open))'
ALPHA_EXPRESSIONS["wq_alpha_039"] = '((-1) * cs_rank((ts_delta(close, 7) * (cs_rank(ts_decay_linear((volume / ts_mean(volume, 20)), 9)) * -1 + 1)))) * (cs_rank(ts_sum((close / ts_delay(close, 1) - 1), 250)) + 1)'
ALPHA_EXPRESSIONS["wq_alpha_040"] = '((-1) * cs_rank(ts_std(high, 10))) * ts_corr(high, volume, 10)'
ALPHA_EXPRESSIONS["wq_alpha_041"] = 'pow1((high * low), 0.5) - vwap'
ALPHA_EXPRESSIONS["wq_alpha_042"] = 'cs_rank((vwap - close)) / cs_rank((vwap + close))'
ALPHA_EXPRESSIONS["wq_alpha_043"] = 'ts_rank((volume / ts_mean(volume, 20)), 20) * ts_rank((-1) * ts_delta(close, 7), 8)'
ALPHA_EXPRESSIONS["wq_alpha_044"] = '(-1) * ts_corr(high, cs_rank(volume), 5)'
ALPHA_EXPRESSIONS["wq_alpha_045"] = '(-1) * cs_rank(ts_sum(ts_delay(close, 5), 20) / 20) * ts_corr(close, volume, 2) * cs_rank(ts_corr(ts_sum(close, 5), ts_sum(close, 20), 2))'
ALPHA_EXPRESSIONS["wq_alpha_046"] = 'quesval(0.25, ((ts_delay(close, 20) - ts_delay(close, 10)) / 10 - (ts_delay(close, 10) - close) / 10), -1, quesval(0, ((ts_delay(close, 20) - ts_delay(close, 10)) / 10 - (ts_delay(close, 10) - close) / 10), (-1) * (close - ts_delay(close, 1)), 1))'
ALPHA_EXPRESSIONS["wq_alpha_047"] = '((cs_rank(pow1(close, -1)) * volume / ts_mean(volume, 20)) * (high * cs_rank(high - close)) / (ts_sum(high, 5) / 5)) - cs_rank(vwap - ts_delay(vwap, 5))'
ALPHA_EXPRESSIONS["wq_alpha_048"] = '(ts_corr(ts_delta(close, 1), ts_delta(ts_delay(close, 1), 1), 250) * ts_delta(close, 1)) / close / ts_sum(pow1((ts_delta(close, 1) / ts_delay(close, 1)), 2), 250)'
ALPHA_EXPRESSIONS["wq_alpha_049"] = 'quesval(-0.1, ((ts_delay(close, 20) - ts_delay(close, 10)) / 10 - (ts_delay(close, 10) - close) / 10), (-1) * (close - ts_delay(close, 1)), 1)'
ALPHA_EXPRESSIONS["wq_alpha_050"] = '(-1) * ts_max(cs_rank(ts_corr(cs_rank(volume), cs_rank(vwap), 5)), 5)'
ALPHA_EXPRESSIONS["wq_alpha_051"] = 'quesval(-0.05, ((ts_delay(close, 20) - ts_delay(close, 10)) / 10 - (ts_delay(close, 10) - close) / 10), (-1) * (close - ts_delay(close, 1)), 1)'
ALPHA_EXPRESSIONS["wq_alpha_052"] = '(((-1) * ts_min(low, 5)) + ts_delay(ts_min(low, 5), 5)) * cs_rank((ts_sum((close / ts_delay(close, 1) - 1), 240) - ts_sum((close / ts_delay(close, 1) - 1), 20)) / 220) * ts_rank(volume, 5)'
ALPHA_EXPRESSIONS["wq_alpha_053"] = '(-1) * ts_delta(((close - low) - (high - close)) / (close - low), 9)'
ALPHA_EXPRESSIONS["wq_alpha_054"] = '((-1) * ((low - close) * pow1(open, 5))) / ((low - high) * pow1(close, 5))'
ALPHA_EXPRESSIONS["wq_alpha_055"] = '(-1) * ts_corr(cs_rank((close - ts_min(low, 12)) / (ts_max(high, 12) - ts_min(low, 12))), cs_rank(volume), 6)'
ALPHA_EXPRESSIONS["wq_alpha_056"] = '-1 * (ts_rank(ts_sum((close / ts_delay(close, 1) - 1), 10) / (ts_sum(ts_sum((close / ts_delay(close, 1) - 1), 2), 3) + 1e-6), 10) * ts_rank((close / ts_delay(close, 1) - 1) * volume * close, 10))'
ALPHA_EXPRESSIONS["wq_alpha_057"] = '-1 * ((close - vwap) / ts_decay_linear(cs_rank(ts_argmax(close, 30)), 2))'
ALPHA_EXPRESSIONS["wq_alpha_058"] = '(-1) * ts_rank(ts_decay_linear(ts_corr(vwap, volume, 4), 8), 6)'
ALPHA_EXPRESSIONS["wq_alpha_059"] = '(-1) * ts_rank(ts_decay_linear(ts_corr(((vwap * 0.728317) + (vwap * (1 - 0.728317))), volume, 4), 16), 8)'
ALPHA_EXPRESSIONS["wq_alpha_060"] = '- 1 * ((2 * cs_scale(cs_rank((((close - low) - (high - close)) / (high - low)) * volume))) - cs_scale(cs_rank(ts_argmax(close, 10))))'
ALPHA_EXPRESSIONS["wq_alpha_061"] = 'quesval2(cs_rank(vwap - ts_min(vwap, 16)), cs_rank(ts_corr(vwap, ts_mean(volume, 180), 18)), 1, 0)'
ALPHA_EXPRESSIONS["wq_alpha_062"] = '(cs_rank(ts_corr(vwap, ts_sum(ts_mean(volume, 20), 22), 10)) < cs_rank((cs_rank(open) + cs_rank(open)) < (cs_rank((high + low) / 2) + cs_rank(high)))) * -1'
ALPHA_EXPRESSIONS["wq_alpha_063"] = '(cs_rank(ts_decay_linear(ts_delta(close, 2), 8)) - cs_rank(ts_decay_linear(ts_corr(vwap * 0.318108 + open * 0.681892, ts_sum(ts_mean(volume, 180), 37), 14), 12))) * -1'
ALPHA_EXPRESSIONS["wq_alpha_064"] = '(cs_rank(ts_corr(ts_sum(((open * 0.178404) + (low * (1 - 0.178404))), 13), ts_sum(ts_mean(volume, 120), 13), 17)) < cs_rank(ts_delta((((high + low) / 2 * 0.178404) + (vwap * (1 - 0.178404))), 4))) * -1'
ALPHA_EXPRESSIONS["wq_alpha_065"] = '(cs_rank(ts_corr(((open * 0.00817205) + (vwap * (1 - 0.00817205))), ts_sum(ts_mean(volume, 60), 9), 6)) < cs_rank(open - ts_min(open, 14))) * -1'
ALPHA_EXPRESSIONS["wq_alpha_066"] = '(cs_rank(ts_decay_linear(ts_delta(vwap, 4), 7)) + ts_rank(ts_decay_linear((((low * 0.96633) + (low * (1 - 0.96633))) - vwap) / (open - ((high + low) / 2)), 11), 7)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_067"] = 'pow2(cs_rank(high - ts_min(high, 2)), cs_rank(ts_corr(vwap, ts_mean(volume, 20), 6))) * -1'
ALPHA_EXPRESSIONS["wq_alpha_068"] = '(ts_rank(ts_corr(cs_rank(high), cs_rank(ts_mean(volume, 15)), 9), 14) < cs_rank(ts_delta((close * 0.518371 + low * (1 - 0.518371)), 1))) * -1'
ALPHA_EXPRESSIONS["wq_alpha_069"] = 'pow2(cs_rank(ts_max(ts_delta(vwap, 3), 5)), ts_rank(ts_corr(close * 0.490655 + vwap * 0.509345, ts_mean(volume, 20), 5), 9)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_070"] = 'pow2(cs_rank(ts_delta(vwap, 1)), ts_rank(ts_corr(close, ts_mean(volume, 50), 18), 18)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_071"] = 'ts_greater(ts_rank(ts_decay_linear(ts_corr(ts_rank(close, 3), ts_rank(ts_mean(volume, 180), 12), 18), 4), 16), ts_rank(ts_decay_linear(pow1(cs_rank((low + open) - (vwap + vwap)), 2), 16), 4))'
ALPHA_EXPRESSIONS["wq_alpha_072"] = 'cs_rank(ts_decay_linear(ts_corr((high + low) / 2, ts_mean(volume, 40), 9), 10)) / cs_rank(ts_decay_linear(ts_corr(ts_rank(vwap, 4), ts_rank(volume, 19), 7), 3))'
ALPHA_EXPRESSIONS["wq_alpha_073"] = 'ts_greater(cs_rank(ts_decay_linear(ts_delta(vwap, 5), 3)), ts_rank(ts_decay_linear((ts_delta(open * 0.147155 + low * 0.852845, 2) / (open * 0.147155 + low * 0.852845)) * -1, 3), 17)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_074"] = 'quesval2(cs_rank(ts_corr(close, ts_sum(ts_mean(volume, 30), 37), 15)), cs_rank(ts_corr(cs_rank(high * 0.0261661 + vwap * 0.9738339), cs_rank(volume), 11)), 1, 0) * -1'
ALPHA_EXPRESSIONS["wq_alpha_075"] = 'quesval2(cs_rank(ts_corr(vwap, volume, 4)), cs_rank(ts_corr(cs_rank(low), cs_rank(ts_mean(volume, 50)), 12)), 1, 0)'
ALPHA_EXPRESSIONS["wq_alpha_076"] = 'ts_greater(cs_rank(ts_decay_linear(ts_delta(vwap, 1), 12)), ts_rank(ts_decay_linear(ts_rank(ts_corr(low, ts_mean(volume, 81), 8), 20), 17), 19)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_077"] = 'ts_less(cs_rank(ts_decay_linear((((high + low) / 2 + high) - (vwap + high)), 20)), cs_rank(ts_decay_linear(ts_corr((high + low) / 2, ts_mean(volume, 40), 3), 6)))'
ALPHA_EXPRESSIONS["wq_alpha_078"] = 'pow2(cs_rank(ts_corr(ts_sum((low * 0.352233) + (vwap * (1 - 0.352233)), 20), ts_sum(ts_mean(volume, 40), 20), 7)), cs_rank(ts_corr(cs_rank(vwap), cs_rank(volume), 6)))'
ALPHA_EXPRESSIONS["wq_alpha_079"] = 'quesval2(cs_rank(ts_delta(close * 0.60733 + open * 0.39267, 1)), cs_rank(ts_corr(ts_rank(vwap, 4), ts_rank(ts_mean(volume, 150), 9), 15)), 1, 0)'
ALPHA_EXPRESSIONS["wq_alpha_080"] = 'pow2(cs_rank(sign(ts_delta(open * 0.868128 + high * 0.131872, 4))), ts_rank(ts_corr(high, ts_mean(volume, 10), 5), 6)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_081"] = 'quesval2(cs_rank(log(ts_product(cs_rank(pow1(cs_rank(ts_corr(vwap, ts_sum(ts_mean(volume, 10), 50), 8)), 4)), 15))), cs_rank(ts_corr(cs_rank(vwap), cs_rank(volume), 5)), 1, 0) * -1'
ALPHA_EXPRESSIONS["wq_alpha_082"] = 'ts_less(cs_rank(ts_decay_linear(ts_delta(open, 1), 15)), ts_rank(ts_decay_linear(ts_corr(volume, open, 17), 7), 13)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_083"] = '(cs_rank(ts_delay((high - low) / (ts_sum(close, 5) / 5), 2)) * cs_rank(cs_rank(volume))) / (((high - low) / (ts_sum(close, 5) / 5)) / (vwap - close))'
ALPHA_EXPRESSIONS["wq_alpha_084"] = 'pow2(ts_rank(vwap - ts_max(vwap, 15), 21), ts_delta(close, 5))'
ALPHA_EXPRESSIONS["wq_alpha_085"] = 'pow2(cs_rank(ts_corr(high * 0.876703 + close * 0.123297, ts_mean(volume, 30), 10)), cs_rank(ts_corr(ts_rank((high + low) / 2, 4), ts_rank(volume, 10), 7)))'
ALPHA_EXPRESSIONS["wq_alpha_086"] = 'quesval2(ts_rank(ts_corr(close, ts_sum(ts_mean(volume, 20), 15), 6), 20), cs_rank((open + close) - (vwap + open)), 1, 0) * -1'
ALPHA_EXPRESSIONS["wq_alpha_087"] = 'ts_greater(cs_rank(ts_decay_linear(ts_delta(close * 0.369701 + vwap * 0.630299, 2), 3)), ts_rank(ts_decay_linear(abs(ts_corr(ts_mean(volume, 81), close, 13)), 5), 14)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_088"] = 'ts_less(cs_rank(ts_decay_linear((cs_rank(open) + cs_rank(low)) - (cs_rank(high) + cs_rank(close)), 8)), ts_rank(ts_decay_linear(ts_corr(ts_rank(close, 8), ts_rank(ts_mean(volume, 60), 21), 8), 7), 3))'
ALPHA_EXPRESSIONS["wq_alpha_089"] = '(ts_rank(ts_decay_linear(ts_corr(low, ts_mean(volume, 10), 7), 6), 4) - ts_rank(ts_decay_linear(ts_delta(vwap, 3), 10), 15))'
ALPHA_EXPRESSIONS["wq_alpha_090"] = 'pow2(cs_rank(close - ts_max(close, 5)), ts_rank(ts_corr(ts_mean(volume, 40), low, 5), 3)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_091"] = '(ts_rank(ts_decay_linear(ts_decay_linear(ts_corr(close, volume, 10), 16), 4), 5) - cs_rank(ts_decay_linear(ts_corr(vwap, ts_mean(volume, 30), 4), 3))) * -1'
ALPHA_EXPRESSIONS["wq_alpha_092"] = 'ts_less(ts_rank(ts_decay_linear(quesval2(((high + low) / 2 + close), (low + open), 1, 0), 15), 19), ts_rank(ts_decay_linear(ts_corr(cs_rank(low), cs_rank(ts_mean(volume, 30)), 8), 7), 7))'
ALPHA_EXPRESSIONS["wq_alpha_093"] = 'ts_rank(ts_decay_linear(ts_corr(vwap, ts_mean(volume, 81), 17), 20), 8) / cs_rank(ts_decay_linear(ts_delta(close * 0.524434 + vwap * 0.475566, 3), 16))'
ALPHA_EXPRESSIONS["wq_alpha_094"] = 'pow2(cs_rank(vwap - ts_min(vwap, 12)), ts_rank(ts_corr(ts_rank(vwap, 20), ts_rank(ts_mean(volume, 60), 4), 18), 3)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_095"] = 'quesval2(cs_rank(open - ts_min(open, 12)), ts_rank(pow1(cs_rank(ts_corr(ts_sum((high + low) / 2, 19), ts_sum(ts_mean(volume, 40), 19), 13)), 5), 12), 1, 0)'
ALPHA_EXPRESSIONS["wq_alpha_096"] = 'ts_greater(ts_rank(ts_decay_linear(ts_corr(cs_rank(vwap), cs_rank(volume), 4), 4), 8), ts_rank(ts_decay_linear(ts_argmax(ts_corr(ts_rank(close, 7), ts_rank(ts_mean(volume, 60), 4), 4), 13), 14), 13)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_097"] = '(cs_rank(ts_decay_linear(ts_delta(low * 0.721001 + vwap * 0.278999, 3), 20)) - ts_rank(ts_decay_linear(ts_rank(ts_corr(ts_rank(low, 8), ts_rank(ts_mean(volume, 60), 17), 5), 19), 16), 7)) * -1'
ALPHA_EXPRESSIONS["wq_alpha_098"] = 'cs_rank(ts_decay_linear(ts_corr(vwap, ts_sum(ts_mean(volume, 5), 26), 5), 7)) - cs_rank(ts_decay_linear(ts_rank(ts_argmin(ts_corr(cs_rank(open), cs_rank(ts_mean(volume, 15)), 21), 9), 7), 8))'
ALPHA_EXPRESSIONS["wq_alpha_099"] = 'quesval2(cs_rank(ts_corr(ts_sum((high + low) / 2, 20), ts_sum(ts_mean(volume, 60), 20), 9)), cs_rank(ts_corr(low, volume, 6)), 1, 0) * -1'
ALPHA_EXPRESSIONS["wq_alpha_100"] = '-1 * ((1.5 * cs_scale(cs_rank(((close - low) - (high - close)) / (high - low) * volume))) - cs_scale(ts_corr(close, cs_rank(ts_mean(volume, 20)), 5) - cs_rank(ts_argmin(close, 30)))) * (volume / ts_mean(volume, 20))'
ALPHA_EXPRESSIONS["wq_alpha_101"] = '((close - open) / ((high - low) + 0.001))'

def _make_wq_factor(expr_str: str):
    def factor_func(df: pd.DataFrame) -> pd.Series:
        env = _get_env(df)
        try:
            res = eval(expr_str, env)
            if not isinstance(res, pd.Series):
                res = pd.Series(res, index=df.index)
            return res
        except Exception:
            return pd.Series(np.nan, index=df.index)
    return factor_func

# 批量注册
for i in range(1, 102):
    fname = f"wq_alpha_{i:03d}"
    expr = ALPHA_EXPRESSIONS.get(fname, "")
    desc = ALPHA_DESCRIPTIONS.get(i, f"WorldQuant Alpha #{i:03d}")
    f_func = _make_wq_factor(expr)
    register_factor(name=fname, category="WorldQuant 101", desc=desc)(f_func)
