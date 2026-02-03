from vnpy.trader.utility import ArrayManager

class FactorLibrary:
    """
    因子军火库
    所有函数接收 am (ArrayManager), 返回 signal (int)
    Signal: 1 (做多), -1 (做空), 0 (保持/平仓)
    """

    @staticmethod
    def factor_double_ma_trend(am: ArrayManager, fast=10, slow=20) -> int:
        """双均线趋势策略"""
        fast_ma = am.sma(fast, array=True)
        slow_ma = am.sma(slow, array=True)
        
        # 金叉：快线 > 慢线
        if fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2]:
            return 1
        # 死叉：快线 < 慢线
        elif fast_ma[-1] < slow_ma[-1] and fast_ma[-2] >= slow_ma[-2]:
            return -1
        return 0

    @staticmethod
    def factor_rsi_reversal(am: ArrayManager, window=14, low=30, high=70) -> int:
        """RSI 反转策略 (超跌买入，超涨卖出)"""
        rsi = am.rsi(window, array=True)
        
        if rsi[-1] < low: # 超卖 -> 买入
            return 1
        elif rsi[-1] > high: # 超买 -> 卖出
            return -1
        return 0

    @staticmethod
    def factor_bollinger_breakout(am: ArrayManager, window=20, dev=2.0) -> int:
        """布林带突破策略"""
        up, down = am.boll(window, dev, array=True)
        close = am.close
        
        if close[-1] > up[-1]: # 突破上轨
            return 1
        elif close[-1] < down[-1]: # 跌破下轨
            return -1
        return 0

    @staticmethod
    def factor_momentum_roc(am: ArrayManager, window=10) -> int:
        """ROC 动量策略 (涨得快就追)"""
        # ROC = (当前价 - N天前价) / N天前价
        close = am.close
        if len(close) < window + 1:
            return 0
            
        roc = (close[-1] - close[-window-1]) / close[-window-1]
        
        if roc > 0.05: # 10天涨了5%以上
            return 1
        elif roc < -0.05: # 10天跌了5%以上
            return -1
        return 0

    @staticmethod
    def factor_turtle_breakout(am: ArrayManager, window=20) -> int:
        """海龟法则 (唐奇安通道突破)"""
        # 过去20天的最高价（不含今天）
        high_price = am.high[:-1].max()
        low_price = am.low[:-1].min()
        current_close = am.close[-1]
        
        if current_close > high_price: # 创20日新高
            return 1
        elif current_close < low_price: # 创20日新低
            return -1
        return 0
