
import akshare as ak
import pandas as pd
from datetime import datetime
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
from vnpy.trader.database import get_database
import time
import sys

# 版本标识
VERSION = "1.1.0-SmartSync"

class ProductionDownloader:
    def __init__(self):
        print(f"🚀 [Production] 正在初始化智能同步程序 (版本: {VERSION})...")
        try:
            self.db = get_database()
            # 预先获取数据库中已有的股票列表，实现“已下载跳过”
            overviews = self.db.get_bar_overview()
            self.existing_symbols = {ov.symbol for ov in overviews}
            print(f"ℹ️  数据库中已存在 {len(self.existing_symbols)} 只股票的数据。")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            sys.exit(1)

    def get_sina_symbol(self, code):
        """智能判断 A 股前缀"""
        if code.startswith(('60', '68', '90')):
            return "sh" + code, Exchange.SSE
        elif code.startswith(('00', '30', '20')):
            return "sz" + code, Exchange.SZSE
        elif code.startswith(('8', '43', '92')):
            return "bj" + code, Exchange.BSE # 北交所
        else:
            return "sh" + code, Exchange.SSE # 默认上海

    def safe_float(self, value):
        if value is None or value == "" or pd.isna(value): return 0.0
        try: return float(value)
        except: return 0.0

    def save_bars(self, symbol, exchange, df):
        if df is None or df.empty: return
        bars = []
        for _, row in df.iterrows():
            dt = pd.to_datetime(row.get("date") or row.get("日期"))
            if dt.tzinfo is not None: dt = dt.tz_convert(None)
            
            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                datetime=dt.to_pydatetime(),
                interval=Interval.DAILY,
                open_price=self.safe_float(row.get("open") or row.get("开盘")),
                high_price=self.safe_float(row.get("high") or row.get("最高")),
                low_price=self.safe_float(row.get("low") or row.get("最低")),
                close_price=self.safe_float(row.get("close") or row.get("收盘")),
                volume=self.safe_float(row.get("volume") or row.get("成交量")),
                gateway_name="SINA"
            )
            bars.append(bar)
        self.db.save_bar_data(bars)

    def fetch_list_with_retry(self, fetch_func, max_retries=5):
        """专门为获取股票列表增加的重试逻辑"""
        for i in range(max_retries):
            try:
                return fetch_func()
            except Exception as e:
                wait_time = (i + 1) * 5
                print(f"  ⚠️ 获取列表失败 ({e})，正在进行第 {i+1} 次重试，等待 {wait_time} 秒...")
                time.sleep(wait_time)
        return None

    def sync_a_shares(self):
        print("🇨🇳 [A-Share] 正在扫描 A 股全市场...")
        stocks = self.fetch_list_with_retry(ak.stock_zh_a_spot_em)
        if stocks is None:
            print("❌ 无法获取 A 股代码列表，请尝试更换网络（如手机热点）或检查 AkShare 版本。")
            return
            
        codes = stocks['代码'].tolist()
        
        # 过滤掉已存在的
        target_codes = [c for code in codes if (c := str(code)) not in self.existing_symbols]
        print(f"📊 总共 {len(codes)} 只股票，待同步 {len(target_codes)} 只。")

        for i, code in enumerate(target_codes):
            try:
                sina_symbol, exchange = self.get_sina_symbol(code)
                print(f"[{i+1}/{len(target_codes)}] 正在同步 {code} ({exchange.value})...")
                df = ak.stock_zh_a_daily(symbol=sina_symbol, adjust="qfq")
                self.save_bars(code, exchange, df)
                time.sleep(0.05)
            except Exception as e:
                print(f"  ⚠️ {code} 同步失败: {e}")

    def sync_hk_shares(self):
        print("🇭🇰 [HK-Share] 正在同步港股核心标的...")
        stocks = ak.stock_hk_spot_em()
        codes = stocks['代码'].tolist()
        target_codes = [c for c in codes if c not in self.existing_symbols]
        
        for i, code in enumerate(target_codes):
            try:
                print(f"[{i+1}/{len(target_codes)}] 正在同步港股: {code}")
                df = ak.stock_hk_daily(symbol=code, adjust="qfq")
                self.save_bars(code, Exchange.SEHK, df)
                time.sleep(0.05)
            except Exception as e:
                print(f"  ⚠️ HK.{code} 失败: {e}")

    def sync_us_shares(self):
        print("🇺🇸 [US-Share] 正在同步美股核心标的...")
        stocks = ak.stock_us_spot_em()
        # 清洗美股代码，去掉东方财富的交易所前缀 (例如 '105.AAPL' -> 'AAPL')
        stocks['clean_code'] = stocks['代码'].apply(lambda x: str(x).split('.')[-1] if '.' in str(x) else str(x))
        
        target_rows = stocks[~stocks['clean_code'].isin(self.existing_symbols)]
        
        for i, (_, row) in enumerate(target_rows.iterrows()):
            raw_code = row['代码']
            clean_code = row['clean_code']
            try:
                print(f"[{i+1}/{len(target_rows)}] 正在同步美股: {clean_code} (原代码: {raw_code})")
                df = ak.stock_us_daily(symbol=clean_code, adjust="qfq")
                self.save_bars(clean_code, Exchange.NASDAQ, df)
                time.sleep(0.05)
            except Exception as e:
                print(f"  ⚠️ US.{clean_code} 失败: {e}")

if __name__ == "__main__":
    downloader = ProductionDownloader()
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    if arg in ["a", "all"]: downloader.sync_a_shares()
    if arg in ["hk", "all"]: downloader.sync_hk_shares()
    if arg in ["us", "all"]: downloader.sync_us_shares()
    
    print("\n🎉 同步任务圆满完成！")
