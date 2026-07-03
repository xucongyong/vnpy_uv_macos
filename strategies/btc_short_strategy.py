
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    ArrayManager,
)

class BtcTrendStrategy(CtaTemplate):
    """
    BTC 多空趋势对开策略 (全能版)
    1. 趋势过滤：MA60 均线确定大方向。
    2. 双向破位：突破 24h 高点做多，跌破 24h 低点做空。
    3. 动态追踪：使用 ATR 追踪止损，让利润奔跑。
    """
    author = "Gemini Quant"

    breakout_window = 24      # 24小时破位线
    ma_window = 60            # 60小时大趋势过滤
    atr_window = 20           # ATR 波动率窗口
    atr_multiplier = 2.5      # ATR 追踪止损倍数
    fixed_size = 1            # 每次开仓 1 个 BTC

    atr_value = 0.0
    ma_value = 0.0
    entry_high = 0.0
    entry_low = 0.0
    intra_high = 0.0          # 多头持仓期间最高价
    intra_low = 0.0           # 空头持仓期间最低价

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.am = ArrayManager()

    def on_init(self):
        self.write_log("全能版策略初始化中...")
        self.load_bar(10)

    def on_start(self):
        self.write_log("全能版策略已启动！多空双向捕捉开启。")

    def on_stop(self):
        self.write_log("策略停止。")

    def on_bar(self, bar: BarData):
        self.cancel_all()

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # 1. 计算指标
        self.ma_value = self.am.sma(self.ma_window)
        self.atr_value = self.am.atr(self.atr_window)
        self.entry_high = self.am.high[-self.breakout_window-1:-1].max()
        self.entry_low = self.am.low[-self.breakout_window-1:-1].min()

        # 2. 交易逻辑
        if self.pos == 0:
            # 【做多信号】：价格 > 天花板 且 价格 > 大均线
            if bar.close_price > self.entry_high and bar.close_price > self.ma_value:
                self.buy(bar.close_price + 10, self.fixed_size)
                self.intra_high = bar.close_price
                self.write_log(f"🚀 做多触发！价格: {bar.close_price}, 天花板: {self.entry_high}")

            # 【做空信号】：价格 < 地板线 且 价格 < 大均线
            elif bar.close_price < self.entry_low and bar.close_price < self.ma_value:
                self.short(bar.close_price - 10, self.fixed_size)
                self.intra_low = bar.close_price
                self.write_log(f"📉 做空触发！价格: {bar.close_price}, 地板线: {self.entry_low}")

        # 3. 持仓平仓逻辑
        elif self.pos > 0:
            # 多头追踪止损
            self.intra_high = max(self.intra_high, bar.high_price)
            stop_loss = self.intra_high - self.atr_multiplier * self.atr_value
            
            if bar.close_price < stop_loss or bar.close_price < self.am.sma(20):
                self.sell(bar.close_price - 10, abs(self.pos))
                self.write_log(f"🚩 多头止损/止盈平仓！价格: {bar.close_price}")

        elif self.pos < 0:
            # 空头追踪止损
            self.intra_low = min(self.intra_low, bar.low_price)
            stop_loss = self.intra_low + self.atr_multiplier * self.atr_value
            
            if bar.close_price > stop_loss or bar.close_price > self.am.sma(20):
                self.cover(bar.close_price + 10, abs(self.pos))
                self.write_log(f"🚩 空头止损/止盈平仓！价格: {bar.close_price}")

        self.put_event()
