
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta, date
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
import time
import sys

# 【关键改动】直接导入 PostgreSQL 数据库类，绕过配置文件
try:
    from vnpy_postgresql.postgresql_database import Database
except ImportError:
    print("❌ 错误：检测到 uv 环境中缺少 vnpy_postgresql 驱动！")
    print("💡 请执行：uv pip install vnpy-postgresql psycopg2-binary")
    sys.exit(1)

# 版本标识
VERSION = "1.0.9-HardLink-PostgreSQL"

class HardLinkDownloader:
    def __init__(self):
        print(f"🚀 [HardLink] 正在直接连接 v.xucongyong.com (不依赖配置)...")
        # 直接实例化数据库对象
        try:
            self.db = Database()
            # 强行设置连接属性（内部 hack）
            from vnpy.trader.setting import SETTINGS
            SETTINGS["database.name"] = "postgresql"
            SETTINGS["database.database"] = "postgres"
            SETTINGS["database.host"] = "v.xucongyong.com"
            SETTINGS["database.user"] = "postgres"
            SETTINGS["database.password"] = "1121hotsren"
            # 重新初始化连接
            self.db.init()
            print("✅ 远程 PostgreSQL 硬连接成功！")
        except Exception as e:
            print(f"❌ 硬连接失败: {e}")
            sys.exit(1)
        
    def safe_float(self, value):
        if value is None or value == "" or pd.isna(value): return 0.0
        try: return float(value)
        except: return 0.0

    def sync_stock(self, name, symbol, mkt, ex):
        print(f"📥 正在抓取 {name} ({symbol})...")
        try:
            if mkt == "A":
                df = ak.stock_zh_a_daily(symbol=symbol, adjust="qfq")
                vn_code = symbol[2:]
            elif mkt == "HK":
                df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
                vn_code = symbol
            else:
                df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
                vn_code = symbol

            bars = []
            for _, row in df.iterrows():
                dt = pd.to_datetime(row.get("date") or row.get("日期"))
                if dt.tzinfo is not None: dt = dt.tz_convert(None)
                
                bar = BarData(
                    symbol=vn_code,
                    exchange=getattr(Exchange, ex),
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
            print(f"   ✅ {name} 存入成功: {len(bars)} 行")
        except Exception as e:
            print(f"   ❌ {name} 出错: {e}")

if __name__ == "__main__":
    # 强制执行驱动安装检查
    print(f"--- 诊断开始 (版本: {VERSION}) ---")
    
    downloader = HardLinkDownloader()
    
    samples = [
        {"symbol": "sz000001", "name": "平安银行", "mkt": "A", "ex": "SZSE"},
        {"symbol": "00700", "name": "腾讯控股", "mkt": "HK", "ex": "SEHK"},
        {"symbol": "AAPL", "name": "苹果公司", "mkt": "US", "ex": "NASDAQ"}
    ]

    for s in samples:
        downloader.sync_stock(s['name'], s['symbol'], s['mkt'], s['ex'])

    print("\n🎉 任务完成！请去 v.xucongyong.com 的 postgres 库中查看数据。")
