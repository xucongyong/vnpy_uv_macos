
import pandas as pd
from datetime import datetime
from vnpy_ctastrategy.backtesting import BacktestingEngine
from x_generic_strategy import XGenericStrategy
from factor_library import FactorLibrary

def run_factor_scan():
    # 1. 目标资产
    symbol = "MSTR"
    vt_symbol = f"{symbol}.SMART"
    
    # 2. 自动获取所有因子名称
    # 只要是 factor_ 开头的函数都算
    available_factors = [func for func in dir(FactorLibrary) if func.startswith("factor_")]
    
    # 3. 构建测试任务清单
    # 格式: (因子名, p1参数, p2参数, 描述)
    tasks = []
    
    for factor in available_factors:
        if factor == "factor_double_ma_trend":
            tasks.append((factor, 5, 10, "均线激进 (5/10)"))
            tasks.append((factor, 10, 20, "均线波段 (10/20)"))
            tasks.append((factor, 20, 60, "均线趋势 (20/60)"))
        elif factor == "factor_rsi_reversal":
            tasks.append((factor, 6, 0, "RSI超短 (6)"))
            tasks.append((factor, 14, 0, "RSI标准 (14)"))
        elif factor == "factor_bollinger_breakout":
            tasks.append((factor, 20, 0, "布林带标准 (20)"))
        elif factor == "factor_momentum_roc":
            tasks.append((factor, 5, 0, "ROC动量 (5天)"))
            tasks.append((factor, 10, 0, "ROC动量 (10天)"))
        elif factor == "factor_turtle_breakout":
            tasks.append((factor, 10, 0, "海龟短线 (10日突破)"))
            tasks.append((factor, 20, 0, "海龟标准 (20日突破)"))

    # 4. 批量回测引擎启动
    print(f"🏭 因子工厂启动! 目标: {symbol}")
    print(f"📦 待测因子组合: {len(tasks)} 个")
    print("=" * 100)
    print(f"{ '因子名称':<25} | {'参数':<15} | {'收益率%':<10} | {'夏普比':<8} | {'回撤%':<10} | {'胜率%':<8}")
    print("-" * 100)
    
    results = []

    for factor_name, p1, p2, desc in tasks:
        engine = BacktestingEngine()
        engine.set_parameters(
            vt_symbol=vt_symbol,
            interval="d",
            start=datetime(2022, 1, 1),
            end=datetime.now(),
            rate=0.0005,
            slippage=0.1,
            size=1,
            pricetick=0.01,
            capital=1_000_000,
        )
        
        setting = {
            "factor_name": factor_name,
            "fixed_size": 100,
            "p1": p1,
            "p2": p2
        }
        
        engine.add_strategy(XGenericStrategy, setting)
        
        try:
            engine.load_data()
            if len(engine.history_data) == 0:
                continue
                
            engine.run_backtesting()
            engine.calculate_result()
            stats = engine.calculate_statistics(output=False)
            
            # 打印
            param_str = f"{p1}/{p2}"
            print(f"{factor_name:<25} | {param_str:<15} | {stats['total_return']:>9.2f}% | {stats['sharpe_ratio']:>8.2f} | {stats['max_ddpercent']:>9.2f}% | {stats.get('winning_rate', 0):>7.2f}%")
            
            results.append({
                "Factor": factor_name,
                "Params": param_str,
                "Description": desc,
                "Return %": stats['total_return'],
                "Sharpe": stats['sharpe_ratio'],
                "Max DD %": stats['max_ddpercent'],
                "Win Rate %": stats.get('winning_rate', 0)
            })
            
        except Exception as e:
            # print(f"Error testing {factor_name}: {e}")
            pass

    # 5. 最终排名
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values(by="Return %", ascending=False)
        print("=" * 100)
        print("🏆 因子王者排行榜")
        print(df[["Description", "Return %", "Sharpe", "Max DD %", "Win Rate %"]].to_string(index=False))
        df.to_csv("factor_ranking.csv", index=False)
        print("\n✅ 结果已保存至 factor_ranking.csv")

if __name__ == "__main__":
    run_factor_scan()
