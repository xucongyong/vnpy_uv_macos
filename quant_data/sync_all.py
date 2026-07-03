
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
from vnpy.trader.database import get_database
import time
import sys

# 版本标识
VERSION = "1.0.4"

class MarketDownloader:
    def __init__(self, days=30):
        print(f"🚀 [QuantData] 正在初始化同步程序 (版本: {VERSION})...")
        try:
            self.db = get_database()
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            sys.exit(1)
        self.days = days
        self.start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
    def safe_float(self, value):
        """安全转换 float，处理 None 和空字符串"""
        if value is None or value == "" or pd.isna(value):
            return 0.0
        try:
            return float(value)
        except:
            return 0.0

    def save_to_db(self, symbol, exchange, df):
        if df is None or df.empty: return
        bars = []
        for _, row in df.iterrows():
            # 1. 处理时间
            raw_dt = row.get("date") or row.get("日期")
            if raw_dt is None: continue
            
            dt = pd.to_datetime(raw_dt)
            if dt.tzinfo is not None:
                dt = dt.tz_convert(None)
            py_dt = dt.to_pydatetime()
            
            # 2. 安全获取数值
            open_p = self.safe_float(row.get("open") or row.get("开盘"))
            high_p = self.safe_float(row.get("high") or row.get("最高"))
            low_p = self.safe_float(row.get("low") or row.get("最低"))
            close_p = self.safe_float(row.get("close") or row.get("收盘"))
            vol = self.safe_float(row.get("volume") or row.get("成交量"))
            
            # 3. 简单清洗：过滤掉价格为 0 的无效数据（通常是停牌）
            if close_p <= 0: continue
            
            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                datetime=py_dt,
                interval=Interval.DAILY,
                open_price=open_p,
                high_price=high_p,
                low_price=low_p,
                close_price=close_p,
                volume=vol,
                gateway_name="SINA"
            )
            bars.append(bar)
        
        if bars:
            try:
                self.db.save_bar_data(bars)
            except Exception as e:
                print(f"   ❌ 保存数据到数据库失败: {e}")

    def sync_a_shares(self):
        print("🇨🇳 [QuantData] 正在同步 A 股 (Sina)...")
        try:
            symbols = ["sh600036", "sz000001", "sh600519", "sz000858"] 
            for code in symbols:
                print(f"  -> 同步 {code}...")
                df = ak.stock_zh_a_daily(symbol=code, start_date=self.start_date, adjust="qfq")
                exchange = Exchange.SSE if code.startswith("sh") else Exchange.SZSE
                self.save_to_db(code[2:], exchange, df)
                time.sleep(0.5)
            print("✅ A 股同步任务完成")
        except Exception as e:
            print(f"❌ A 股同步失败: {e}")

    def sync_hk_shares(self):
        print("🇭🇰 [QuantData] 正在同步港股 (Sina)...")
        try:
            symbols = ["00700", "09988", "03690"]
            for code in symbols:
                print(f"  -> 同步 {code}...")
                df = ak.stock_hk_daily(symbol=code, adjust="qfq")
                self.save_to_db(code, Exchange.SEHK, df)
                time.sleep(0.5)
            print("✅ 港股同步任务完成")
        except Exception as e:
            print(f"❌ 港股同步失败: {e}")

    def sync_us_shares(self):
        print("🇺🇸 [QuantData] 正在同步美股 (Sina)...")
        try:
            symbols = ["AAPL", "TSLA", "NVDA", "MSFT"]
            for code in symbols:
                print(f"  -> 同步 {code}...")
                df = ak.stock_us_daily(symbol=code, adjust="qfq")
                self.save_to_db(code, Exchange.NASDAQ, df)
                time.sleep(0.5)
            print("✅ 美股同步任务完成")
        except Exception as e:
            print(f"❌ 美股同步失败: {e}")

if __name__ == "__main__":
    downloader = MarketDownloader(days=30)
    market = sys.argv[1] if len(sys.argv) > 1 else "all"
    if market in ["a", "all"]: downloader.sync_a_shares()
    if market in ["hk", "all"]: downloader.sync_hk_shares()
    if market in ["us", "all"]: downloader.sync_us_shares()
