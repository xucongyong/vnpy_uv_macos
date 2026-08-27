#!/usr/bin/env bash
# 服务器端一键配置 (uv 版): 补依赖 + 打 vnpy 补丁 + 验证连库 + 加 cron
#
# 用法(在项目根目录):
#   bash deploy/setup_server.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT="$(pwd)"
echo "📁 项目目录: $PROJECT"

# 1. 找 uv / python
if command -v uv >/dev/null 2>&1; then
  echo "✅ 检测到 uv"
  VENV_PY="$PROJECT/.venv/bin/python"

  if [ ! -x "$VENV_PY" ]; then
    echo "⚠️  项目里还没有 .venv, 先执行: uv sync  然后重跑本脚本"
    exit 1
  fi

  # 确保关键依赖在 (完整输出, 不吞错)
  echo ""
  echo "--- 确保依赖 (uv pip install) ---"
  uv pip install --python "$VENV_PY" \
    vnpy-postgresql vnpy-ctastrategy vnpy-sqlite \
    akshare pandas numpy ta-lib importlib-metadata \
    psycopg2-binary tzlocal plotly deap pyzmq loguru tqdm
  PY="$VENV_PY"
else
  # 没有 uv, 退回直接找 python
  if [ -x "$PROJECT/.venv/bin/python" ]; then
    PY="$PROJECT/.venv/bin/python"
  elif command -v python3 >/dev/null 2>&1; then
    PY="$(command -v python3)"
  else
    echo "❌ 找不到 uv 也找不到 python。先装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
  fi
fi
echo "🐍 使用 Python: $PY"

# 2. 配置 vnpy 配置到 ~/.vntrader/ (vnpy 只从这里读 vt_setting.json)
echo ""
echo "--- 配置 vnpy (~/.vntrader/vt_setting.json) ---"
mkdir -p ~/.vntrader
if [ -f "$PROJECT/vt_setting.json" ]; then
  cp "$PROJECT/vt_setting.json" ~/.vntrader/vt_setting.json
  echo "✅ 已把项目配置复制到 ~/.vntrader/vt_setting.json"
else
  cat > ~/.vntrader/vt_setting.json << 'EOF'
{
    "database.name": "postgresql",
    "database.database": "quant",
    "database.host": "v.xucongyong.com",
    "database.port": 5432,
    "database.user": "postgres",
    "database.password": "1121hotsren",
    "database.timezone": "Asia/Shanghai"
}
EOF
  echo "✅ 已生成默认配置到 ~/.vntrader/vt_setting.json"
fi

# 3. 打 vnpy_postgresql 驱动补丁 (表名 quant_data/quant_data_sync)
echo ""
echo "--- 打 vnpy_postgresql 补丁 ---"
"$PY" deploy/patch_vnpy_postgresql.py

# 4. 验证数据库连接
echo ""
echo "--- 验证数据库连接 ---"
"$PY" -c "from vnpy.trader.database import get_database; d=get_database(); print('✅ 连接OK, 共', len(d.get_bar_overview()), '个标的')"

# 5. 加 cron 每日任务 (周一~五 16:30), 日志放 ~/.logs/
echo ""
echo "--- 配置 cron 每日任务 ---"
mkdir -p ~/.logs
CRON_LINE="30 16 * * 1-5 cd $PROJECT && $PY daily.py >> $HOME/.logs/daily.log 2>&1"
( crontab -l 2>/dev/null | grep -v "daily.py" ; echo "$CRON_LINE" ) | crontab -
echo "✅ cron 已加入:"
crontab -l | grep "daily.py"
echo "日志位置: $HOME/.logs/daily.log"

echo ""
echo "=================================================="
echo "完成! 接下来手动验证一次:"
echo "  $PY daily.py"
echo "查看自动日志:"
echo "  tail -f $PROJECT/logs/daily.log"
echo "改运行时间: crontab -e (把 30 16 改成你要的时间)"
echo "=================================================="
