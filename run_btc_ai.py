
import warnings
warnings.filterwarnings("ignore")

import yfinance as yf
import polars as pl
import numpy as np
from datetime import datetime, timedelta
from functools import partial

from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import BarData
from vnpy.alpha import AlphaLab, Segment, AlphaDataset, AlphaModel
from vnpy.alpha.dataset.datasets.alpha_158 import Alpha158
from vnpy.alpha.dataset import process_drop_na
from vnpy.alpha.model.models.lgb_model import LgbModel

def main():
    # 1. 初始化 AI 实验室
    lab = AlphaLab("./lab/btc_ai")
    
    symbol = "BTC-USD"
    vn_symbol = "BTCUSDT.LOCAL"
    
    print("==================================================")
    print("🚀 第一步：获取数据 (下载过去 6 年的 BTC 日线数据)")
    start_date = (datetime.now() - timedelta(days=365 * 6)).strftime("%Y-%m-%d")
    
    try:
        df_yf = yf.download(symbol, start=start_date, interval="1d", progress=False)
        if not df_yf.empty:
            bars = []
            for index, row in df_yf.iterrows():
                dt = index.to_pydatetime().replace(tzinfo=None)
                bar = BarData(
                    symbol="BTCUSDT",
                    exchange=Exchange.LOCAL,
                    datetime=dt,
                    interval=Interval.DAILY,
                    open_price=float(row['Open'].iloc[0]) if isinstance(row['Open'], pl.Series) or hasattr(row['Open'], 'iloc') else float(row['Open']),
                    high_price=float(row['High'].iloc[0]) if isinstance(row['High'], pl.Series) or hasattr(row['High'], 'iloc') else float(row['High']),
                    low_price=float(row['Low'].iloc[0]) if isinstance(row['Low'], pl.Series) or hasattr(row['Low'], 'iloc') else float(row['Low']),
                    close_price=float(row['Close'].iloc[0]) if isinstance(row['Close'], pl.Series) or hasattr(row['Close'], 'iloc') else float(row['Close']),
                    volume=float(row['Volume'].iloc[0]) if isinstance(row['Volume'], pl.Series) or hasattr(row['Volume'], 'iloc') else float(row['Volume']),
                    turnover=float(row['Volume'].iloc[0]) * float(row['Close'].iloc[0]) if hasattr(row['Volume'], 'iloc') else float(row['Volume']) * float(row['Close']),
                    gateway_name="YAHOO"
                )
                bars.append(bar)
            lab.save_bar_data(bars)
            print(f"✅ 成功从 Yahoo 下载并加载 {len(bars)} 天的日线数据！")
        else:
            raise ValueError("Yahoo 返回空数据")
    except Exception as e:
        print(f"⚠️ Yahoo 下载失败 ({e})，正在尝试从本地数据库加载...")
        # 尝试从本地加载，看是否有数据
        existing_bars = lab.load_bar_data(vn_symbol, Interval.DAILY, start_date, datetime.now())
        if existing_bars:
            print(f"✅ 成功从本地数据库恢复 {len(existing_bars)} 条日线数据！")
        else:
            print("❌ 本地数据库也没有数据，请稍后再试。")
            return

    # 2. 计算 Alpha158 特征
    print("\n==================================================")
    print("🧠 第二步：特征工程 (计算 Qlib Alpha 158 个高维因子)")
    
    # 取出数据进行计算
    start_dt = datetime.now() - timedelta(days=365 * 6)
    end_dt = datetime.now()
    
    df_bars = lab.load_bar_df([vn_symbol], Interval.DAILY, start_dt, end_dt, extended_days=100)
    
    # 划分训练集、验证集、测试集
    # 训练：前 3.5 年，验证：中间 1 年，测试：最近 1.5 年
    train_start = start_dt.strftime("%Y-%m-%d")
    train_end = (start_dt + timedelta(days=365 * 3.5)).strftime("%Y-%m-%d")
    
    valid_start = (start_dt + timedelta(days=365 * 3.5 + 1)).strftime("%Y-%m-%d")
    valid_end = (start_dt + timedelta(days=365 * 4.5)).strftime("%Y-%m-%d")
    
    test_start = (start_dt + timedelta(days=365 * 4.5 + 1)).strftime("%Y-%m-%d")
    test_end = end_dt.strftime("%Y-%m-%d")
    
    dataset = Alpha158(
        df_bars,
        train_period=(train_start, train_end),
        valid_period=(valid_start, valid_end),
        test_period=(test_start, test_end)
    )
    
    # 预处理：去掉空值 (不使用横截面标准化，因为只有一个标的)
    dataset.add_processor("learn", partial(process_drop_na, names=["label"]))
    
    # 并行计算特征
    filters = {vn_symbol: [(start_dt, end_dt)]}
    dataset.prepare_data(filters, max_workers=6)
    dataset.process_data()
    
    lab.save_dataset("btc_158", dataset)
    print("✅ Alpha 158 因子计算完成！")

    # 3. 训练 LightGBM 模型
    print("\n==================================================")
    print("🤖 第三步：模型训练 (让 LightGBM 学习因子与未来收益的非线性关系)")
    
    model = LgbModel(seed=42)
    model.fit(dataset)
    lab.save_model("btc_lgb", model)
    print("✅ 模型训练完成！")

    # 4. 生成预测信号
    print("\n==================================================")
    print("🔮 第四步：预测测试集 (最近 1.5 年) 的涨跌信号")
    
    pre = model.predict(dataset, Segment.TEST)
    df_t = dataset.fetch_infer(Segment.TEST)
    df_t = df_t.with_columns(pl.Series(pre).alias("signal"))
    
    # 从原始数据集中合并 close 价格用于计算真实收益率
    df_t = df_t.join(dataset.df.select(["datetime", "vt_symbol", "close"]), on=["datetime", "vt_symbol"], how="inner")
    
    signal_df = df_t.select(["datetime", "vt_symbol", "signal", "close"])
    
    # 进行一次简单的矢量化智能回测
    print("\n==================================================")
    print("📈 第五步：智能回测 (基于 AI 信号的自动多空策略)")
    
    # 策略逻辑：
    # AI 预测未来的收益率 (signal)。
    # 如果预测 signal > 0，说明看涨，做多；
    # 如果预测 signal < 0，说明看跌，做空。
    
    pandas_df = signal_df.to_pandas()
    pandas_df.set_index("datetime", inplace=True)
    
    # 计算每日真实收益率
    pandas_df["real_return"] = pandas_df["close"].pct_change()
    
    # 根据 T-1 日的预测信号，决定 T 日的仓位方向 (1 为多，-1 为空)
    pandas_df["position"] = np.where(pandas_df["signal"].shift(1) > 0, 1, -1)
    
    # 计算策略收益
    pandas_df["strategy_return"] = pandas_df["position"] * pandas_df["real_return"]
    
    # 计算资金曲线
    pandas_df["cumulative_market"] = (1 + pandas_df["real_return"]).cumprod()
    pandas_df["cumulative_strategy"] = (1 + pandas_df["strategy_return"]).cumprod()
    
    final_market = pandas_df["cumulative_market"].iloc[-1]
    final_strategy = pandas_df["cumulative_strategy"].iloc[-1]
    
    print(f"回测时间段: {test_start} 至 {test_end}")
    print(f"如果一直持有 (买入并持有) 收益率: {(final_market - 1) * 100:.2f}%")
    print(f"🌟 机器学习 AI 策略 收益率: {(final_strategy - 1) * 100:.2f}%")
    
    # 计算胜率
    winning_days = len(pandas_df[pandas_df["strategy_return"] > 0])
    total_trade_days = len(pandas_df[pandas_df["strategy_return"] != 0])
    print(f"日胜率 (预测准确率): {winning_days / total_trade_days * 100:.2f}%")
    print("\n任务完成！这就是现代量化最强大的武器。")

if __name__ == "__main__":
    main()
