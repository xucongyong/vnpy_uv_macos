import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CryptoPortfolioEnv(gym.Env):
    """
    符合论文《基于强化学习的投资组合管理模型》的强化学习交易环境
    """
    
    def __init__(self, df_data, window_size=48, num_assets=12):
        super(CryptoPortfolioEnv, self).__init__()
        
        self.df_data = df_data          # 全部的历史行情数据
        self.window_size = window_size  # 回溯的历史K线数量 (论文里是48小时)
        self.num_assets = num_assets    # 交易的资产数量 (论文里是12个加密货币)
        self.current_step = self.window_size
        
        # ==========================================
        # 1. 动作 (Action)
        # 论文里说：12个加密货币的调仓权重 + 1个借贷权重 = 13维
        # wt ∈ [−1, 1] 负数代表做空/借钱，正数代表做多/放贷
        # ==========================================
        self.action_space = spaces.Box(
            low=-1.0, 
            high=1.0, 
            shape=(self.num_assets + 1,), 
            dtype=np.float32
        )
        
        # ==========================================
        # 2. 状态 (State)
        # 论文里说：M个资产 * 4个特征(开、高、低、收) * N(48小时)
        # 这是一个 3D 的状态矩阵 (Tensor)
        # ==========================================
        self.observation_space = spaces.Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(self.num_assets, 4, self.window_size), 
            dtype=np.float32
        )
        
        # 初始资金池
        self.initial_balance = 1_000_000
        self.balance = self.initial_balance
        self.net_worth = self.initial_balance
        self.peak_net_worth = self.initial_balance

    def reset(self, seed=None, options=None):
        """游戏重新开始"""
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.net_worth = self.initial_balance
        self.peak_net_worth = self.initial_balance
        self.current_step = self.window_size
        
        return self._get_state(), {}

    def _get_state(self):
        """
        获取当前时刻的状态 (48小时的OHLC历史记录)
        """
        # 假装从数据中抽取过去48小时的行情矩阵
        # 返回形状为 (12, 4, 48)
        state = np.random.randn(self.num_assets, 4, self.window_size).astype(np.float32)
        return state

    def step(self, action):
        """
        ==========================================
        3. 环境计算 (Environment 交互核心)
        代理(Agent)给出动作后，环境进行结算，产生新状态和奖励
        ==========================================
        """
        # 取出 12 个币的买卖指令 和 1个放贷借钱指令
        crypto_weights = action[:self.num_assets]
        lending_weight = action[self.num_assets]
        
        # 模拟模拟计算：扣除手续费、加上放贷利息、结算资产涨跌
        transaction_fee_rate = 0.0005 # 手续费 δ
        lending_rate = 0.0001         # 借贷利息 ζ
        
        # 假装经过了真实的结算逻辑，算出了本期盈亏(PnL)
        # 这里用一个随机数假装
        PnL = np.random.normal(0, 1000)
        self.net_worth += PnL
        
        # 更新最高净值，监控最大回撤
        self.peak_net_worth = max(self.peak_net_worth, self.net_worth)
        drawdown = 1 - (self.net_worth / self.peak_net_worth)

        # ==========================================
        # 4. 奖励函数 (Reward Function)
        # 就像老师打分，这里参考论文通过惩罚回撤来提高 Sortino / Calmar 比例
        # ==========================================
        reward = PnL  # 赚了多少钱就给多少分
        
        # 如果回撤超过了 5%，开始狠狠地扣它的分！惩罚！
        if drawdown > 0.05:
            penalty = (drawdown - 0.05) * 100000 
            reward -= penalty
            
        # 进入下一个4小时
        self.current_step += 4
        
        # 判断是不是破产了或者到了年底 (游戏结束条件)
        terminated = False
        if self.net_worth < self.initial_balance * 0.5:
            # 亏了一半直接挂掉
            terminated = True
        
        # 如果把所有数据都跑完了也是结束
        truncated = False
        if self.current_step > 10000:
            truncated = True
        
        # 获取下一个状态
        next_state = self._get_state()
        
        # 返回：下一个状态, 你的得分, 游戏有没有胜利/失败停机, 是否到时间, 其他信息
        return next_state, reward, terminated, truncated, {"net_worth": self.net_worth}


if __name__ == "__main__":
    # ==========================================
    # 5. 代理 (Agent) - SAC算法的调用
    # 这里用主流深度学习库 stable-baselines3 
    # ==========================================
    try:
        from stable_baselines3 import SAC
        from stable_baselines3.common.env_checker import check_env
        print("💡 检查到你安装了强化学习库，开始演示。")
        
        # 1. 实例化我们的真实交易环境
        env = CryptoPortfolioEnv(df_data=None)
        check_env(env)  # 测试环境是否写对
        
        # 2. 实例化最强代理心脏：SAC 神经网络
        print("🧠 小管家 SAC 行动者-评价者大脑 正在诞生...")
        model = SAC("MlpPolicy", env, verbose=1)
        
        # 3. 让小管家开始练习几万次，自己去撞墙、试错、学习赚钱 
        print("🏃‍♂️ 小管家进入精神时光屋，开始 10000 次模拟交易训练...")
        model.learn(total_timesteps=10000)
        
        # 4. 考试通过！把它脑子里的记忆存到硬盘上
        print("💾 训练完成，正在把大脑导出成智力卡(ZIP文件)...")
        model.save("sac_crypto_agent")
        
        print("✅ 成功！把 sac_crypto_agent.zip 塞进 vn.py ，它就能开始自动操盘了！")
    
    except ImportError:
        print("⚠️ 没找到 'stable-baselines3'。你可以用 pip install stable-baselines3 来安装AI的核心大脑。")
