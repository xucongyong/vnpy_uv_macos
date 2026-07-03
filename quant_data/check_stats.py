
import psycopg2
import sys

def check_database_stats():
    print("📊 [DatabaseStats] 正在直接连接 PostgreSQL 读取存储统计...")
    
    # 连接配置
    params = {
        "host": "v.xucongyong.com",
        "port": 5432,
        "user": "postgres",
        "password": "1121hotsren",
        "dbname": "postgres"
    }
    
    try:
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        
        # 1. 统计表信息
        sql = """
            SELECT 
                count(*) AS total_rows,
                pg_size_pretty(pg_total_relation_size('quant_data.dbbardata')) AS total_size,
                pg_size_pretty(pg_relation_size('quant_data.dbbardata')) AS table_size,
                pg_size_pretty(pg_total_relation_size('quant_data.dbbardata') - pg_relation_size('quant_data.dbbardata')) AS index_size
            FROM quant_data.dbbardata;
        """
        
        # 2. 统计库信息
        db_sql = "SELECT pg_size_pretty(pg_database_size('postgres'));"
        
        print("-" * 50)
        
        # 执行表统计
        try:
            cur.execute(sql)
            stats = cur.fetchone()
            print(f"📈 行情总行数: {stats[0]:,}")
            print(f"💾 表物理占用: {stats[2]}")
            print(f"🔍 索引占用:   {stats[3]}")
            print(f"📦 总计占用:   {stats[1]} (含索引)")
        except Exception:
            print("⚠️ 未发现行情表，可能尚未开始同步。")
            
        # 执行库统计
        cur.execute(db_sql)
        db_size = cur.fetchone()[0]
        print(f"🌐 数据库总大小: {db_size}")
        
        print("-" * 50)
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ 连接数据库失败: {e}")

if __name__ == "__main__":
    check_database_stats()
