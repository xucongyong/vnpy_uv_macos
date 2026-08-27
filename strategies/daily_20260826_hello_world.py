"""每日策略 2026-08-26: 双均线金叉死叉(趋势) - 快线上穿慢线买入, 下穿卖空
生成工具: scripts/new_strategy.py (kind=ma)
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


class HelloWorldStrategy(CtaTemplate):
    """双均线交叉趋势策略"""

    author = "quant-daily"
    created_date = "2026-08-26"


    # ========== 可调参数(回测时用 --params 覆盖) ==========
    fast_window = 20
    slow_window = 60
    fixed_size = 100

    # ========== 变量(状态展示) ==========
    fast_ma = 0.0
    slow_ma = 0.0

    parameters = ["fast_window", "slow_window", "fixed_size"]
    variables = ["fast_ma", "slow_ma"]

    def on_init(self):
        self.write_log("双均线策略初始化")
        self.load_bar(200)

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        fast_ma0 = self.am.sma(self.fast_window, array=True)[-1]
        slow_ma0 = self.am.sma(self.slow_window, array=True)[-1]
        fast_ma1 = self.am.sma(self.fast_window, array=True)[-2]
        slow_ma1 = self.am.sma(self.slow_window, array=True)[-2]
        self.fast_ma = fast_ma0
        self.slow_ma = slow_ma0

        if fast_ma1 <= slow_ma1 and fast_ma0 > slow_ma0:      # 金叉
            if self.pos == 0:
                self.buy(bar.close_price * 1.01, self.fixed_size)
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))
                self.buy(bar.close_price * 1.01, self.fixed_size)
        elif fast_ma1 >= slow_ma1 and fast_ma0 < slow_ma0:    # 死叉
            if self.pos == 0:
                self.short(bar.close_price * 0.99, self.fixed_size)
            elif self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
                self.short(bar.close_price * 0.99, self.fixed_size)

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
