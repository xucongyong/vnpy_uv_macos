
import json
import os
import psycopg2
from vnpy.trader.utility import get_file_path
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 1. 核心配置定义
host = "v.xucongyong.com"
user = "postgres"
password = "1121hotsren"
dbname = "postgres"
schema = "quant_data"

config = {
    "font.family": "微软雅黑",
    "font.size": 12,
    "log.active": True,
    "log.level": 20,
    "log.console": True,
    "log.file": True,
    "database.name": "postgresql",
    "database.database": dbname, # 数据库必须是 postgres
    "database.host": host,
    "database.port": 5432,
    "database.user": user,
    "database.password": password,
    "database.timezone": "Asia/Shanghai"
}

def setup_all():
    print(f"🛠️ [Setup] 正在修复配置并初始化 Schema...")
    
    # A. 写入配置文件
    paths = [get_file_path("vt_setting.json"), "vt_setting.json"]
    for p in paths:
        os.makedirs(os.path.dirname(p), exist_ok=True) if os.path.dirname(p) else None
        with open(p, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print(f"   ✅ 已写入配置: {p}")

    # B. 初始化数据库 Schema
    try:
        conn = psycopg2.connect(host=host, user=user, password=password, dbname=dbname)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        print(f"   🏗️  正在创建 Schema '{schema}' 并锁定 search_path...")
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        cur.execute(f"ALTER USER {user} SET search_path TO {schema}, public;")
        
        cur.close()
        conn.close()
        print(f"✅ [Setup] 全部完成！现在数据将存入: {dbname}.{schema}")
        
    except Exception as e:
        print(f"❌ [Setup] 数据库操作失败: {e}")

if __name__ == "__main__":
    setup_all()
