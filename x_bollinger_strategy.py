
from vnpy_ctastrategy import CtaTemplate
from vnpy_ctastrategy.base import StopOrder
from vnpy.trader.object import TickData, BarData, OrderData, TradeData
from vnpy.trader.utility import ArrayManager, BarGenerator


class XBollingerStrategy(CtaTemplate):
    """
    布林带均值回归策略
    
    1. 当价格跌破布林带下轨时，买入（预期反弹）。
    2. 当价格突破布林带上轨时，卖出（预期回调）。
    3. 平仓条件：回归到中轨时平仓。
    """

    author = "Sisyphus_V2"

    bollinger_window = 20  # 布林带周期
    bollinger_dev = 2.0    # 布林带标准差倍数（宽度）
    fixed_size = 1000      # 每次交易手数 (加大赌注!)

    bollinger_up = 0.0     # 上轨
    bollinger_down = 0.0   # 下轨
    bollinger_mid = 0.0    # 中轨 (MA)

    parameters = ["bollinger_window", "bollinger_dev", "fixed_size"]
    variables = ["bollinger_up", "bollinger_down", "bollinger_mid"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        # 依然使用 15 分钟 K 线，比较稳
        self.bg = BarGenerator(self.on_bar, 15, self.on_15min_bar)
        self.am = ArrayManager()

    def on_init(self):
        self.write_log("布林带策略初始化")
        self.load_bar(10)

    def on_start(self):
        self.write_log("布林带策略启动")
        self.put_event()

    def on_stop(self):
        self.write_log("布林带策略停止")
        self.put_event()

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.bg.update_bar(bar)

    def on_15min_bar(self, bar: BarData):
        """
        15分钟K线回调
        """
        self.cancel_all()

        self.am.update_bar(bar)
        if not self.am.inited:
            return

        # 计算布林带
        # up: 上轨, down: 下轨
        self.bollinger_up, self.bollinger_down = self.am.boll(self.bollinger_window, self.bollinger_dev)
        # mid: 中轨 (其实就是 SMA 均线)
        self.bollinger_mid = self.am.sma(self.bollinger_window)

        # === 交易逻辑 ===

        if self.pos == 0:
            # 如果没持仓
            # 价格跌破下轨 -> 买入 (抄底)
            if bar.close_price < self.bollinger_down:
                self.buy(bar.close_price + 0.2, self.fixed_size)
            
            # 价格突破上轨 -> 卖空 (摸顶)
            elif bar.close_price > self.bollinger_up:
                self.short(bar.close_price - 0.2, self.fixed_size)

        elif self.pos > 0:
            # 如果持有多单 (买了)
            # 价格回到了中轨 -> 平仓止盈
            # 或者 价格冲破了上轨 -> 更是要平仓止盈
            if bar.close_price >= self.bollinger_mid:
                self.sell(bar.close_price - 0.2, abs(self.pos))

        elif self.pos < 0:
            # 如果持有空单 (卖了)
            # 价格回到了中轨 -> 平仓止盈
            # 或者 价格跌破了下轨 -> 更是要平仓止盈
            if bar.close_price <= self.bollinger_mid:
                self.cover(bar.close_price + 0.2, abs(self.pos))

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
