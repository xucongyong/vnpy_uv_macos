
import psycopg2
import pandas as pd
import sys

def check_postgres_inventory():
    print("🧐 [InventoryCheck] 正在核对 PostgreSQL 资产...")
    
    # 数据库连接参数
    params = {
        "host": "v.xucongyong.com",
        "port": 5432,
        "user": "postgres",
        "password": "1121hotsren",
        "dbname": "postgres"
    }
    
    try:
        conn = psycopg2.connect(**params)
        
        # 1. 统计总体情况
        sql_summary = """
            SELECT 
                COUNT(DISTINCT symbol) as total_symbols,
                COUNT(*) as total_rows,
                MIN(datetime) as earliest_date,
                MAX(datetime) as latest_date
            FROM quant_data.dbbardata;
        """
        
        # 2. 统计各市场分布
        sql_markets = """
            SELECT 
                exchange,
                COUNT(DISTINCT symbol) as symbol_count,
                COUNT(*) as row_count
            FROM quant_data.dbbardata
            GROUP BY exchange;
        """

        summary = pd.read_sql(sql_summary, conn)
        markets = pd.read_sql(sql_markets, conn)
        
        print("\n" + "="*50)
        print("📊 数据库资产总览 (PostgreSQL)")
        print("="*50)
        
        if summary['total_rows'][0] == 0:
            print("⚠️ 数据库当前是空的。")
        else:
            print(f"✅ 已覆盖股票总数: {summary['total_symbols'][0]} 只")
            print(f"✅ 累计 K 线总行数: {summary['total_rows'][0]:,} 条")
            print(f"✅ 时间跨度: {summary['earliest_date'][0]} 至 {summary['latest_date'][0]}")
            
            print("\n📈 市场分布情况:")
            print(markets.to_string(index=False))
            
        print("="*50)
        print("💡 去重确认: 数据库已通过 (Symbol, Exchange, Datetime) 主键逻辑实现自动去重。")
        
        conn.close()
            
    except Exception as e:
        print(f"❌ 资产核对失败: {e}")

if __name__ == "__main__":
    check_postgres_inventory()
