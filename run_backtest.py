from datetime import datetime
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval

# 导入你的策略类
# 注意：这里对应的是 strategies 文件夹下的 my_strategy.py 文件中的 MyStrategy 类
from strategies.my_strategy import MyStrategy

def run():
    # 1. 创建回测引擎
    engine = BacktestingEngine()
    
    # 2. 设置回测参数
    engine.set_parameters(
        vt_symbol="IF888.CFFEX",    # 虚拟合约代码
        interval="1m",              # K线周期
        start=datetime(2019, 1, 1), # 开始时间
        end=datetime(2019, 4, 30),  # 结束时间
        rate=0.3/10000,             # 手续费万0.3
        slippage=0.2,               # 滑点0.2
        size=300,                   # 合约乘数
        pricetick=0.2,              # 最小价格变动
        capital=1_000_000,          # 初始本金
    )

    # 3. 添加策略
    # setting 字典可以用来覆盖策略里的默认参数，例如 {"fast_window": 20}
    engine.add_strategy(MyStrategy, {})

    # 4. 加载数据
    print("开始加载历史数据...")
    engine.load_data()

    # 5. 运行回测
    print("开始回测...")
    engine.run_backtesting()

    # 6. 计算盈亏结果
    print("计算结果...")
    df = engine.calculate_result()
    
    # 7. 打印统计指标
    print("----------------------------------------")
    engine.calculate_statistics()
    
    # 8. 如果在支持GUI的环境(如Jupyter)可以画图，命令行下通常省略
    # engine.show_chart()

if __name__ == "__main__":
    run()
