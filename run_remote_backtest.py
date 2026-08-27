
from vnpy.trader.database import get_database
from vnpy.trader.constant import Exchange, Interval
from vnpy_ctastrategy.backtesting import BacktestingEngine
from datetime import datetime
from strategies.my_strategy import MyStrategy # 或者换成你具体的策略类名
from x_bollinger_strategy import XBollingerStrategy

def run_remote_test():
    print("🎬 [Backtest] 正在启动远程数据库回测引擎...")
    
    # 1. 初始化引擎
    engine = BacktestingEngine()
    
    # 2. 配置参数 (使用我们刚刚下载的平安银行数据)
    # 注意: 区间不要从 1991 开始 —— 当年股价 0.33 元, 后来涨了 33 倍,
    #       布林策略的做空逻辑在这种行情下会把账户打爆(资金归零)
    engine.set_parameters(
        vt_symbol="000001.SZSE", # 平安银行
        interval=Interval.DAILY,
        start=datetime(2015, 1, 1),
        end=datetime.now(),
        rate=0.0003, # 手续费
        slippage=0.2, # 滑点
        size=100, # 合约乘数
        pricetick=0.01, # 价格跳动
        capital=1_000_000, # 初始资金
    )
    
    # 3. 添加策略 (这里以布林带策略为例)
    # 注意: fixed_size 是股数, A股 size=100 (1手=100股), 100股即可避免单笔全仓爆仓
    engine.add_strategy(XBollingerStrategy, {"fixed_size": 100})
    
    # 4. 加载数据 (这一步会自动连接远程 PostgreSQL)
    print("   📥 正在从远程数据库加载 K 线数据...")
    engine.load_data()
    
    # 5. 开始回测
    print("   📈 正在运行回测...")
    engine.run_backtesting()
    
    # 6. 计算统计结果
    df = engine.calculate_result()
    statistics = engine.calculate_statistics()
    
    print("\n" + "="*50)
    print("🏆 回测报告 (平安银行 2015-2026)")
    for key, value in statistics.items():
        print(f"   - {key}: {value}")
    print("="*50)
    
    # 7. 绘图 (如果需要，会自动弹出浏览器)
    # engine.plot_chart()

if __name__ == "__main__":
    run_remote_test()
