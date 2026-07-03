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

    fast_window = 20  # 短期均线周期
    slow_window = 60  # 长期均线周期
    rsi_window = 14   # RSI周期
    adx_window = 14   # ADX周期
    adx_threshold = 25 # ADX阈值
    fixed_size = 1000  # 每次交易手数 (加大赌注!)

    fast_ma0 = 0.0  # 当前快线值
    fast_ma1 = 0.0  # 上一周期快线值
    slow_ma0 = 0.0  # 当前慢线值
    slow_ma1 = 0.0  # 上一周期慢线值
    rsi_value = 0.0 # 当前RSI值
    adx_value = 0.0 # 当前ADX值

    parameters = ["fast_window", "slow_window", "rsi_window", "adx_window", "adx_threshold", "fixed_size"]
    variables = ["fast_ma0", "fast_ma1", "slow_ma0", "slow_ma1", "rsi_value", "adx_value"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar, 15, self.on_15min_bar)  # 生成15分钟K线
        self.am = ArrayManager()  # 用于管理历史K线数据和计算指标

    def on_init(self):
        """
        策略初始化回调。
        """
        self.write_log("策略初始化")
        self.load_bar(100)  # 加载100天的数据，确保足够计算60日均线

    def on_start(self):
        """
        策略启动回调。
        """
        self.write_log("策略启动")
        self.put_event()

    def on_stop(self):
        """
        策略停止回调。
        """
        self.write_log("策略停止")
        self.put_event()

    def on_tick(self, tick: TickData):
        """
        最新Tick数据推送回调。
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        K线数据推送回调。
        兼容日线回测和分钟线回测。
        """
        # 如果是日线回测，直接在这里跑逻辑
        # 或者我们简单点，直接把逻辑写在这里，不再用 15分钟合成
        
        self.cancel_all()

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # 计算均线
        self.fast_ma0 = self.am.sma(self.fast_window, array=True)[-1]
        self.slow_ma0 = self.am.sma(self.slow_window, array=True)[-1]
        
        # 记录上一周期
        self.fast_ma1 = self.am.sma(self.fast_window, array=True)[-2]
        self.slow_ma1 = self.am.sma(self.slow_window, array=True)[-2]

        # === 交易逻辑 (金叉死叉) ===
        if self.fast_ma1 < self.slow_ma1 and self.fast_ma0 >= self.slow_ma0:
            if self.pos == 0:
                self.buy(bar.close_price * 1.01, self.fixed_size) # 稍微追高买入
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))
                self.buy(bar.close_price * 1.01, self.fixed_size)

        elif self.fast_ma1 > self.slow_ma1 and self.fast_ma0 <= self.slow_ma0:
            if self.pos == 0:
                self.short(bar.close_price * 0.99, self.fixed_size)
            elif self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
                self.short(bar.close_price * 0.99, self.fixed_size)

        self.put_event()

    def on_15min_bar(self, bar: BarData):
        """
        原 15分钟回调，现在废弃（为了兼容日线）
        """
        pass

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
