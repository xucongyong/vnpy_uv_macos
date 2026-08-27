"""RSI 均值回归策略(经典 CTA 集合)

逻辑:
- RSI 低于 buy_threshold (默认30) → 超卖 → 开多/平空
- RSI 高于 sell_threshold (默认70) → 超买 → 开空/平多
- 持仓中回归到反向阈值时反向操作(先平后开)

设计为日线周期直接交易(on_bar),也可用于分钟线(自动合成)。
"""
from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class RsiStrategy(CtaTemplate):
    author = "quant-lab"

    # 参数(可优化)
    rsi_window = 14          # RSI 计算周期
    buy_threshold = 30       # 超卖阈值: RSI 低于此值买入
    sell_threshold = 70      # 超买阈值: RSI 高于此值卖出
    fixed_size = 100         # 每次下单数量

    # 变量(UI 展示)
    rsi_value = 0.0

    parameters = ["rsi_window", "buy_threshold", "sell_threshold", "fixed_size"]
    variables = ["rsi_value"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)     # Tick 合成 K 线
        self.am = ArrayManager(200)             # 指标计算器

    def on_init(self):
        self.write_log("RSI 策略初始化")
        self.load_bar(30)                       # 预热指标

    def on_start(self):
        self.write_log("RSI 策略启动")

    def on_stop(self):
        self.write_log("RSI 策略停止")

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.cancel_all()                       # 每次决策先撤掉未成交委托

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.rsi_value = self.am.rsi(self.rsi_window)

        if self.pos == 0:
            if self.rsi_value < self.buy_threshold:
                self.buy(bar.close_price * 1.01, self.fixed_size)      # 超卖开多
            elif self.rsi_value > self.sell_threshold:
                self.short(bar.close_price * 0.99, self.fixed_size)    # 超买开空

        elif self.pos > 0:
            if self.rsi_value > self.sell_threshold:
                self.sell(bar.close_price * 0.99, abs(self.pos))       # 超买平多

        elif self.pos < 0:
            if self.rsi_value < self.buy_threshold:
                self.cover(bar.close_price * 1.01, abs(self.pos))      # 超卖平空

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
