
import pandas as pd
from sqlalchemy import text
from vnpy.trader.database import get_database
import os

def export_samples_to_csv():
    print("📤 [Export] 正在从远程数据库提取数据...")
    try:
        db = get_database()
        # 获取当前库中所有的股票代码
        sql_symbols = text("SELECT DISTINCT symbol FROM dbbardata;")
        
        with db.engine.connect() as conn:
            symbols = [row[0] for row in conn.execute(sql_symbols).fetchall()]
            
            if not symbols:
                print("⚠️ 数据库里没货，请先运行 size_test.py 下载数据。")
                return

            for symbol in symbols:
                print(f"   -> 导出 {symbol}...")
                # 读取该股票全部历史
                sql_data = text(f"SELECT * FROM dbbardata WHERE symbol = '{symbol}' ORDER BY datetime ASC")
                df = pd.read_sql(sql_data, conn)
                
                # 保存到本地 quant_data 目录
                file_name = f"quant_data/{symbol}_history.csv"
                df.to_csv(file_name, index=False)
                print(f"   ✅ 已保存: {file_name}")
                
        print("\n🎉 导出完成！你现在可以在 quant_data 文件夹下直接用 Excel 打开这些 CSV 文件了。")
        
    except Exception as e:
        print(f"❌ 导出失败: {e}")

if __name__ == "__main__":
    export_samples_to_csv()
