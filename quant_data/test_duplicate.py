
from vnpy.trader.database import get_database
from vnpy.trader.object import BarData
from vnpy.trader.constant import Exchange, Interval
from datetime import datetime
import time

def test_deduplication():
    print("🧪 [DedupTest] 正在测试 PostgreSQL 去重能力...")
    try:
        db = get_database()
        
        # 定义测试常量
        symbol = "TEST_DEDUP"
        exchange = Exchange.LOCAL
        interval = Interval.DAILY
        dt = datetime(2025, 1, 1)

        # 1. 构造第一条测试数据
        bar1 = BarData(
            symbol=symbol,
            exchange=exchange,
            datetime=dt,
            interval=interval,
            open_price=100.0,
            high_price=110.0,
            low_price=90.0,
            close_price=105.0,
            volume=1000,
            gateway_name="TEST"
        )
        
        print("   -> 尝试第一次保存 (价格: 105.0)...")
        db.save_bar_data([bar1])
        
        # 2. 构造第二条测试数据（相同主键，不同收盘价）
        bar2 = BarData(
            symbol=symbol,
            exchange=exchange,
            datetime=dt,
            interval=interval,
            open_price=100.0,
            high_price=110.0,
            low_price=90.0,
            close_price=106.0, # 修改价格
            volume=1000,
            gateway_name="TEST"
        )
        
        print("   -> 尝试第二次保存 (价格: 106.0)...")
        db.save_bar_data([bar2])
        
        # 3. 验证结果
        print("   🔍 正在从数据库回读...")
        bars = db.load_bar_data(symbol, exchange, interval, datetime(2024,12,31), datetime(2025,1,2))
        
        if len(bars) == 1:
            print(f"✅ 去重测试成功！")
            print(f"   数据库行数: {len(bars)} (符合预期)")
            print(f"   最终收盘价: {bars[0].close_price} (预期 106.0)")
        else:
            print(f"❌ 去重测试失败！数据库中出现了 {len(bars)} 条重复记录。")
            
    except Exception as e:
        import traceback
        print(f"❌ 测试过程中发生异常:")
        traceback.print_exc()

if __name__ == "__main__":
    test_deduplication()
