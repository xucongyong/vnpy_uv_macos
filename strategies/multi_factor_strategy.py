"""多因子综合评分交易策略 (Alpha Ensemble CTA Strategy)

策略逻辑:
  1. 订阅每日 K 线，累积历史数据
  2. 实时调用 gemini_quant 因子库计算核心因子 (量比异动 + RSI超跌)
  3. 进行 Z-Score 标准化并合成总分 (alpha_score)
  4. 交易决策:
     - 总分 > threshold_buy (强烈看多) 且空仓 -> 买入开多
     - 总分 < threshold_sell (转空或回落) 且持仓 -> 卖出平仓
"""

import numpy as np
import pandas as pd
from vnpy_ctastrategy import (
    CtaTemplate,
    BarData,
    ArrayManager
)


class MultiFactorAlphaStrategy(CtaTemplate):
    """基于多因子打分的 CTA 实盘与回测策略"""
    author = "Gemini"

    # 可调参数
    threshold_buy = 0.5     # 买入打分阈值
    threshold_sell = -0.2   # 平仓打分阈值
    fixed_size = 100        # 每次下单手数/股数
    history_window = 60     # 回溯窗口天数

    # 策略运行时变量 (状态监控)
    current_alpha_score = 0.0

    parameters = ["threshold_buy", "threshold_sell", "fixed_size", "history_window"]
    variables = ["current_alpha_score"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.am = ArrayManager(size=120)

    def on_init(self):
        """初始化: 预热历史K线"""
        self.write_log("多因子 Alpha 策略正在初始化，加载历史 K 线...")
        self.load_bar(100)

    def on_start(self):
        self.write_log("多因子 Alpha 策略启动！")

    def on_stop(self):
        self.write_log("多因子 Alpha 策略停止。")

    def on_bar(self, bar: BarData):
        """每来一根日线，计算因子得分并执行交易"""
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # 1. 提取近期行情数组构建简易 DataFrame
        df = pd.DataFrame({
            "open": self.am.open_array[-self.history_window:],
            "high": self.am.high_array[-self.history_window:],
            "low": self.am.low_array[-self.history_window:],
            "close": self.am.close_array[-self.history_window:],
            "volume": self.am.volume_array[-self.history_window:],
        })

        # 2. 实时计算两个实战最有效因子:
        # 因子 A: 5日量比因子 (资金放量异动)
        ma_vol_5 = df["volume"].rolling(5).mean()
        ma_vol_20 = df["volume"].rolling(20).mean()
        factor_vol = ma_vol_5 / (ma_vol_20 + 1e-9)

        # 因子 B: RSI 超跌反弹因子
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / (loss + 1e-9)))
        factor_rsi = 50.0 - rsi

        # 3. Z-Score 标准化处理
        z_vol = (factor_vol.iloc[-1] - factor_vol.mean()) / (factor_vol.std() + 1e-6)
        z_rsi = (factor_rsi.iloc[-1] - factor_rsi.mean()) / (factor_rsi.std() + 1e-6)

        # 4. 加权合成总分 (量比赋予 0.6 权重，RSI 赋予 0.4 权重)
        score = 0.6 * np.clip(z_vol, -3, 3) + 0.4 * np.clip(z_rsi, -3, 3)
        self.current_alpha_score = round(float(score), 3)

        # 5. 执行买卖交易
        # 当前空仓，且多因子综合得分强烈看多 -> 买入
        if self.pos == 0:
            if self.current_alpha_score > self.threshold_buy:
                self.buy(bar.close_price, self.fixed_size)
                self.write_log(f"[{bar.datetime.date()}] 综合因子打分={self.current_alpha_score:.2f} > {self.threshold_buy}, 开多买入 {self.fixed_size} 股")

        # 当前有多仓，且因子得分回落转空 -> 平仓避险
        elif self.pos > 0:
            if self.current_alpha_score < self.threshold_sell:
                self.sell(bar.close_price, abs(self.pos))
                self.write_log(f"[{bar.datetime.date()}] 综合因子打分={self.current_alpha_score:.2f} < {self.threshold_sell}, 平仓离场")
