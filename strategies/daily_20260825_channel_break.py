"""每日策略 2026-08-25: 动量突破(唐奇安通道) - 收盘价创 N 日新高买入, 创新低卖空
生成工具: scripts/new_strategy.py (kind=momentum)
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


class ChannelBreakStrategy(CtaTemplate):
    """N 日高低点突破策略(海龟/唐奇安风格)"""

    author = "quant-daily"
    created_date = "2026-08-25"


    # ========== 可调参数(回测时用 --params 覆盖) ==========
    entry_window = 20
    exit_window = 10
    fixed_size = 100

    # ========== 变量(状态展示) ==========
    entry_high = 0.0
    entry_low = 0.0

    parameters = ["entry_window", "exit_window", "fixed_size"]
    variables = ["entry_high", "entry_low"]

    def on_init(self):
        self.write_log("动量突破策略初始化")
        self.load_bar(200)

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # 唐奇安通道: 过去 N 根K线的高低点(不含当前)
        entry_high = max(self.am.high[:-1][-self.entry_window:])
        entry_low = min(self.am.low[:-1][-self.entry_window:])
        exit_high = max(self.am.high[:-1][-self.exit_window:])
        exit_low = min(self.am.low[:-1][-self.exit_window:])
        self.entry_high = entry_high
        self.entry_low = entry_low

        if self.pos == 0:
            if bar.close_price > entry_high:
                self.buy(bar.close_price * 1.01, self.fixed_size)
            elif bar.close_price < entry_low:
                self.short(bar.close_price * 0.99, self.fixed_size)
        elif self.pos > 0:
            if bar.close_price < exit_low:
                self.sell(bar.close_price * 0.99, abs(self.pos))
        elif self.pos < 0:
            if bar.close_price > exit_high:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()


    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

    def on_start(self):
        self.write_log("策略启动")

    def on_stop(self):
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
