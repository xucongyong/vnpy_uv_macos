"""新策略脚手架: 一行命令生成一个可运行的 CTA 策略文件。

用法:
    python scripts/new_strategy.py --name rsi_momentum --kind ma
    python scripts/new_strategy.py --name my_idea --kind template
    python scripts/new_strategy.py --list

生成文件:
    strategies/daily_YYYYMMDD_<name>.py

生成后直接回测:
    python run_backtest.py --strategy Daily... --symbol 00700.SEHK
"""

import argparse
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.strategy_templates import TEMPLATES, build_template

STRATEGY_DIR = Path(__file__).resolve().parent.parent / "strategies"
AUTHOR_DEFAULT = "quant-daily"


def to_filename(name: str) -> str:
    return name.lower().replace(" ", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成每日 CTA 策略脚手架")
    parser.add_argument("--name", required=True, help="策略名, 如 rsi_momentum")
    parser.add_argument("--kind", default="template", choices=list(TEMPLATES.keys()),
                        help="模板类型: " + ", ".join(f"{k}({v['help']})" for k, v in TEMPLATES.items()))
    parser.add_argument("--author", default=AUTHOR_DEFAULT, help="作者名")
    parser.add_argument("--date", default=None, help="日期 YYYY-MM-DD, 默认今天")
    parser.add_argument("--list", action="store_true", help="列出所有可用模板")
    args = parser.parse_args()

    if args.list:
        print("可用模板:")
        for k, v in TEMPLATES.items():
            print(f"  {k:<10} {v['help']}")
        return

    date_str = args.date or datetime.date.today().strftime("%Y-%m-%d")
    name = to_filename(args.name)

    if name in ("daily", "strategy"):
        print(f"❌ 策略名 '{name}' 太笼统, 请起个有辨识度的名字")
        sys.exit(1)

    filename = f"daily_{date_str.replace('-', '')}_{name}.py"
    target = STRATEGY_DIR / filename

    if target.exists():
        print(f"❌ 文件已存在: {target}")
        sys.exit(1)

    source = build_template(args.kind, date_str, name, args.author)

    STRATEGY_DIR.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")

    camel = "".join(p.capitalize() for p in name.split("_"))
    print(f"✅ 策略已生成: {target}")
    print(f"   类名: {camel}Strategy")
    print()
    print("下一步, 直接回测:")
    print(f"   python run_backtest.py --strategy {camel} --symbol 00700.SEHK --start 2022-01-01")
    print()
    print("或用模板覆盖参数:")
    print(f"   python run_backtest.py --strategy {camel} --symbol AAPL.NASDAQ "
          f"--params fast_window=5,slow_window=20,fixed_size=500")


if __name__ == "__main__":
    main()
