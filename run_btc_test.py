
from datetime import datetime
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval, Exchange
from strategies.btc_pro_strategy import BtcProStrategy

def run():
    engine = BacktestingEngine()
    
    # 设置回测参数
    engine.set_parameters(
        vt_symbol="BTCUSDT.LOCAL",
        interval=Interval.HOUR,
        start=datetime(2024, 3, 1),
        end=datetime.now(),
        rate=0.0001,                  
        slippage=5,                   
        size=1,                       
        pricetick=0.1,                
        capital=100_000,              
    )

    # 添加大玩家策略
    engine.add_strategy(BtcProStrategy, {})

    # 加载并运行
    engine.load_data()
    engine.run_backtesting()

    # 计算与展示结果
    print("-" * 30)
    print("📈 BTC 大玩家 - 2年长周期回测 (降噪版)")
    engine.calculate_result()
    stats = engine.calculate_statistics()
    print("-" * 30)

if __name__ == "__main__":
    run()
