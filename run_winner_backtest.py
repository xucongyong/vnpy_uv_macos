from datetime import datetime
from vnpy_ctastrategy.backtesting import BacktestingEngine
from x_dual_ma_strategy import XDualMaStrategy
import pandas as pd

def run_detailed_backtest():
    # 1. 锁定冠军参数
    symbol = "MSTR"
    vt_symbol = f"{symbol}.SMART"
    
    # 2. 初始化引擎
    engine = BacktestingEngine()
    engine.set_parameters(
        vt_symbol=vt_symbol,
        interval="d",
        start=datetime(2022, 1, 1),
        end=datetime.now(),
        rate=0.0005,      # 万5手续费
        slippage=0.1,     # 滑点
        size=1,
        pricetick=0.01,
        capital=1_000_000,
    )

    # 3. 添加冠军策略
    engine.add_strategy(XDualMaStrategy, {
        "fast_window": 5,
        "slow_window": 10,
        "fixed_size": 100
    })

    # 4. 执行
    print(f"🎬 正在为冠军 {symbol} (5/10均线) 进行深度演习...")
    engine.load_data()
    engine.run_backtesting()
    engine.calculate_result()
    
    # 5. 显示核心统计指标
    stats = engine.calculate_statistics()
    
    print("\n" + "="*50)
    print(f"📊 {symbol} 深度回测报告摘要")
    print("="*50)
    print(f"首发本金:   $1,000,000")
    print(f"最终净值:   ${stats['end_balance']:,.2f}")
    print(f"总收益率:   {stats['total_return']:,.2f}%")
    print(f"年化收益:   {stats['annual_return']:,.2f}%")
    print(f"最大回撤:   {stats['max_drawdown']:,.2f} ({stats['max_ddpercent']:.2f}%)")
    print(f"夏普比率:   {stats['sharpe_ratio']:.2f}")
    print(f"总交易次数: {stats['total_trade_count']}")
    print(f"胜率:       {stats['winning_rate']:.2f}%")
    print(f"盈亏比:     {stats['profit_loss_ratio']:.2f}")
    print("="*50)

    # 6. 看看最后5笔交易长什么样
    if engine.trades:
        print("\n📝 最近 5 笔成交记录:")
        trades_list = []
        for trade in list(engine.trades.values())[-5:]:
            trades_list.append({
                "时间": trade.datetime.strftime("%Y-%m-%d"),
                "方向": trade.direction.value,
                "价格": trade.price,
                "数量": trade.volume
            })
        print(pd.DataFrame(trades_list).to_string(index=False))

if __name__ == "__main__":
    run_detailed_backtest()
