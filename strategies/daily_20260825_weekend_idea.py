"""每日策略 2026-08-25: 空骨架 - 只给结构, 交易逻辑自己填
生成工具: scripts/new_strategy.py (kind=template)
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


class WeekendIdeaStrategy(CtaTemplate):
    """自定义策略(模板)"""

    author = "quant-daily"
    created_date = "2026-08-25"


    # ========== 可调参数(回测时用 --params 覆盖) ==========
    fixed_size = 100

    # ========== 变量(状态展示) ==========

    parameters = ["fixed_size"]
    variables = []

    def on_init(self):
        self.write_log("策略初始化")
        self.load_bar(200)

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # ===== 在这里写你的交易逻辑 =====
        # 指标: self.am.sma(n) / self.am.boll(n,d) / self.am.rsi(n) ...
        # 下单: self.buy(price, vol) / self.sell / self.short / self.cover
        # 持仓: self.pos > 0 多单, < 0 空单

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
