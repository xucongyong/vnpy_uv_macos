
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
import time
import sys

# 硬连接 PostgreSQL
try:
    from vnpy.trader.database import get_database
except ImportError:
    print("❌ 错误：请确保已安装 vnpy 环境。")
    sys.exit(1)

class DailyIncrementalSync:
    def __init__(self, days=5):
        print(f"🚀 [DailySync] 正在初始化增量同步 (回溯 {days} 天)...")
        self.db = get_database()
        self.days = days
        self.start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

    def get_sina_symbol(self, code):
        if code.startswith(('60', '68', '90')): return "sh" + code, Exchange.SSE
        elif code.startswith(('00', '30', '20')): return "sz" + code, Exchange.SZSE
        elif code.startswith(('8', '43', '92')): return "bj" + code, Exchange.BSE
        return "sh" + code, Exchange.SSE

    def save_bars(self, symbol, exchange, df):
        if df is None or df.empty: return
        bars = []
        for _, row in df.iterrows():
            dt = pd.to_datetime(row.get("date") or row.get("日期"))
            if dt.tzinfo is not None: dt = dt.tz_convert(None)
            bar = BarData(
                symbol=symbol, exchange=exchange, datetime=dt.to_pydatetime(),
                interval=Interval.DAILY,
                open_price=float(row.get("open") or row.get("开盘") or 0),
                high_price=float(row.get("high") or row.get("最高") or 0),
                low_price=float(row.get("low") or row.get("最低") or 0),
                close_price=float(row.get("close") or row.get("收盘") or 0),
                volume=float(row.get("volume") or row.get("成交量") or 0),
                gateway_name="DAILY_SYNC"
            )
            bars.append(bar)
        self.db.save_bar_data(bars)

    def sync_a(self):
        print("🇨🇳 正在同步 A 股增量...")
        stocks = ak.stock_zh_a_spot_em()
        for i, code in enumerate(stocks['代码'].tolist()):
            sina_symbol, ex = self.get_sina_symbol(code)
            try:
                df = ak.stock_zh_a_daily(symbol=sina_symbol, start_date=self.start_date, adjust="qfq")
                self.save_bars(code, ex, df)
                if i % 100 == 0: print(f"进度: {i}/{len(stocks)}")
            except: pass

    def sync_hk(self):
        print("🇭🇰 正在同步港股增量...")
        stocks = ak.stock_hk_spot_em()
        for i, code in enumerate(stocks['代码'].tolist()):
            try:
                df = ak.stock_hk_daily(symbol=code, adjust="qfq")
                # 过滤最近几天
                df['date'] = pd.to_datetime(df['date'])
                df = df[df['date'] >= (datetime.now() - timedelta(days=self.days))]
                self.save_bars(code, Exchange.SEHK, df)
                if i % 100 == 0: print(f"进度: {i}/{len(stocks)}")
            except: pass

    def sync_us(self):
        print("🇺🇸 正在同步美股增量...")
        stocks = ak.stock_us_spot_em()
        for i, row in stocks.iterrows():
            code = str(row['代码']).split('.')[-1]
            try:
                df = ak.stock_us_daily(symbol=code, adjust="qfq")
                df['date'] = pd.to_datetime(df['date'])
                df = df[df['date'] >= (datetime.now() - timedelta(days=self.days))]
                self.save_bars(code, Exchange.NASDAQ, df)
                if i % 100 == 0: print(f"进度: {i}/{len(stocks)}")
            except: pass

if __name__ == "__main__":
    sync = DailyIncrementalSync(days=5)
    market = sys.argv[1] if len(sys.argv) > 1 else "all"
    if market in ["a", "all"]: sync.sync_a()
    if market in ["hk", "all"]: sync.sync_hk()
    if market in ["us", "all"]: sync.sync_us()
    print(f"✅ [{datetime.now()}] 增量同步完成。")
