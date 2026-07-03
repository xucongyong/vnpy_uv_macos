
import yfinance as yf
from datetime import datetime, timedelta
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
from vnpy.trader.database import get_database

def download_btc_long():
    symbol = "BTC-USD"
    vn_symbol = "BTCUSDT"
    exchange = Exchange.LOCAL 
    
    # 抓取过去 720 天的小时数据 (接近 2 年的极限)
    start_date = (datetime.now() - timedelta(days=720)).strftime("%Y-%m-%d")
    
    print(f"🚀 正在深度抓取 {symbol} 过去 2 年 (720天) 的小时线数据...")
    df = yf.download(symbol, start=start_date, interval="1h", progress=True)
    
    if df.empty:
        print("❌ 下载失败！请尝试缩短时间或检查网络。")
        return

    bars = []
    database = get_database()
    
    for index, row in df.iterrows():
        dt = index.to_pydatetime().replace(tzinfo=None)
        
        bar = BarData(
            symbol=vn_symbol,
            exchange=exchange,
            datetime=dt,
            interval=Interval.HOUR,
            open_price=float(row['Open']),
            high_price=float(row['High']),
            low_price=float(row['Low']),
            close_price=float(row['Close']),
            volume=float(row['Volume']),
            gateway_name="YAHOO"
        )
        bars.append(bar)
    
    database.save_bar_data(bars)
    print(f"✅ 成功导入 {len(bars)} 条长周期历史数据！")

if __name__ == "__main__":
    download_btc_long()
