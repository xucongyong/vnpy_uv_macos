from datetime import datetime
from vnpy_portfoliostrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval
import sys
import os

# 把策略所在的文件夹加入环境
sys.path.append(os.path.join(os.path.dirname(__file__), 'strategies'))
from x_rl_portfolio_strategy import XRlPortfolioStrategy

def run_rl_backtest():
    engine = BacktestingEngine()
    
    # 假设我们用这三个有历史数据的品种进行回测，充当虚拟的加密货币资产
    # 测试高波动的微策略(MSTR)、稳健的大盘ETF(SPY) 和 苹果(AAPL)
    vt_symbols = ["MSTR.SMART", "SPY.SMART", "AAPL.SMART"]
    
    # 构建各个品种的参数字典
    rates = {s: 0.0005 for s in vt_symbols}
    slippages = {s: 0.02 for s in vt_symbols}
    sizes = {s: 1 for s in vt_symbols}
    priceticks = {s: 0.01 for s in vt_symbols}

    # 设置引擎参数
    engine.set_parameters(
        vt_symbols=vt_symbols,
        interval=Interval.DAILY,
        start=datetime(2022, 1, 1),
        end=datetime(2025, 1, 1),
        rates=rates,
        slippages=slippages,
        sizes=sizes,
        priceticks=priceticks,
        capital=10_000_000,
    )

    # 1. 添加策略：回溯长度稍微给小一点做演示（这里改为 5 方便短时间数据也可以凑足）
    engine.add_strategy(XRlPortfolioStrategy, {
        "lookback_window": 5, 
        "rebalance_interval": 1  # 每天调仓1次
    })

    print("开始加载历史数据...")
    engine.load_data()
    


    print("===================================")
    print("开始运行强化学习组合管理策略回测...")
    engine.run_backtesting()

    print("计算盈亏结果...")
    df = engine.calculate_result()
    
    if df is not None and len(df) > 0:
        print("===================================")
        print("开始计算统计指标：")
        engine.calculate_statistics()
    else:
        print("未产生平仓盈亏统计。")

if __name__ == "__main__":
    run_rl_backtest()
