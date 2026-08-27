"""一键给 vnpy_postgresql 驱动打补丁 (幂等, 可重复跑)。

补丁内容:
  1. 表名: dbbardata → quant_data, dbbaroverview → quant_data_sync
  2. create_tables 只建 [DbBarData, DbBarOverview], 不再自动建 tick 空表

用法:
    python deploy/patch_vnpy_postgresql.py                       # 自动定位已安装的驱动
    python deploy/patch_vnpy_postgresql.py /path/to/postgresql_database.py  # 指定文件(测试用)
"""

import pathlib
import sys

# 确保项目根目录可导入 (否则从 deploy/ 跑时找不到 vnpy)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def apply_patch(target: pathlib.Path) -> None:
    src = target.read_text(encoding="utf-8")

    if 'table_name: str = "quant_data"' in src:
        print(f"✅ 已打过补丁, 无需重复: {target}")
        return

    replaces = [
        # 1. DbBarData 表名 (唯一索引行特征)
        (
            'indexes: tuple = ((("symbol", "exchange", "interval", "datetime"), True),)',
            'table_name: str = "quant_data"\n        indexes: tuple = ((("symbol", "exchange", "interval", "datetime"), True),)',
            "DbBarData 表名",
        ),
        # 2. DbBarOverview 表名
        (
            'indexes: tuple = ((("symbol", "exchange", "interval"), True),)',
            'table_name: str = "quant_data_sync"\n        indexes: tuple = ((("symbol", "exchange", "interval"), True),)',
            "DbBarOverview 表名",
        ),
        # 3. 只建两张表
        (
            "self.db.create_tables([DbBarData, DbTickData, DbBarOverview, DbTickOverview])",
            "self.db.create_tables([DbBarData, DbBarOverview])",
            "create_tables 只建两张表",
        ),
    ]

    missing = []
    for old, new, label in replaces:
        if old in src:
            src = src.replace(old, new)
            print(f"  ✓ {label}")
        else:
            missing.append(label)

    if missing:
        print(f"⚠️  未匹配到: {', '.join(missing)}。版本可能不同, 请人工确认。")
        print(f"   目标文件: {target}")

    target.write_text(src, encoding="utf-8")
    print(f"✅ 补丁已应用: {target}")


def main() -> None:
    if len(sys.argv) > 1:
        apply_patch(pathlib.Path(sys.argv[1]))
        return

    try:
        import vnpy_postgresql
    except Exception as e:
        print(f"❌ 导入 vnpy_postgresql 失败: {type(e).__name__}: {e}")
        print("   通常是缺依赖, 试: uv pip install peewee tzlocal importlib-metadata ta-lib --python .venv/bin/python")
        sys.exit(1)

    target = pathlib.Path(vnpy_postgresql.__file__).parent / "postgresql_database.py"
    if not target.exists():
        print(f"❌ 找不到驱动文件: {target}")
        sys.exit(1)
    apply_patch(target)


if __name__ == "__main__":
    main()
