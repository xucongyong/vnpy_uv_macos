
import yfinance as yf
from datetime import datetime
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
from vnpy.trader.database import get_database
from zoneinfo import ZoneInfo

def import_yahoo_data():
    # 1. 定义我们要“走私”的美股名单
    # 格式：(雅虎代码, VNPY代码, 名称)
    TARGETS = [
        ("SPY", "SPY", "标普500ETF"),
        ("NVDA", "NVDA", "英伟达"),
        ("TSLA", "TSLA", "特斯拉"),
        ("AAPL", "AAPL", "苹果"),
        ("MSTR", "MSTR", "微策略(比特币概念)"),
    ]

    start_date = "2022-01-01"
    end_date = datetime.now().strftime("%Y-%m-%d")

    database = get_database()
    
    print(f"开始从 Yahoo Finance 下载数据 ({start_date} ~ {end_date})...")
    print("-" * 50)

    for yf_symbol, vn_symbol, name in TARGETS:
        print(f"正在下载 {name} ({yf_symbol})...")
        
        # 从雅虎下载日线数据
        df = yf.download(yf_symbol, start=start_date, end=end_date, interval="1d", progress=False)
        
        if df.empty:
            print(f"❌ {name} 下载失败，没数据。")
            continue

        bars = []
        # 遍历下载的数据
        for index, row in df.iterrows():
            # 雅虎的时间是 index
            dt = index.to_pydatetime()
            # 移除时区信息
            dt = dt.replace(tzinfo=None)
            # 强行设置时间为 16:00:00 (美股收盘时间)，防止被 VN.py 过滤
            dt = dt.replace(hour=16, minute=0, second=0)

            bar = BarData(
                symbol=vn_symbol,
                exchange=Exchange.SMART, # 伪装成 SMART 交易所
                datetime=dt,
                interval=Interval.DAILY, # 标记为日线
                volume=row['Volume'],
                open_price=row['Open'],
                high_price=row['High'],
                low_price=row['Low'],
                close_price=row['Close'],
                gateway_name="YAHOO"
            )
            bars.append(bar)

        if bars:
            database.save_bar_data(bars)
            print(f"✅ 成功写入 {len(bars)} 条日线数据到数据库！")
        else:
            print(f"⚠️ {name} 有数据但转换失败。")

    print("-" * 50)
    print("全部搞定！现在你的数据库里有美股数据了！")

if __name__ == "__main__":
    import_yahoo_data()
