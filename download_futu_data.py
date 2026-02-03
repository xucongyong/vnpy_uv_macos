import sys
import os
from datetime import datetime
from time import sleep

# 将当前目录加入系统路径，确保能找到 vnpy_futu
sys.path.append(os.getcwd())

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.constant import Interval, Exchange
from vnpy.trader.object import HistoryRequest
from vnpy.trader.database import get_database

# 尝试导入 FutuGateway
try:
    from vnpy_futu import FutuGateway
except ImportError:
    # 如果没安装，尝试从本地路径导入
    sys.path.append(os.path.join(os.getcwd(), "vnpy_futu"))
    from vnpy_futu import FutuGateway

def download_data():
    """批量下载数据脚本"""
    
    # 1. 配置参数：要下载的股票列表
    # (代码, 交易所)
    TARGETS = [
        ("00700", Exchange.SEHK),    # 腾讯 (港股)
        ("03690", Exchange.SEHK),    # 美团 (港股)
        # ("00005", Exchange.SEHK),  # 汇丰 (港股)
        ("TSLA", Exchange.NASDAQ),   # 特斯拉 (美股)
        ("AAPL", Exchange.NASDAQ),   # 苹果 (美股)
        ("NVDA", Exchange.NASDAQ),   # 英伟达 (美股)
    ]
    
    START_DATE = datetime(2022, 1, 1)
    END_DATE = datetime.now()
    
    # Futu OpenD 配置
    FUTU_HOST = "127.0.0.1"
    FUTU_PORT = 11111
    FUTU_PWD = "123" 

    # 2. 初始化引擎
    print("正在初始化引擎...")
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(FutuGateway)

    # 3. 连接 Futu
    # 注意：vn.py 的 FutuGateway 连接时主要验证 OpenD 是否通，
    # 填写的 "市场" 参数主要影响订阅，但 query_history 是主动拉取，通常都能通。
    # 我们先用 'HK' 连接。
    print(f"正在连接 Futu OpenD ({FUTU_HOST}:{FUTU_PORT})...")
    main_engine.connect({
        "地址": FUTU_HOST,
        "端口": FUTU_PORT,
        "密码": FUTU_PWD,
        "市场": "HK", 
        "环境": 1     
    })

    sleep(5)
    gateway = main_engine.get_gateway("FUTU")
    if not gateway:
        print("错误：无法获取 Futu Gateway，请检查连接。")
        return

    # 获取数据库管理器
    database = get_database()

    # 4. 循环下载
    for symbol, exchange in TARGETS:
        print("------------------------------------------------")
        print(f"准备下载: {symbol}.{exchange.value}")
        
        req = HistoryRequest(
            symbol=symbol,
            exchange=exchange,
            start=START_DATE,
            end=END_DATE,
            interval=Interval.MINUTE
        )

        try:
            print(f"正在请求数据 ({START_DATE.date()} ~ {END_DATE.date()})...")
            # 调用接口下载
            data = gateway.query_history(req)
            
            if data:
                print(f"下载成功！共 {len(data)} 条数据。")
                print(f"正在写入数据库...")
                database.save_bar_data(data)
                print("写入完成。")
            else:
                print(f"警告：未获取到 {symbol} 的数据。")
                
        except Exception as e:
            print(f"下载 {symbol} 时发生错误: {e}")
        
        # 休息一下，防止触发频率限制
        print("等待 3 秒避免限流...")
        sleep(3)

    print("------------------------------------------------")
    print("所有任务执行完毕！")
    main_engine.close()
    sys.exit(0)

if __name__ == "__main__":
    download_data()
