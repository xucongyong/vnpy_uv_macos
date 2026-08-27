# AGENTS.md — quant 项目工作流

VeighNa (vn.py) 量化交易框架 + 自定义工作区。数据存在远程 PostgreSQL (`v.xucongyong.com`, 见 `vt_setting.json`)。

## 运行环境

- Python 解释器: `.venv/bin/python` (本目录的 venv)
- 勿用系统 python。所有命令用 `.venv/bin/python xxx.py`
- 格式/检查: `.venv/bin/ruff check .` (先装: `.venv/bin/python -m pip install ruff`)

## 每日策略工作流 (核心)

### 1. 新建策略 (脚手架)

```
.venv/bin/python scripts/new_strategy.py --name <策略名> --kind <模板>
```

模板 `--kind` 可选:
- `ma`        双均线金叉死叉 (趋势)
- `boll`      布林带均值回归
- `rsi`       RSI 超买超卖
- `momentum`  唐奇安通道突破 (海龟风格)
- `template`  空骨架, 逻辑自己填

生成文件: `strategies/daily_YYYYMMDD_<name>.py`, 类名 `<CamelName>Strategy`。

改模板见 `scripts/strategy_templates.py` (每个 kind 一个 dict: 参数/变量/on_init/on_bar)。

### 2. 单策略回测

```
.venv/bin/python run_backtest.py --strategy <名字> --symbol <SYMBOL.EXCHANGE> [选项]
```

- `--strategy`: 类名或别名 (`XDualMaStrategy` / `dual_ma` / `dualma` 均可, 注册表自动模糊匹配)
- `--symbol`: `00700.SEHK` `AAPL.NASDAQ` `000001.SZSE` (交易所后缀见下)
- `--interval`: `d`(默认) `1m` `1h`
- `--start` `--end`: 日期, 默认近 3 年~今天
- `--params`: 逗号分隔 `k=v` 覆盖策略参数
- `--csv`: 逐日绩效存 `research/reports/`
- `--list`: 列出所有可用策略

市场默认费率/滑点/跳动(可 `--rate/--slippage/--pricetick` 覆盖):
- A股 `SSE/SZSE/BSE`: 万3 / 0.01 / 0.01
- 港股 `SEHK`: 千1.5 / 0.05 / 0.01
- 美股 `NASDAQ/NYSE`: 万5 / 0.01 / 0.01
- BTC `LOCAL`: (DB 无实盘BTC行情, 走 AI 流程, 见下)

### 3. 批量回测对比

```
.venv/bin/python batch_backtest.py \
    --symbols AAPL.NASDAQ,00700.SEHK,000001.SZSE \
    --strategies dual_ma,boll,rsi-fast=5,slow=20
```

结果: 控制台排行榜 + `batch_backtest_results.csv`。

### 4. 每日一条龙 (同步+批量回测+报告)

```
.venv/bin/python daily.py                                                     # 默认名单(内置3只/或watchlist.txt)+默认策略
.venv/bin/python daily.py --symbols 00700.SEHK,AAPL.NASDAQ --strategies dual_ma,boll,rsi
.venv/bin/python daily.py --symbols-file watchlist.txt --start 2024-01-01
```

流程: ①增量同步(秒级) → ②批量回测(名单×策略) → ③排行榜存 `research/reports/daily_*.csv`。

## 行情同步 (数据更新)

```
.venv/bin/python quant_data/sync_full_production.py      # A股+港股+美股 全市场 (增量, 慢, 易封IP)
.venv/bin/python quant_data/daily_sync.py                # 每日增量更新
```

### 推荐: 自选股同步 (快, 增量)

```
.venv/bin/python scripts/save_watchlist.py --symbols 00700.SEHK,AAPL.NASDAQ,000001.SZSE
.venv/bin/python scripts/save_watchlist.py --symbols-file watchlist.txt   # 名单文件, 每行一个
.venv/bin/python scripts/save_watchlist.py --symbols 00700.SEHK --force-full --days 3650  # 强制全量重拉10年
```

- 增量逻辑: 查库里最新K线日期 → 只拉 (最新日期-5天) 到现在; 库里没有则全量拉 `--days` 天
- `db.save_bar_data()` 是 upsert(按 symbol+exchange+interval+datetime 唯一键), 跑多遍不产生重复, 无需手动"跳过已存在的价格"
- 数据落到 vt_setting.json 指向的 PG 库 `dbbardata` 表

### 查看数据库里的数据

```
.venv/bin/python scripts/show_data.py --symbol 00700.SEHK --days 20        # 打印最近K线
.venv/bin/python scripts/show_data.py --symbol AAPL.NASDAQ --csv aapl.csv  # 导出 CSV

# 或直接用 psql 查后台 (PGPASSWORD 见 vt_setting.json)
# 专用库: quant (vt_setting.json 的 database.database)
# 表名: quant_data(K线数据) / quant_data_sync(同步状态摘要) —— 已重命名, 驱动已同步改好
# 注意: 若重装/升级 vnpy_postgresql, 需重打补丁(见下)
export PGPASSWORD=1121hotsren
/opt/homebrew/opt/libpq/bin/psql -h v.xucongyong.com -U postgres -d quant \
  -c "SELECT symbol,exchange,count(*),min(datetime)::date,max(datetime)::date FROM quant_data.quant_data WHERE symbol='00700' GROUP BY 1,2"
```

> 2026-08-27: 数据已从 `postgres` 库整体迁移到专用库 `quant`(697万行+2872行同步表), `vt_setting.json` 已指向 `quant`。

数据库标的编码: `000001.SZSE` / `00700.SEHK` / `AAPL.NASDAQ`。同步用 AkShare, 数据存远程 PG。

## BTC / AI 策略 (vnpy.alpha)

```
.venv/bin/python run_btc_ai.py   # 下载 6 年 BTC 日线(yfinance) + Alpha158 因子 + LightGBM 训练 + 智能回测
```

产物在 `lab/btc_ai/`。BTC 不经过 CTA 回测引擎。

## 代码约定

- 策略: 继承 `CtaTemplate`, 类属性声明 `parameters`(可调参数)/`variables`(状态变量), 交易逻辑在 `on_bar`(日线直接交易, 分钟线用 `BarGenerator` 聚合)
- 下单: 只用 `self.buy/sell/short/cover`
- 策略自动发现: `strategies/registry.py` 扫描 `strategies/*.py` + 根目录 `x_*.py`, 无需手动注册
- 新策略文件命名: `strategies/daily_YYYYMMDD_<name>.py`

## 重要提示

- 数据最近同步到 2026-06-11, 更新请跑 daily_sync
- 远程 PG 分块查询很慢, 回测 CLI 已改用一次性全量加载 (`fast_load_data`)
- `x_rl_portfolio_strategy.py` 缺少 `vnpy_portfoliostrategy` 依赖, 会被注册表自动跳过(正常)
- **vnpy_postgresql 驱动已补丁**: 表名改为 `quant_data`/`quant_data_sync`(原 dbbardata/dbbaroverview), 且不再自动建 tick 空表。
  若重装/升级该包, 需在 `.venv/lib/python3.12/site-packages/vnpy_postgresql/postgresql_database.py` 重新应用:
  1. `DbBarData.Meta` / `DbBarOverview.Meta` 加 `table_name = "quant_data"` / `"quant_data_sync"`
  2. `__init__` 的 `create_tables` 只留 `[DbBarData, DbBarOverview]`
