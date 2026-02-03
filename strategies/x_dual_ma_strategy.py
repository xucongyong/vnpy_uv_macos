# strategies/dual_ma_strategy.py

from vnpy_ctastrategy import CtaTemplate
from vnpy_ctastrategy.base import StopOrder
from vnpy.trader.object import TickData, BarData, OrderData, TradeData
from vnpy.trader.utility import ArrayManager, BarGenerator


class XDualMaStrategy(CtaTemplate):
    """
    双均线交叉策略

    当快线（短期均线）向上穿越慢线（长期均线）时，发出买入信号。
    当快线（短期均线）向下穿越慢线时，发出卖出信号。
    """

    author = "Sisyphus"

    fast_window = 10  # 短期均线周期
    slow_window = 30  # 长期均线周期
    fixed_size = 1  # 每次交易手数

    fast_ma0 = 0.0  # 当前快线值
    fast_ma1 = 0.0  # 上一周期快线值
    slow_ma0 = 0.0  # 当前慢线值
    slow_ma1 = 0.0  # 上一周期慢线值

    parameters = ["fast_window", "slow_window", "fixed_size"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)  # 用于将Tick数据合成K线（如果需要）
        self.am = ArrayManager()  # 用于管理历史K线数据和计算指标

    def on_init(self):
        """
        策略初始化回调。
        在加载策略后，会自动调用该方法。
        这里我们通常加载历史数据以预热指标。
        """
        self.write_log("策略初始化")
        self.load_bar(self.slow_window * 2)  # 确保加载足够历史数据以初始化ArrayManager

    def on_start(self):
        """
        策略启动回调。
        在点击启动按钮后，会自动调用该方法。
        """
        self.write_log("策略启动")
        self.put_event()  # 更新UI界面上的策略状态

    def on_stop(self):
        """
        策略停止回调。
        在点击停止按钮后，会自动调用该方法。
        """
        self.write_log("策略停止")
        self.put_event()  # 更新UI界面上的策略状态

    def on_tick(self, tick: TickData):
        """
        最新Tick数据推送回调。
        如果需要基于Tick数据进行交易，可以在这里实现。
        """
        self.bg.update_tick(tick)  # 将Tick数据推送到K线生成器

    def on_bar(self, bar: BarData):
        """
        最新K线数据推送回调。
        这是我们实现核心交易逻辑的地方。
        """
        self.write_log(f"收到K线数据: {bar.datetime}, 收盘价: {bar.close_price}")

        self.cancel_all()  # 撤销所有未完成的订单，确保每次决策都重新下单

        self.am.update_bar(bar)  # 更新ArrayManager的K线数据
        if not self.am.inited:
            # 如果ArrayManager还没有初始化完成（即历史K线数据不足），则等待
            self.write_log("ArrayManager尚未初始化，等待更多历史K线数据...")
            return

        # 记录上一周期的均线值
        self.fast_ma1 = self.fast_ma0
        self.slow_ma1 = self.slow_ma0

        # 计算当前周期的短期和长期移动平均线
        self.fast_ma0 = self.am.sma(self.fast_window, array=True)[-1]
        self.slow_ma0 = self.am.sma(self.slow_window, array=True)[-1]

        # === 交易逻辑 ===
        # 金叉：快线从下向上穿过慢线
        if self.fast_ma1 < self.slow_ma1 and self.fast_ma0 >= self.slow_ma0:
            if self.pos == 0:  # 如果当前无持仓，则开多仓
                self.buy(bar.close_price + 0.1, self.fixed_size)  # 以市价附近买入
            elif self.pos < 0:  # 如果当前持有空仓，则先平空仓，再开多仓
                self.cover(bar.close_price + 0.1, abs(self.pos))
                self.buy(bar.close_price + 0.1, self.fixed_size)
            self.write_log(f"发出买入信号，当前持仓: {self.pos}")

        # 死叉：快线从上向下穿过慢线
        elif self.fast_ma1 > self.slow_ma1 and self.fast_ma0 <= self.slow_ma0:
            if self.pos == 0:  # 如果当前无持仓，则开空仓
                self.short(bar.close_price - 0.1, self.fixed_size)  # 以市价附近卖空
            elif self.pos > 0:  # 如果当前持有多仓，则先平多仓，再开空仓
                self.sell(bar.close_price - 0.1, abs(self.pos))
                self.short(bar.close_price - 0.1, self.fixed_size)
            self.write_log(f"发出卖出信号，当前持仓: {self.pos}")

        self.put_event()  # 更新UI界面上的策略变量

    def on_order(self, order: OrderData):
        """
        订单状态更新回调。
        """
        self.write_log(f"订单更新: {order.vt_orderid}, 状态: {order.status}")
        self.put_event()

    def on_trade(self, trade: TradeData):
        """
        成交数据推送回调。
        """
        self.write_log(
            f"成交: {trade.vt_tradeid}, 价格: {trade.price}, 数量: {trade.volume}"
        )
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        停止单（如止损单）更新回调。
        """
        self.write_log(
            f"停止单更新: {stop_order.stop_orderid}, 状态: {stop_order.status}"
        )
        self.put_event()
