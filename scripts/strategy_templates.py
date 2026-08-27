"""策略模板库: 供 new_strategy.py 脚手架生成新策略文件。

每种模板都是完整可运行的 CtaTemplate 策略(日线直接交易)。
新增模板 = 在此加一个 dict 条目, 并在 TEMPLATES 中注册。
"""

# 生成规则:
#   骨架 = 头部(imports + class 声明) + 模板主体(params/variables/on_init/on_bar)
#        + 标准尾部(__init__ / on_tick / on_order / on_trade / on_stop_order)
#   "template" 类型给完整骨架, 逻辑留空自己填。

IMPORTS = """from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)
"""


TAIL = """
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
"""


def build_template(kind: str, date: str, name: str, author: str) -> str:
    """组装完整策略源码字符串。kind: ma/boll/rsi/momentum/template"""
    tpl = TEMPLATES[kind]
    camel = "".join(p.capitalize() for p in name.split("_"))

    header = (
        f'"""每日策略 {date}: {tpl["help"]}\n'
        f'生成工具: scripts/new_strategy.py (kind={kind})\n'
        f'"""\n\n'
        f"{IMPORTS}\n\n"
        f"class {camel}Strategy(CtaTemplate):\n"
        f'    """{tpl["doc"]}"""\n\n'
        f'    author = "{author}"\n'
        f'    created_date = "{date}"\n'
    )

    if kind == "template":
        # 完整骨架: 所有方法都给出来, 逻辑留空
        body = TEMPLATES["template"]["body"]
        return header + "\n" + body + "\n" + TAIL

    # 具体模板: 主体 + 标准尾部
    return header + "\n" + tpl["body"] + "\n" + TAIL


TEMPLATES: dict[str, dict] = {
    "ma": {
        "help": "双均线金叉死叉(趋势) - 快线上穿慢线买入, 下穿卖空",
        "doc": "双均线交叉趋势策略",
        "body": """
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
""",
    },

    "boll": {
        "help": "布林带均值回归 - 跌破下轨买入, 突破上轨卖空, 回中轨平仓",
        "doc": "布林带均值回归策略",
        "body": """
    # ========== 可调参数(回测时用 --params 覆盖) ==========
    boll_window = 20
    boll_dev = 2.0
    fixed_size = 100

    # ========== 变量(状态展示) ==========
    boll_up = 0.0
    boll_down = 0.0
    boll_mid = 0.0

    parameters = ["boll_window", "boll_dev", "fixed_size"]
    variables = ["boll_up", "boll_down", "boll_mid"]

    def on_init(self):
        self.write_log("布林带策略初始化")
        self.load_bar(200)

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.boll_up, self.boll_down = self.am.boll(
            self.boll_window, self.boll_dev
        )
        self.boll_mid = self.am.sma(self.boll_window)

        if self.pos == 0:
            if bar.close_price < self.boll_down:
                self.buy(bar.close_price * 1.01, self.fixed_size)
            elif bar.close_price > self.boll_up:
                self.short(bar.close_price * 0.99, self.fixed_size)
        elif self.pos > 0:
            if bar.close_price >= self.boll_mid:
                self.sell(bar.close_price * 0.99, abs(self.pos))
        elif self.pos < 0:
            if bar.close_price <= self.boll_mid:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()
""",
    },

    "rsi": {
        "help": "RSI 超买超卖 - 低于 buy_threshold 买入, 高于 sell_threshold 卖空",
        "doc": "RSI 均值回归策略",
        "body": """
    # ========== 可调参数(回测时用 --params 覆盖) ==========
    rsi_window = 14
    buy_threshold = 30
    sell_threshold = 70
    fixed_size = 100

    # ========== 变量(状态展示) ==========
    rsi_value = 0.0

    parameters = ["rsi_window", "buy_threshold", "sell_threshold", "fixed_size"]
    variables = ["rsi_value"]

    def on_init(self):
        self.write_log("RSI 策略初始化")
        self.load_bar(200)

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.rsi_value = self.am.rsi(self.rsi_window)

        if self.pos == 0:
            if self.rsi_value < self.buy_threshold:
                self.buy(bar.close_price * 1.01, self.fixed_size)
            elif self.rsi_value > self.sell_threshold:
                self.short(bar.close_price * 0.99, self.fixed_size)
        elif self.pos > 0:
            if self.rsi_value > self.sell_threshold:
                self.sell(bar.close_price * 0.99, abs(self.pos))
        elif self.pos < 0:
            if self.rsi_value < self.buy_threshold:
                self.cover(bar.close_price * 1.01, abs(self.pos))

        self.put_event()
""",
    },

    "momentum": {
        "help": "动量突破(唐奇安通道) - 收盘价创 N 日新高买入, 创新低卖空",
        "doc": "N 日高低点突破策略(海龟/唐奇安风格)",
        "body": """
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
""",
    },

    "template": {
        "help": "空骨架 - 只给结构, 交易逻辑自己填",
        "doc": "自定义策略(模板)",
        "body": """
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
""",
    },
}
