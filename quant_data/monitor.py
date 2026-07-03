
import time
import pandas as pd
from sqlalchemy import text
from vnpy.trader.database import get_database
import sys

def monitor_remote_db():
    print("🚀 [Monitor] 正在连接远程数据库监控数据流入情况...")
    try:
        db = get_database()
        sql = text("SELECT count(*) FROM dbbardata;")
        
        # 获取初始行数
        with db.engine.connect() as conn:
            initial_count = conn.execute(sql).fetchone()[0]
            print(f"📈 初始行数: {initial_count}")
            
            while True:
                time.sleep(5)
                current_count = conn.execute(sql).fetchone()[0]
                diff = current_count - initial_count
                print(f"⏰ {time.strftime('%H:%M:%S')} | 总行数: {current_count} | 新流入: +{diff}")
                sys.stdout.flush()
                
    except Exception as e:
        print(f"❌ 监控失败 (可能表还没建立或连接断开): {e}")

if __name__ == "__main__":
    monitor_remote_db()
