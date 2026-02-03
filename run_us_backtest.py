
from datetime import datetime
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval, Exchange

from x_dual_ma_strategy import XDualMaStrategy

def run_us():
    # 1. 也是这几只全明星
    TARGETS = [
        ("SPY", "标普500ETF"),
        ("NVDA", "英伟达"),
        ("TSLA", "特斯拉"),
        ("MSTR", "微策略"),
    ]

    print(f"{'股票':<10} | {'策略':<10} | {'总收益%':<10} | {'最大回撤%':<10} | {'交易次数':<8}")
    print("-" * 65)

    for symbol, name in TARGETS:
        engine = BacktestingEngine()
        
        # 2. 设置参数：注意 interval 是 DAILY (日线)
        engine.set_parameters(
            vt_symbol=f"{symbol}.SMART",
            interval="d",  # d 代表 Daily
            start=datetime(2022, 1, 1),
            end=datetime.now(),
            rate=0.0005,
            slippage=0.1,
            size=100, # 美股大概买 100 股一手
            pricetick=0.01,
            capital=10_000_000, # 1000万美金本金，确保买得起！
        )

        # 3. 策略参数调整
        # 因为是日线，20/60 均线代表 20天/60天，这是很标准的中长线参数
        # fixed_size 设置为 100 股
        engine.add_strategy(XDualMaStrategy, {"fixed_size": 100})

        try:
            engine.load_data()
            if len(engine.history_data) == 0:
                print(f"{name:<10} | No Data")
                continue
                
            engine.run_backtesting()
            df = engine.calculate_result()
            stats = engine.calculate_statistics(output=False)
            
            print(f"{name:<10} | {'DualMA':<10} | {stats['total_return']:>9.2f}% | {stats['max_ddpercent']:>9.2f}% | {stats['total_trade_count']:>8}")

        except Exception as e:
            # print(e)
            pass

if __name__ == "__main__":
    run_us()
