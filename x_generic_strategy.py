from vnpy_ctastrategy import CtaTemplate
from vnpy.trader.object import TickData, BarData
from vnpy.trader.utility import ArrayManager, BarGenerator
from factor_library import FactorLibrary

class XGenericStrategy(CtaTemplate):
    """
    通用因子测试策略
    可以加载 FactorLibrary 中的任何因子进行测试
    """
    author = "AI_Architect"

    factor_name = "factor_double_ma_trend" # 默认因子
    fixed_size = 100
    
    # 这些参数用于传递给具体因子函数，虽然不是所有因子都用得到，但先占位
    p1 = 0.0 # 通用参数1 (比如 fast window)
    p2 = 0.0 # 通用参数2 (比如 slow window)

    parameters = ["factor_name", "fixed_size", "p1", "p2"]
    variables = []

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(100) # 默认加载足够长的数据
        
        # 动态绑定因子函数
        if hasattr(FactorLibrary, self.factor_name):
            self.factor_func = getattr(FactorLibrary, self.factor_name)
        else:
            self.write_log(f"错误: 找不到因子 {self.factor_name}")
            self.factor_func = None

    def on_init(self):
        self.load_bar(100)

    def on_start(self):
        self.write_log("通用策略启动")

    def on_stop(self):
        self.write_log("通用策略停止")

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.cancel_all()
        self.am.update_bar(bar)
        if not self.am.inited or not self.factor_func:
            return

        # === 调用因子获取信号 ===
        # 根据因子不同，动态传递参数
        # 这里为了简化，我们做一个简单的参数映射逻辑，或者直接让因子函数使用默认值
        # 进阶版应该用 **kwargs 传递 setting
        
        try:
            # 简单的尝试传递 p1, p2，如果因子不需要这些参数，可以修改 FactorLibrary 使用 **kwargs
            # 为了演示稳定性，我们先硬编码调用几个常用的，或者修改 FactorLibrary 让参数可选
            
            signal = 0
            if self.factor_name == "factor_double_ma_trend":
                f, s = int(self.p1) if self.p1 else 10, int(self.p2) if self.p2 else 20
                signal = self.factor_func(self.am, fast=f, slow=s)
            
            elif self.factor_name == "factor_rsi_reversal":
                w = int(self.p1) if self.p1 else 14
                signal = self.factor_func(self.am, window=w)
                
            elif self.factor_name == "factor_bollinger_breakout":
                w = int(self.p1) if self.p1 else 20
                signal = self.factor_func(self.am, window=w)
                
            else:
                # 其他因子使用默认参数调用
                signal = self.factor_func(self.am)
                
        except Exception as e:
            self.write_log(f"因子计算出错: {e}")
            return

        # === 执行交易 ===
        if signal == 1:
            if self.pos == 0:
                self.buy(bar.close_price * 1.01, self.fixed_size)
            elif self.pos < 0:
                self.cover(bar.close_price * 1.01, abs(self.pos))
                self.buy(bar.close_price * 1.01, self.fixed_size)
        
        elif signal == -1:
            if self.pos == 0:
                self.short(bar.close_price * 0.99, self.fixed_size)
            elif self.pos > 0:
                self.sell(bar.close_price * 0.99, abs(self.pos))
                self.short(bar.close_price * 0.99, self.fixed_size)

    def on_order(self, order):
        pass

    def on_trade(self, trade):
        pass

    def on_stop_order(self, stop_order):
        pass
