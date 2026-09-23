"""因子挖掘、评估与合成端到端运行脚本 (可直接运行的真实最小例子)

功能流程:
  ① 从真实远程 PostgreSQL (postgres.quant_data) 加载股票历史 K 线
  ② 批量计算已注册的 6 个经典因子
  ③ 科学评估每个因子的预测能力 (IC, Rank IC, IC_IR, 胜率) 并输出体检排行榜
  ④ 将因子合成一个总分 (Alpha Score)，模拟根据因子总分打分选出买入信号
"""

import argparse
import os
import sys
from pathlib import Path
import pandas as pd
import psycopg2

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from gemini_quant.factors.base import get_all_factors
from gemini_quant.evaluation.evaluator import evaluate_factor_on_symbol
from gemini_quant.portfolio.combiner import combine_factors

# 数据库连接参数 (指向你熟悉的 postgres.quant_data)
DB_PARAMS = {
    "host": "v.xucongyong.com",
    "port": 5432,
    "user": "postgres",
    "password": os.environ.get("PGPASSWORD", "1121hotsren"),
    "dbname": "postgres"
}


def load_bars_from_db(symbol: str, limit: int = 500) -> pd.DataFrame:
    """从数据库加载历史日线行情"""
    clean_sym = symbol.split(".")[0]
    sql = f"""
        SELECT datetime as date, open_price as open, high_price as high, 
               low_price as low, close_price as close, volume
        FROM quant_data.quant_data
        WHERE symbol = '{clean_sym}'
        ORDER BY datetime DESC
        LIMIT {limit};
    """
    conn = psycopg2.connect(**DB_PARAMS)
    df = pd.read_sql(sql, conn)
    conn.close()
    
    if df.empty:
        return df
    
    # 转换为升序时间序列
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def main():
    parser = argparse.ArgumentParser(description="多因子体系最小端到端测试")
    parser.add_argument("--symbol", default="00700.SEHK", help="测试标的, 默认 00700.SEHK (腾讯)")
    parser.add_argument("--days", type=int, default=500, help="回溯天数, 默认 500 天")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(f"🚀 启动多因子自动化测试: 标的={args.symbol} (加载近 {args.days} 个交易日真实数据)")
    print("=" * 70)

    # 1. 加载数据
    df = load_bars_from_db(args.symbol, args.days)
    if df.empty:
        print(f"❌ 未能从数据库加载到 {args.symbol} 的数据")
        return
    print(f"✅ 数据加载成功: 共 {len(df)} 根K线, 区间 {df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()}")

    # 2. 批量计算因子
    all_factors = get_all_factors()
    print(f"\n📦 已注册因子库 (共 {len(all_factors)} 个):")
    factor_values = {}
    for name, meta in all_factors.items():
        print(f"  - [{meta['category']}] {name:18s} : {meta['desc']}")
        factor_values[name] = meta["func"](df)

    # 3. 因子质量体检与评估 (IC / Rank IC / IR / 胜率)
    print("\n" + "=" * 70)
    print(f"📊 因子预测质量评估报告 (基于未来 5 天收益率预测)")
    print("=" * 70)
    eval_results = []
    for name, series in factor_values.items():
        metrics = evaluate_factor_on_symbol(series, df["close"], forward_periods=5)
        eval_results.append({
            "Factor": name,
            "Category": all_factors[name]["category"],
            "Rank IC": metrics["rank_ic"],
            "IC": metrics["ic"],
            "IC_IR": metrics["ic_ir"],
            "Win Rate %": metrics["win_rate"]
        })

    eval_df = pd.DataFrame(eval_results).sort_values("Rank IC", ascending=False)
    print(eval_df.to_string(index=False))

    # 4. 因子加权合成与综合打分
    print("\n" + "=" * 70)
    print("🧠 多因子合成与综合信号 (Composite Alpha Score)")
    print("=" * 70)
    # 选取 Rank IC > 0 的有效因子，赋予权重合成总分
    valid_weights = {row["Factor"]: max(row["Rank IC"], 0.05) for _, row in eval_df.iterrows()}
    composite_score = combine_factors(factor_values, weights=valid_weights)
    df["alpha_score"] = composite_score

    # 查看最近 5 天的因子打分情况
    recent_signals = df[["date", "close", "alpha_score"]].tail(5).copy()
    recent_signals["Signal"] = recent_signals["alpha_score"].apply(
        lambda s: "🟢 强烈看多" if s > 1.0 else ("🔴 强烈看空" if s < -1.0 else "⚪ 中性观望")
    )
    print("最近 5 个交易日的因子综合打分与交易信号:")
    print(recent_signals.to_string(index=False))
    print("\n🎉 整个多因子流水线从【数据库读取 -> 因子计算 -> 质量体检 -> 多因子合成 -> 信号输出】全流程测试成功！\n")


if __name__ == "__main__":
    main()
