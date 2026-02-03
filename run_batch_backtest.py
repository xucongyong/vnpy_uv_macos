
from datetime import datetime
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval

# 导入我们的两个策略
from x_dual_ma_strategy import XDualMaStrategy
from x_bollinger_strategy import XBollingerStrategy

def run_batch():
    # 要测试的股票列表 (必须和下载的一致)
    TARGETS = [
        ("00700.SEHK", "腾讯控股"),
        ("03690.SEHK", "美团"),
        ("TSLA.NASDAQ", "特斯拉"),
        ("AAPL.NASDAQ", "苹果"),
        ("NVDA.NASDAQ", "英伟达"),
    ]

    # 要测试的策略列表
    STRATEGIES = [
        ("DualMA_ADX", XDualMaStrategy, {}),  # 策略名, 类, 参数
        ("Bollinger", XBollingerStrategy, {}),
    ]

    print(f"{'股票':<10} | {'策略':<12} | {'总收益%':<10} | {'最大回撤%':<10} | {'交易次数':<8}")
    print("-" * 65)

    for symbol, name in TARGETS:
        
        # 针对不同市场设置手续费和跳动
        if "SEHK" in symbol:
            rate = 0.0015 # 港股千分之1.5
            pricetick = 0.2
            slippage = 0.2
        else:
            rate = 0.0005 # 美股假设万分之5
            pricetick = 0.01
            slippage = 0.05

        for strat_name, strat_class, strat_setting in STRATEGIES:
            engine = BacktestingEngine()
            engine.set_parameters(
                vt_symbol=symbol,
                interval="1m",
                start=datetime(2022, 1, 1),
                end=datetime(2025, 6, 1),
                rate=rate,
                slippage=slippage,
                size=1,
                pricetick=pricetick,
                capital=1_000_000,
            )
            
            # 添加策略
            engine.add_strategy(strat_class, strat_setting)
            
            # 加载数据 (静默模式，不打印进度条)
            # 注意：如果数据没下载，这里会加载不到数据
            try:
                engine.load_data()
                if len(engine.history_data) == 0:
                    print(f"{name:<10} | {strat_name:<12} | {'No Data':<10} | {'-':<10} | {'-':<8}")
                    continue
                    
                engine.run_backtesting()
                df = engine.calculate_result()
                stats = engine.calculate_statistics(output=False) # output=False 不打印详细日志
                
                return_pct = f"{stats['total_return']:.2f}%"
                drawdown_pct = f"{stats['max_ddpercent']:.2f}%"
                trade_count = stats['total_trade_count']
                
                print(f"{name:<10} | {strat_name:<12} | {return_pct:<10} | {drawdown_pct:<10} | {trade_count:<8}")

            except Exception as e:
                print(f"{name:<10} | {strat_name:<12} | Error: {e}")

if __name__ == "__main__":
    run_batch()
