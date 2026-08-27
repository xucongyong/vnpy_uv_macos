"""演示: 数据存在哪里? 就在这个数据库里, 回测也读它。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "vnpy_futu"))
from datetime import datetime
from vnpy.trader.database import get_database
from vnpy.trader.constant import Interval, Exchange

db = get_database()

# ===== 看数据: 行情存这里(akshare同步时调用 db.save_bar_data 存进来的) =====
bars = db.load_bar_data("00700", Exchange.SEHK, Interval.DAILY,
                        datetime(2026, 1, 1), datetime(2026, 6, 11))
print(f"📦 数据库里腾讯 00700 有 {len(bars)} 根K线 (2026年)")
print(f"   最新一根: {bars[-1].datetime.date()}  收盘价 {bars[-1].close_price}")

# ===== 看数据库里总共有什么 =====
ov = db.get_bar_overview()
print(f"\n📦 整个数据库共有 {len(ov)} 个标的")
