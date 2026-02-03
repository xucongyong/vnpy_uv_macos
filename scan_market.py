
import sys
import os
import pandas as pd
from datetime import datetime
from vnpy_ctastrategy.backtesting import BacktestingEngine
from vnpy.trader.constant import Interval, Exchange

# 导入策略
from x_dual_ma_strategy import XDualMaStrategy
from x_bollinger_strategy import XBollingerStrategy

def run_scan():
    """
    港股全明星策略扫描
    """
    # === 配置 ===
    MARKET = "HK"
    STAR_STOCKS = [
        ("00700", Exchange.SEHK, "腾讯控股"),
        ("09988", Exchange.SEHK, "阿里巴巴-W"),
        ("03690", Exchange.SEHK, "美团-W"),
        ("01810", Exchange.SEHK, "小米集团-W"),
        ("01024", Exchange.SEHK, "快手-W"),
        ("09888", Exchange.SEHK, "百度集团-SW"),
        ("01211", Exchange.SEHK, "比亚迪股份"),
        ("00981", Exchange.SEHK, "中芯国际"),
        ("02318", Exchange.SEHK, "中国平安"),
        ("03888", Exchange.SEHK, "金山软件"),
    ]
    
    # 策略池
    STRATEGIES = [
        {"name": "DualMA_ADX", "class": XDualMaStrategy, "setting": {}},
        {"name": "Bollinger", "class": XBollingerStrategy, "setting": {}},
    ]
    # ===========

    results = []
    print(f"开始扫描港股全明星股票...")
    print(f"{'代码':<10} | {'名称':<8} | {'策略':<12} | {'收益%':<8} | {'回撤%':<8} | {'次数':<6}")
    print("-" * 70)

    for symbol, exchange, name in STAR_STOCKS:
        # 港股手续费
        rate = 0.0015
        pricetick = 0.2
        slippage = 0.2

        # 对每个策略进行回测
        for strat in STRATEGIES:
            engine = BacktestingEngine()
            engine.set_parameters(
                vt_symbol=f"{symbol}.{exchange.value}",
                interval="1m",
                start=datetime(2023, 1, 1),
                end=datetime.now(),
                rate=rate,
                slippage=slippage,
                size=1,
                pricetick=pricetick,
                capital=1_000_000,
            )
            
            engine.add_strategy(strat["class"], strat["setting"])
            
            try:
                engine.load_data()
                if len(engine.history_data) == 0:
                    continue # 没数据就跳过
                    
                engine.run_backtesting()
                engine.calculate_result()
                stats = engine.calculate_statistics(output=False)
                
                # 记录结果
                res = {
                    "code": symbol,
                    "name": name,
                    "strategy": strat["name"],
                    "return": stats["total_return"],
                    "drawdown": stats["max_ddpercent"],
                    "trades": stats["total_trade_count"],
                    "sharpe": stats["sharpe_ratio"]
                }
                results.append(res)
                
                # 打印简报
                print(f"{symbol:<10} | {name:<8} | {strat['name']:<12} | {stats['total_return']:>6.2f}% | {stats['max_ddpercent']:>6.2f}% | {stats['total_trade_count']:>6}")
                
            except Exception as e:
                # print(f"Error {symbol}: {e}")
                pass

    # 3. 保存最终排行榜
    if results:
        res_df = pd.DataFrame(results)
        # 按收益率从高到低排序
        res_df = res_df.sort_values(by="return", ascending=False)
        
        output_file = "scan_results.csv"
        res_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print("-" * 70)
        print(f"扫描完成！排行榜已保存至: {output_file}")
        print("请用 Excel 打开查看谁是冠军！🏆")
    else:
        print("未产生任何回测结果，请检查是否已下载数据。")

if __name__ == "__main__":
    run_scan()
