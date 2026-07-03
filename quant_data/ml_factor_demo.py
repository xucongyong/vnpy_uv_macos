
import pandas as pd
import polars as pl
import lightgbm as lgb
from sqlalchemy import text
from datetime import datetime
import psycopg2
import warnings
warnings.filterwarnings('ignore')

def fetch_data(symbols):
    """直接使用 psycopg2 从 PostgreSQL 提取指定股票的历史数据"""
    print(f"📥 正在从数据库读取 {len(symbols)} 只股票的数据...")
    
    # 数据库连接参数 (直接硬连接，绕过 vn.py 封装)
    params = {
        "host": "v.xucongyong.com",
        "port": 5432,
        "user": "postgres",
        "password": "1121hotsren",
        "dbname": "postgres"
    }
    
    symbol_str = "','".join(symbols)
    # 注意 schema 是 quant_data
    sql = f"SELECT symbol, datetime as date, open_price as open, high_price as high, low_price as low, close_price as close, volume FROM quant_data.dbbardata WHERE symbol IN ('{symbol_str}') ORDER BY symbol, datetime"
    
    try:
        conn = psycopg2.connect(**params)
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ 数据库读取失败: {e}")
        return pd.DataFrame()

def calculate_factors_and_labels(pdf):
    """使用 Polars 极速计算因子和标签"""
    print("🧮 正在计算因子和未来收益率(标签)...")
    df = pl.from_pandas(pdf)
    
    factors = [
        (pl.col("close") / pl.col("close").shift(5) - 1).over("symbol").alias("momentum_5d"),
        (pl.col("close") / pl.col("close").shift(20) - 1).over("symbol").alias("momentum_20d"),
        ((pl.col("high") - pl.col("low")) / pl.col("close")).rolling_mean(20).over("symbol").alias("volatility_20d"),
        (pl.col("volume") / pl.col("volume").rolling_mean(20).shift(1) - 1).over("symbol").alias("volume_ratio_5d")
    ]
    
    label = [
        (pl.col("close").shift(-5) / pl.col("close")).log().over("symbol").alias("label_return_5d")
    ]
    
    df = df.with_columns(factors + label).drop_nulls()
    return df.to_pandas()

def train_and_predict(df):
    """使用 LightGBM 训练模型并进行预测"""
    print("🤖 正在进入 AI 炼丹炉 (LightGBM 训练)...")
    
    feature_cols = ["momentum_5d", "momentum_20d", "volatility_20d", "volume_ratio_5d"]
    label_col = "label_return_5d"
    
    train_df = df[df['date'] < '2024-01-01']
    test_df = df[df['date'] >= '2024-01-01']
    
    if train_df.empty or test_df.empty:
        print("⚠️ 数据量太少，不足以划分训练集和测试集。请确认数据库里有足够的数据。")
        return

    train_data = lgb.Dataset(train_df[feature_cols], label=train_df[label_col])
    
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'verbose': -1
    }
    
    print("   -> 正在训练模型...")
    model = lgb.train(params, train_data, num_boost_round=100)
    
    importance = pd.DataFrame({
        'Factor': feature_cols,
        'Importance': model.feature_importance()
    }).sort_values(by='Importance', ascending=False)
    
    print("\n🌟 [AI 结论] 因子重要性排名:")
    print(importance.to_string(index=False))
    
    print("\n🎯 模拟实盘打分 (根据最后一天的数据，预测哪只股票最值得买):")
    latest_data = test_df.groupby('symbol').last().reset_index()
    latest_data['ai_score'] = model.predict(latest_data[feature_cols])
    
    recommendation = latest_data[['symbol', 'date', 'ai_score']].sort_values(by='ai_score', ascending=False)
    print(recommendation.to_string(index=False))
    print("\n💡 提示: ai_score 就是模型预测的未来 5 天收益率。你应该做多得分最高的股票。")

if __name__ == "__main__":
    test_symbols = ["000001", "000002", "000063", "000858", "600519"]
    
    try:
        raw_data = fetch_data(test_symbols)
        if raw_data.empty:
            print("❌ 数据库中没有找到指定的股票数据。请确保同步脚本已经下载了这几只股票。")
        else:
            print(f"✅ 成功读取 {len(raw_data)} 行原始数据。")
            factor_data = calculate_factors_and_labels(raw_data)
            train_and_predict(factor_data)
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        import traceback
        traceback.print_exc()
