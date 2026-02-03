
import sys
import os
import pandas as pd
from datetime import datetime
from time import sleep

# 配置 VNPY 环境
sys.path.append(os.getcwd())
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import HistoryRequest
from vnpy.trader.database import get_database
try:
    from vnpy_futu import FutuGateway
except ImportError:
    print("Error: vnpy_futu not installed")
    sys.exit(1)

def mass_download():
    """读取 csv 文件并批量下载"""

    # === 配置区域 ===
    MARKET = "HK"  
    # 港股全明星列表：波动大，趋势强
    STAR_STOCKS = [
        ("00700", Exchange.SEHK, "腾讯控股"),
        ("09988", Exchange.SEHK, "阿里巴巴-W"),
        ("03690", Exchange.SEHK, "美团-W"),
        ("01810", Exchange.SEHK, "小米集团-W"),
        ("01024", Exchange.SEHK, "快手-W"),
        ("09888", Exchange.SEHK, "百度集团-SW"),
        ("01211", Exchange.SEHK, "比亚迪股份"),
        ("00981", Exchange.SEHK, "中芯国际"),
        ("02318", Exchange.SEHK, "中国平安"),
        ("03888", Exchange.SEHK, "金山软件"),
    ]
    # =============
    
    # 2. 初始化引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(FutuGateway)
    gateway = main_engine.get_gateway("FUTU")

    print("连接 OpenD (港股全明星模式)...")
    gateway.connect({
        "地址": "127.0.0.1",
        "端口": 11111,
        "密码": "123",
        "市场": MARKET, 
        "环境": 1
    })
    sleep(5)
    database = get_database()

    # 3. 循环下载
    success_count = 0
    start_date = datetime(2023, 1, 1) 
    end_date = datetime.now()

    for i, (symbol, exchange, name) in enumerate(STAR_STOCKS):
        print(f"[{i+1}/{len(STAR_STOCKS)}] 正在下载 {name} ({symbol}.{exchange.value})...")

        req = HistoryRequest(
            symbol=symbol,
            exchange=exchange,
            start=start_date,
            end=end_date,
            interval=Interval.MINUTE
        )

        try:
            data = gateway.query_history(req)
            if data:
                database.save_bar_data(data)
                print(f"  -> 成功：{len(data)} 条")
                success_count += 1
            else:
                print("  -> 无数据（请检查该股票权限）")
        except Exception as e:
            print(f"  -> 错误: {e}")

        sleep(3) 

    print(f"\n全部完成！成功下载 {success_count} 只港股大鱼数据。")
    main_engine.close()
    sys.exit(0)

if __name__ == "__main__":
    mass_download()
