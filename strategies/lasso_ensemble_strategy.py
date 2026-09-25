"""基于 LASSO 正交降维提炼的 5 大兵种多因子决策策略 (LassoEnsembleStrategy)

策略逻辑:
1. 订阅每日 K 线，滑动回溯 60 天行情
2. 实时计算 LASSO 提炼出的 5 大正交核心因子 (动量 / 超跌 / 资金 / 博弈 / 避险)
3. 对 5 大因子做 Winsorized Z-Score 标准化，并按历史 IC 符号动态合成总分 (0.0 ~ 1.0)
4. 纪律化交易与风控:
   - 买入开多: 综合置信度 > threshold_buy (默认 0.60) 且当前空仓
   - 动能衰竭止盈: 综合置信度 < threshold_sell (默认 0.40) 且持有仓位
   - 追踪硬止损: 买入后若自最高价回撤超 trailing_stop_pct (默认 6%)，强制平仓出场保命
"""

import numpy as np
import pandas as pd
from vnpy_ctastrategy import (
    CtaTemplate,
    BarData,
    ArrayManager
)
from gemini_quant.factors.base import get_all_factors


class LassoEnsembleStrategy(CtaTemplate):
    """LASSO 5大正交兵种多因子实战策略"""
    author = "Gemini"

    # 可调参数
    threshold_buy = 0.58       # 开多买入置信度阈值
    threshold_sell = 0.42      # 多头衰竭平仓阈值
    trailing_stop_pct = 0.06   # 6% 移动追踪止损线
    fixed_size = 100           # 每次下单手数/股数
    history_window = 60        # 回溯窗口

    # 运行时监控变量
    current_alpha_score = 0.5
    highest_price = 0.0
    entry_price = 0.0

    parameters = ["threshold_buy", "threshold_sell", "trailing_stop_pct", "fixed_size", "history_window"]
    variables = ["current_alpha_score", "highest_price", "entry_price"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.am = ArrayManager(size=120)
        self.factors_registry = get_all_factors()
        
        # 5 大正交核心兵种配置 (因子名与 IC 方向符号)
        # 涵盖: WorldQuant反转、动量、微软波幅加权大单、形态、佳庆波动率
        self.active_factor_configs = [
            {"name": "wq_alpha_094", "weight_sign": -1.0, "role": "超跌抄底兵"},
            {"name": "wq_alpha_019", "weight_sign": 1.0, "role": "动量前锋兵"},
            {"name": "qlib_wvma_5",  "weight_sign": 1.0, "role": "主力资金兵"},
            {"name": "qlib_kmid",    "weight_sign": 1.0, "role": "日内博弈兵"},
            {"name": "chaikin_vol",  "weight_sign": -1.0, "role": "波动防暴兵"}
        ]

    def on_init(self):
        self.write_log("多因子 LASSO 5大正交策略初始化中，预热加载历史 K 线...")
        self.load_bar(100)

    def on_start(self):
        self.write_log("多因子 LASSO 策略正式启动运行！")

    def on_stop(self):
        self.write_log("多因子 LASSO 策略停止。")

    def on_bar(self, bar: BarData):
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # 1. 提取近期价格构建分析矩阵
        df = pd.DataFrame({
            "open": self.am.open_array[-self.history_window:],
            "high": self.am.high_array[-self.history_window:],
            "low": self.am.low_array[-self.history_window:],
            "close": self.am.close_array[-self.history_window:],
            "volume": self.am.volume_array[-self.history_window:]
        })
        cum_vol = df["volume"].cumsum()
        df["vwap"] = (df["close"] * df["volume"]).cumsum() / (cum_vol + 1e-6)

        # 2. 依次计算 5 大正交兵种得分
        sub_scores = []
        for cfg in self.active_factor_configs:
            fname = cfg["name"]
            sign = cfg["weight_sign"]
            if fname in self.factors_registry:
                try:
                    raw_s = self.factors_registry[fname]["func"](df)
                    val = float(raw_s.iloc[-1])
                    if np.isnan(val) or np.isinf(val):
                        val = 0.0
                    
                    # 滚动标准化
                    hist_mean = float(raw_s.mean())
                    hist_std = float(raw_s.std()) + 1e-6
                    z = (val - hist_mean) / hist_std
                    z = np.clip(z, -3.0, 3.0)
                    
                    # 经由 IC 方向矫正的分数，用 Sigmoid 映射到 0~1
                    directional_z = z * sign
                    score_01 = 1.0 / (1.0 + np.exp(-directional_z))
                    sub_scores.append(score_01)
                except Exception:
                    sub_scores.append(0.5)
            else:
                sub_scores.append(0.5)

        # 3. 计算 5 兵种等权综合置信度得分 (0.0 ~ 1.0)
        self.current_alpha_score = float(np.mean(sub_scores)) if sub_scores else 0.5

        # 4. 执行交易决策与硬风控
        if self.pos == 0:
            # 空仓时: 综合看多置信度触发买入线
            if self.current_alpha_score >= self.threshold_buy:
                self.buy(bar.close_price, self.fixed_size)
                self.entry_price = bar.close_price
                self.highest_price = bar.close_price
                self.write_log(f"🟢 [买入信号] 5大兵种共振看多！综合得分: {self.current_alpha_score:.3f} >= {self.threshold_buy}，价格: {bar.close_price}")
        
        elif self.pos > 0:
            # 持仓中: 刷新入场后最高价
            self.highest_price = max(self.highest_price, bar.close_price)
            drawdown_from_peak = (self.highest_price - bar.close_price) / self.highest_price

            # ① 追踪硬止损优先保护: 自最高点回撤超标，坚决平仓保命
            if drawdown_from_peak >= self.trailing_stop_pct:
                self.sell(bar.close_price, abs(self.pos))
                self.write_log(f"🚨 [硬止损触发] 自最高价 {self.highest_price:.2f} 回撤 {drawdown_from_peak*100:.2f}% >= {self.trailing_stop_pct*100}%，强制清仓止损，价格: {bar.close_price}")
                self.highest_price = 0.0
                self.entry_price = 0.0

            # ② 多头动能衰竭正常止盈/离场
            elif self.current_alpha_score <= self.threshold_sell:
                self.sell(bar.close_price, abs(self.pos))
                self.write_log(f"🔴 [平仓离场] 多头动能减退，综合得分: {self.current_alpha_score:.3f} <= {self.threshold_sell}，平仓锁定盈亏，价格: {bar.close_price}")
                self.highest_price = 0.0
                self.entry_price = 0.0

        self.put_event()
