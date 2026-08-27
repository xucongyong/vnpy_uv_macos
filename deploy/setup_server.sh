#!/usr/bin/env bash
# 服务器端一键配置: 打 vnpy 驱动补丁 + 验证连库 + 加 cron 每日任务
#
# 用法(在项目根目录下):
#   bash deploy/setup_server.sh                     # 自动找 python
#   bash deploy/setup_server.sh /usr/bin/python3     # 指定 python
set -e
cd "$(dirname "$0")/.."
PROJECT="$(pwd)"
echo "📁 项目目录: $PROJECT"

# 1. 找 python
if [ -n "$1" ]; then
  PY="$1"
elif [ -x "$PROJECT/.venv/bin/python" ]; then
  PY="$PROJECT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PY="$(command -v python)"
else
  echo "❌ 找不到 python。用法: bash deploy/setup_server.sh /路径/到/python"
  exit 1
fi
echo "🐍 使用 Python: $PY"

# 2. 打 vnpy 驱动补丁 (表名 quant_data/quant_data_sync)
echo ""
echo "--- 打 vnpy_postgresql 补丁 ---"
"$PY" deploy/patch_vnpy_postgresql.py

# 3. 验证能连数据库
echo ""
echo "--- 验证数据库连接 ---"
"$PY" -c "from vnpy.trader.database import get_database; d=get_database(); print('✅ 数据库连接OK, 共', len(d.get_bar_overview()), '个标的')"

# 4. 加 cron 每日任务 (每周一~五 16:30)
echo ""
echo "--- 配置 cron 每日任务 ---"
mkdir -p "$PROJECT/logs"
CRON_LINE="30 16 * * 1-5 cd $PROJECT && $PY daily.py >> $PROJECT/logs/daily.log 2>&1"
( crontab -l 2>/dev/null | grep -v "daily.py" ; echo "$CRON_LINE" ) | crontab -
echo "✅ 已加入 cron:"
crontab -l | grep "daily.py" || echo "⚠️  未找到, 请人工确认 crontab"

echo ""
echo "=================================================="
echo "完成! 接下来:"
echo "  1. 手动跑一次验证:   $PY daily.py"
echo "  2. 看日志:           tail -f $PROJECT/logs/daily.log"
echo "  3. 改时间:           crontab -e  (第2行改 30 16 为你想要的时间)"
echo "=================================================="
