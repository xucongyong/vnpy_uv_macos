
import pandas as pd
from datetime import datetime
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval, Exchange

# 导入你的策略
from x_dual_ma_strategy import XDualMaStrategy
# 未来可以在这里导入更多策略，如:
# from x_bollinger_strategy import XBollingerStrategy 

def run_batch_backtest():
    # ----------------------------------------------------------- 
    # 1. 实验配置区 (The Lab Configuration)
    # -----------------------------------------------------------    
    
    # 1.1 股票池 (Target Assets)
    symbols = [
        "TSLA", "NVDA", "SPY", "MSTR", "AAPL"
    ]
    
    # 1.2 策略池与参数网格 (Strategy & Parameter Grid)
    # 格式：(策略类, 参数字典列表)
    strategies_config = [
        (XDualMaStrategy, [
            # 激进短线 (5日穿10日)
            {"fast_window": 5, "slow_window": 10, "fixed_size": 100},
            # 稳健波段 (10日穿20日)
            {"fast_window": 10, "slow_window": 20, "fixed_size": 100},
            # 经典趋势 (20日穿60日) - 我们之前的默认设置
            {"fast_window": 20, "slow_window": 60, "fixed_size": 100},
            # 长期信仰 (50日穿200日) - 著名的“金叉/死叉”
            {"fast_window": 50, "slow_window": 200, "fixed_size": 100},
        ]),
        
        # 未来可以在这里加布林带策略的参数组合...
    ]

    # 1.3 回测通用设置
    start_date = datetime(2022, 1, 1)
    end_date = datetime.now()
    capital = 1_000_000   # 100万本金
    commission = 0.0005   # 手续费万5
    slippage = 0.1        # 滑点
    
    # ----------------------------------------------------------- 
    # 2. 批量执行区 (Execution Engine)
    # -----------------------------------------------------------    
    
    results = [] # 用于存储每一场回测的结果

    print(f"🚀 开始批量回测工厂...")
    print(f"📅 时间范围: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"💰 初始本金: ${capital:,.0f}")
    print("=" * 80)
    print(f"{ '股票':<8} | { '策略':<10} | { '参数':<25} | { '收益率%':<10} | { '夏普比':<8} | { '回撤%':<10}")
    print("-" * 80)

    for symbol in symbols:
        vt_symbol = f"{symbol}.SMART"
        
        # 针对每个策略类
        for strategy_class, param_list in strategies_config:
            strategy_name_base = strategy_class.__name__.replace("Strategy", "").replace("X", "")
            
            # 针对每组参数
            for setting in param_list:
                # 创建回测引擎
                engine = BacktestingEngine()
                engine.set_parameters(
                    vt_symbol=vt_symbol,
                    interval="d",
                    start=start_date,
                    end=end_date,
                    rate=commission,
                    slippage=slippage,
                    size=1, # 合约乘数，美股设为1即可 (手数在fixed_size控制)
                    pricetick=0.01,
                    capital=capital,
                )
                
                # 添加策略
                engine.add_strategy(strategy_class, setting)
                
                try:
                    # 加载数据
                    engine.load_data()
                    data_count = len(engine.history_data)
                    
                    if data_count == 0:
                        continue # 没数据就跳过
                    
                    # 运行回测
                    engine.run_backtesting()
                    engine.calculate_result()
                    stats = engine.calculate_statistics(output=False)
                    
                    # 格式化参数字符串
                    param_str = f"F{setting['fast_window']}/S{setting['slow_window']}"
                    
                    # 打印单行结果
                    print(f"{symbol:<8} | {strategy_name_base:<10} | {param_str:<25} | {stats['total_return']:>9.2f}% | {stats['sharpe_ratio']:>8.2f} | {stats['max_ddpercent']:>9.2f}%")
                    
                    # 收集结果
                    results.append({
                        "Symbol": symbol,
                        "Strategy": strategy_name_base,
                        "Fast": setting['fast_window'],
                        "Slow": setting['slow_window'],
                        "Total Return %": stats['total_return'],
                        "Sharpe Ratio": stats['sharpe_ratio'],
                        "Max Drawdown %": stats['max_ddpercent'],
                        "Trades": stats['total_trade_count'],
                        "Win Rate %": float(stats['winning_rate']) if stats.get('winning_rate') else 0.0
                    })
                    
                except Exception as e:
                    # print(f"Error: {e}")
                    pass

    # ----------------------------------------------------------- 
    # 3. 结果分析区 (Analysis)
    # -----------------------------------------------------------    
    print("=" * 80)
    print("🏆 冠军策略排行榜 (按收益率排序)")
    
    if results:
        df = pd.DataFrame(results)
        # 按收益率降序排列
        df_sorted = df.sort_values(by="Total Return %", ascending=False)
        
        # 保存到 CSV
        csv_filename = "batch_backtest_results.csv"
        df_sorted.to_csv(csv_filename, index=False)
        
        # 打印前5名
        print(df_sorted.head(5).to_string(index=False))
        print(f"\n✅ 详细报告已保存至: {csv_filename}")
    else:
        print("⚠️ 没有产生任何回测结果。  ")

if __name__ == "__main__":
    run_batch_backtest()
