import numpy as np
from typing import Dict, List
from vnpy.trader.object import TickData, BarData, OrderData, TradeData
from vnpy_portfoliostrategy import StrategyTemplate, StrategyEngine
from vnpy_portfoliostrategy.utility import PortfolioBarGenerator

class XRlPortfolioStrategy(StrategyTemplate):
    """
    基于强化学习(SAC)的多品种投资组合管理策略 (Demo)
    
    参考论文：Soft Actor-Critic (SAC) + CNN-MHA
    动作维度：12个资产的权重区间 [-1, 1] + 1个借贷比例
    """

    author = "QuantML-Sisyphus"

    # 策略参数
    lookback_window = 48  # 历史回顾窗口（论文中为48小时）
    rebalance_interval = 4  # 调仓周期（论文中为每4小时调仓一次）

    # 策略变量
    current_step = 0

    parameters = ["lookback_window", "rebalance_interval"]
    variables = ["current_step"]

    def __init__(
        self,
        strategy_engine: StrategyEngine,
        strategy_name: str,
        vt_symbols: List[str],
        setting: dict
    ):
        """"""
        super().__init__(strategy_engine, strategy_name, vt_symbols, setting)

        # 针对每个品种的K线生成器与历史数据管理器
        self.bgs: Dict[str, PortfolioBarGenerator] = {}
        self.kline_buffers: Dict[str, list] = {symbol: [] for symbol in self.vt_symbols}

        for vt_symbol in self.vt_symbols:
            # 同样生成多品种对齐的K线
            self.bgs[vt_symbol] = PortfolioBarGenerator(self.on_bars)
            
        # TODO: 在此处加载预训练好的强化学习模型 (如PyTorch/ONNX版SAC Actor网络)
        # self.rl_model = load_pretrained_sac_model("sac_cnn_mha_v1.pth")
        self.write_log("预定义强化学习投资组合策略已初始化。")

    def on_init(self):
        """
        策略初始化回调
        """
        self.write_log("策略初始化")
        # 加载历史数据供缓冲区预热
        self.load_bars(self.lookback_window)

    def on_start(self):
        """
        策略启动回调
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        策略停止回调
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        行情TICK推送回调
        """
        pass

    def on_bars(self, bars: Dict[str, BarData]):
        """
        多品种K线截面数据推送（通常是一小时K线或分钟线这里合成）
        """
        # 更新历史数据缓存
        for vt_symbol, bar in bars.items():
            buffer = self.kline_buffers[vt_symbol]
            buffer.append(bar)
            if len(buffer) > self.lookback_window:
                buffer.pop(0)

        # 检查所有品种数据是否足够
        for symbol, buffer in self.kline_buffers.items():
            if len(buffer) < self.lookback_window:
                return

        # 时间计数器（每4小时调仓一次）
        self.current_step += 1
        if self.current_step % self.rebalance_interval != 0:
            return
            
        self.write_log("到达调仓时刻，开始构建状态矩阵并请求RL网络推理...")

        # 1. 构建状态张量 State Tensor [M(资产) x 4(OHLC) x N(回顾周期)]
        state_tensor = self.build_state_tensor()
        
        # 2. 将 State 传入 RL Agent，获取动作 Action (高斯分布的均值)
        # 按照论文，输出为 12个币的权重 (范围[-1,1]表示多空) + 1个借贷比例权重
        # target_weights = self.rl_model.predict(state_tensor) 
        
        # 这里为了演示，我们随机生成 -1 到 1 的伪预言
        target_weights = {symbol: np.random.uniform(-1, 1) for symbol in self.vt_symbols}
        lending_weight = np.random.uniform(-1, 1)  # w_{m+1} > 0 表示放贷，< 0 表示借款加杠杆
        
        self.write_log(f"当前放贷/借款资金比例权重指令: {lending_weight:.2f}")

        # 3. 计算当前账户净值与可用资金
        total_capital = 1_000_000  

        # 4. 根据目标权重执行调仓（包括做多做空及借贷管理）
        self.rebalance_portfolio(target_weights, total_capital, bars)
        
        self.put_event()

    def build_state_tensor(self) -> np.ndarray:
        """
        将 kline_buffers 中的数据转换为神经网络需要的状态 Tensor。
        论文中是 M×4×N，M=12（资产数），4=OHLC特征，N=48（历史长度）。
        返回: shape 为 (12, 4, 48) 的 np.ndarray
        """
        # 伪代码：
        # tensor = np.zeros((len(self.vt_symbols), 4, self.lookback_window))
        # ... 填充数据及归一化 ...
        # return tensor
        pass

    def rebalance_portfolio(self, target_weights: Dict[str, float], total_capital: float, bars: Dict[str, BarData]):
        """
        将各品种现有仓位调整至目标权重区间
        """
        for vt_symbol, target_w in target_weights.items():
            if vt_symbol not in bars:
                continue
                
            bar = bars[vt_symbol]
            target_value = total_capital * target_w
            target_volume = int(target_value / bar.close_price)  # 换算成目标股/币数
            
            # 获取当前持仓 (由于StrategyTemplate包含对持仓的管理，可直接获取)
            current_volume = self.get_pos(vt_symbol)
            
            # 计算差异并下单
            diff = target_volume - current_volume
            
            if diff > 0:
                self.buy(vt_symbol, bar.close_price * 1.01, diff)
            elif diff < 0:
                self.short(vt_symbol, bar.close_price * 0.99, abs(diff))
    
    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        pass
