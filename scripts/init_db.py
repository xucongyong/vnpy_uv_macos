
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_quant_db():
    # 连接到默认的 postgres 数据库来创建新数据库
    host = "100.66.3.3"
    user = "postgres"
    password = "1121hotsren"
    dbname = "quant"

    try:
        # 首先尝试连接
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # 检查数据库是否存在
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"🚀 正在创建数据库: {dbname}...")
            cur.execute(f"CREATE DATABASE {dbname}")
            print(f"✅ 数据库 {dbname} 创建成功！")
        else:
            print(f"ℹ️ 数据库 {dbname} 已存在，无需创建。")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        print("提示: 请确保 100.66.3.3 允许远程连接，并且防火墙已开放 5432 端口。")

if __name__ == "__main__":
    create_quant_db()
