
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import BarData
from vnpy.trader.database import get_database
import time

# ==========================================
# 配置区域
# ==========================================
# 如果你已经配置了 vt_setting.json，vn.py 会自动读取。
# 这里我们定义一个列表，存放你需要关注的股票代码
SYMBOLS = ["000001", "600036", "600519", "000858"]  # 示例：平安银行、招商银行、贵州茅台、五粮液

def get_exchange(symbol: str) -> Exchange:
    """根据代码判断交易所"""
    if symbol.startswith("6"):
        return Exchange.SSE
    else:
        return Exchange.SZSE

def sync_data():
    """
    每日同步脚本核心逻辑
    """
    db = get_database()
    
    print(f"🔔 开始同步任务: {datetime.now()}")
    
    for symbol in SYMBOLS:
        try:
            exchange = get_exchange(symbol)
            
            # 1. 检查数据库中已有的最后一条数据时间，实现增量更新
            # 注意：vn.py 存储 bar 数据的表名通常是 dbbardata
            # 这里我们通过 get_database().load_bar_data 来判断，或者直接查最新日期
            
            # 简单起见，我们默认更新过去 30 天的数据（自动去重）
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
            
            print(f"🔍 正在同步 {symbol} ({exchange.value})...")
            
            # 2. 从 AkShare 下载
            df = ak.stock_zh_a_hist(
                symbol=symbol, 
                period="daily", 
                start_date=start_date, 
                adjust="qfq"
            )
            
            if df.empty:
                print(f"⚠️ {symbol} 未找到新数据")
                continue

            # 3. 转化为 BarData
            bars = []
            for _, row in df.iterrows():
                dt = pd.to_datetime(row["日期"])
                
                # vn.py 会根据 (symbol, exchange, interval, datetime) 自动处理重复，所以放心 save
                bar = BarData(
                    symbol=symbol,
                    exchange=exchange,
                    datetime=dt,
                    interval=Interval.DAILY,
                    open_price=float(row["开盘"]),
                    high_price=float(row["最高"]),
                    low_price=float(row["最低"]),
                    close_price=float(row["收盘"]),
                    volume=float(row["成交量"]),
                    gateway_name="AKSHARE"
                )
                bars.append(bar)
            
            # 4. 保存到数据库
            db.save_bar_data(bars)
            print(f"✅ {symbol} 同步完成，导入 {len(bars)} 条记录")
            
            # 5. 稍微停顿，防止请求过快被封
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ 同步 {symbol} 出错: {e}")

if __name__ == "__main__":
    # 如果是第一次运行，建议手动修改 start_date 下载过去 10 年的数据
    # 之后每天运行只需同步最近数据即可
    sync_data()
