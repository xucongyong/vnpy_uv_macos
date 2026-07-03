
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_schema():
    host = "v.xucongyong.com"
    user = "postgres"
    password = "1121hotsren"
    dbname = "postgres"
    schema = "quant_data"

    print(f"🚀 [InitSchema] 正在连接 {host} 的 {dbname} 数据库...")
    
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname=dbname
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # 1. 创建模式 (Schema)
        print(f"🛠️  正在创建模式: {schema}...")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        
        # 2. 将该用户的搜索路径默认指向该模式
        print(f"🔗 正在将用户 {user} 的 search_path 指向 {schema}...")
        cur.execute(f"ALTER USER {user} SET search_path TO {schema}, public;")
        
        print(f"✅ [InitSchema] 模式初始化完成！数据现在将存入 {schema}.dbbardata")

        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ [InitSchema] 出错: {e}")

if __name__ == "__main__":
    init_schema()
