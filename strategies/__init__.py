"""strategies 包: 所有自定义 CTA 策略放在这里。

统一约定(加入新策略必须遵守):
1. 继承 vnpy_ctastrategy.CtaTemplate
2. 类属性声明 parameters / variables
3. 交易逻辑写在 on_bar(日线直接交易); 若做分钟级, 用 BarGenerator 聚合
4. 下单只用 self.buy / self.sell / self.short / self.cover

每日新策略用脚手架生成:
    .venv/bin/python scripts/new_strategy.py --name <名> --kind <ma|boll|rsi|momentum|template>
生成文件命名: daily_YYYYMMDD_<name>.py (registry.py 自动发现, 无需注册)

按名字回测:
    .venv/bin/python run_backtest.py --strategy <别名> --symbol 00700.SEHK
"""
