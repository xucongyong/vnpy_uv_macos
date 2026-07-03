
from vnpy.trader.database import get_database
from vnpy.trader.constant import Interval, Exchange
from datetime import datetime, timedelta

def view_sample_data():
    print("👀 [QuantData] 正在通过 vn.py 引擎读取云端数据...")
    try:
        db = get_database()
        
        # 1. 先看数据库里有哪些货 (概览)
        overviews = db.get_bar_overview()
        
        if not overviews:
            print("⚠️ 云端数据库目前是空的，数据还没飞过去呢！")
            return
            
        print(f"✅ 发现 {len(overviews)} 只股票已同步。")
        
        # 2. 拿第一个概览做展示
        ov = overviews[0]
        print(f"\n📊 正在读取 [{ov.symbol}] 的最后几条数据...")
        
        # 读取最后 5 天的数据
        bars = db.load_bar_data(
            symbol=ov.symbol,
            exchange=ov.exchange,
            interval=ov.interval,
            start=ov.end - timedelta(days=10),
            end=ov.end + timedelta(days=1)
        )
        
        if bars:
            print("-" * 60)
            print(f"{'日期':<20} | {'开盘':<10} | {'最高':<10} | {'收盘':<10}")
            for bar in bars[-10:]:
                print(f"{str(bar.datetime):<20} | {bar.open_price:<10.2f} | {bar.high_price:<10.2f} | {bar.close_price:<10.2f}")
            print("-" * 60)
        else:
            print("⚠️ 找到了概览，但没加载出具体 K 线数据。")
            
    except Exception as e:
        print(f"❌ 读取失败: {e}")

if __name__ == "__main__":
    view_sample_data()
