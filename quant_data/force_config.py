
import json
import os
from vnpy.trader.utility import get_file_path

# 配置：数据库为 postgres，模式通过 init_db.py 在服务端锁定
config = {
    "font.family": "微软雅黑",
    "font.size": 12,
    "log.active": True,
    "log.level": 20,
    "log.console": True,
    "log.file": True,
    "database.name": "postgresql",
    "database.database": "postgres", # 数据库依然是 postgres
    "database.host": "v.xucongyong.com",
    "database.port": 5432,
    "database.user": "postgres",
    "database.password": "1121hotsren",
    "database.timezone": "Asia/Shanghai"
}

def force_fix():
    print("🛠️ [ForceConfig] 正在修正配置...")
    target_path = get_file_path("vt_setting.json")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    with open("vt_setting.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    print(f"✅ 配置已更新。")

if __name__ == "__main__":
    force_fix()
