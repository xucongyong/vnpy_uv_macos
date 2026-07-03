
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    ArrayManager,
)

class BtcProStrategy(CtaTemplate):
    """
    BTC 稳健趋势策略 (修正初始化版)
    """
    author = "Gemini Quant"

    breakout_window = 48       
    ma_window = 200            
    atr_window = 30            
    atr_multiplier = 3.0       
    fixed_size = 1             

    atr_value = 0.0
    ma_value = 0.0
    entry_high = 0.0
    entry_low = 0.0
    intra_high = 0.0
    intra_low = 0.0

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.am = ArrayManager(250) # 增大内部缓存

    def on_init(self):
        self.write_log("稳健策略初始化...")
        self.load_bar(15) # 回测时引擎会提供数据，这里 load_bar(15) 是指加载 15 天的数据
        # 在 vnpy 中，load_bar 的参数通常是天数。15天 * 24小时 = 360个Bar，足够初始化 MA200

    def on_start(self):
        self.write_log("稳健策略启动！")

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        
        # 这里的判断非常关键！
        if not self.am.inited:
            return

        # 计算指标
        self.ma_value = self.am.sma(self.ma_window)
        self.atr_value = self.am.atr(self.atr_window)
        
        # 获取切片计算高低点
        self.entry_high = self.am.high[-self.breakout_window-1:-1].max()
        self.entry_low = self.am.low[-self.breakout_window-1:-1].min()

        if self.pos == 0:
            if bar.close_price > self.entry_high and bar.close_price > self.ma_value:
                self.buy(bar.close_price + 20, self.fixed_size)
                self.intra_high = bar.close_price

            elif bar.close_price < self.entry_low and bar.close_price < self.ma_value:
                self.short(bar.close_price - 20, self.fixed_size)
                self.intra_low = bar.close_price

        elif self.pos > 0:
            self.intra_high = max(self.intra_high, bar.high_price)
            stop_loss = self.intra_high - self.atr_multiplier * self.atr_value
            if bar.close_price < stop_loss:
                self.sell(bar.close_price - 20, abs(self.pos))

        elif self.pos < 0:
            self.intra_low = min(self.intra_low, bar.low_price)
            stop_loss = self.intra_low + self.atr_multiplier * self.atr_value
            if bar.close_price > stop_loss:
                self.cover(bar.close_price + 20, abs(self.pos))

        self.put_event()
