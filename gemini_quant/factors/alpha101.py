
import pandas as pd
import numpy as np

class Alpha101:
    """
    WorldQuant Alpha 101 因子库 (标准量化版)
    """

    @staticmethod
    def factor_alpha001(df):
        """
        Alpha#1: rank(Ts_ArgMax(SignedPower((returns < 0 ? stddev(returns, 20) : close), 2.), 5))
        通俗理解: 捕捉价格突然剧烈波动的信号
        """
        returns = df['Close'].pct_change()
        # 简化版实现: 5日波动率的变动
        return returns.rolling(20).std().rolling(5).apply(lambda x: x.argmax() if len(x)>0 else 0)

    @staticmethod
    def factor_alpha006(df):
        """
        Alpha#6: -1 * corr(open, volume, 10)
        通俗理解: 量价背离。如果开盘价涨但成交量跌，通常是假突破。
        """
        return -1 * df['Open'].rolling(10).corr(df['Volume'])

    @staticmethod
    def factor_alpha101(df):
        """
        Alpha#101: (close - low) / ((high - low) + 0.001)
        通俗理解: 强弱位置。看收盘价是在全天波动的顶部还是底部。
        """
        return (df['Close'] - df['Low']) / ((df['High'] - df['Low']) + 0.001)

    @staticmethod
    def factor_momentum_5d(df):
        """5日动量因子"""
        return df['Close'].pct_change(5)

    @staticmethod
    def factor_volatility_10d(df):
        """10日波动率因子"""
        return df['Close'].pct_change().rolling(10).std()
